# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
import csv
import json
import re
from typing import List, Dict, Any
from pathlib import Path
from core.factory import MCPToolBase, Domain


class JiraService(MCPToolBase):
    def __init__(self):
        super().__init__(Domain.JIRA)
        self.logger = logging.getLogger("jira_service")
        self.data_file = Path(__file__).parent.parent / "static" / "issues.csv"
        self.description_file = Path(__file__).parent.parent / "static" / "jira_customfield_description.json"
        self.jql_instruction_file = Path(__file__).parent.parent / "static" / "jql_cheatsheet.md"

        # Define mappings between CSV column headers and description.json field names
        self.field_mappings = {
            # CSV column headers exactly as they appear in the CSV file
            "Creator ID": "creator_id",
            "Created At": "created_at",
            "Issue ID": "issue_id",
            "Issue Type": "issue_type",
            "Issue Description": "issue_description",
            "Issue Status": "issue_status",
            "Severity": "severity",
            "Discussion": "discussion",
            "Resolution": "resolution",
            "Linked Issues": "linked_issues",
            "Owning Team": "owning_team",
            "Affected Version": "affected_version",
            "Affected Service": "affected_service",
            "Escalation Manager": "escalation_manager",
            # Map standard Jira field names to description.json fields
            "id": "issue_id",
            "key": "issue_id",
            "summary": "issue_description",
            "description": "issue_description",
            "status": "issue_status",
            "creator": "creator_id",
            "release": "release"
        }

    def register_tools(self, mcp):
        @mcp.tool(
            name="get_fields",
            description="Get all available fields for Jira issues.",
            tags=[self.domain.value]
        )
        def jira_get_fields() -> List[Dict[str, Any]]:
            """
            Get information about all available Jira fields.
            Returns a list of field definitions including ID, name, and schema information.
            """
            try:
                rows, fieldnames = self._load_issues()
                descriptions = self._load_field_descriptions()

                # Build payload similar to JIRA: a list of field objects
                payload = []
                # Infer types from first non-empty values in column
                for fld in fieldnames:
                    # Try to get a sample value from rows
                    sample = None
                    for r in rows:
                        if r.get(fld):
                            sample = r.get(fld)
                            break

                    # Special handling for Discussion field which may contain JSON string
                    if fld.lower() == "discussion" and sample:
                        try:
                            # Try to parse as JSON if it's a JSON string
                            parsed = json.loads(sample)
                            if isinstance(parsed, list):
                                schema = {"type": "array"}
                            elif isinstance(parsed, dict):
                                schema = {"type": "object"}
                            else:
                                schema = {"type": "string"}
                        except (json.JSONDecodeError, TypeError):
                            schema = {"type": "string"}
                    else:
                        schema = {"type": self._infer_type(sample)}

                    # Check if this is a custom field
                    is_custom = fld.lower().startswith("custom") or fld.lower().startswith("cf_") or fld.lower().startswith("customfield")

                    # Get description from the JSON file if available
                    description = descriptions.get(fld) or descriptions.get(fld.lower(), f"Auto-generated field for column '{fld}'")

                    # Determine a more user-friendly display name - preserve original case from CSV
                    display_name = self._get_display_name(fld)

                    # Look up the field ID from field_mappings
                    field_id = None
                    for csv_field, desc_field in self.field_mappings.items():
                        if csv_field.lower() == fld.lower():
                            field_id = desc_field
                            break

                    # If no mapping found, use the original field name as ID
                    field_id = field_id or fld

                    fobj = {
                        "id": field_id,
                        "name": display_name,
                        "custom": is_custom,
                        "description": description,
                        "schema": schema
                    }
                    payload.append(fobj)
                return payload
            except Exception as e:
                self.logger.error(f"Error retrieving field information: {str(e)}")
                return []

        @mcp.tool(
            name="search_issues",
            description="Search for Jira issues using JQL (Jira Query Language).",
            tags=[self.domain.value]
        )
        def jira_search_issues(jql: str = "") -> Dict[str, Any]:
            """
            Search for Jira issues using JQL (Jira Query Language).

            Args:
                jql: Jira Query Language string to filter issues.
                     Examples: "status = Active", "Issue Type = Bug", etc.
                     If empty, returns all issues.

            Returns:
                A dictionary with total count and list of matching issues.
            """
            try:
                # Load issues data
                rows, _ = self._load_issues()

                # Match issues against JQL query
                matches = [r for r in rows if self._jql_match(r, jql)]

                # Format response in JIRA-like structure
                issues = []
                for r in matches:
                    # Create a copy of the row to avoid modifying the original
                    issue_fields = {}

                    # Process each field, converting JSON strings to objects where appropriate
                    for field_name, field_value in r.items():
                        if field_value is None:
                            issue_fields[field_name] = ""
                        elif field_name.lower() == "discussion" or field_name.lower() == "linked_issues":
                            # Try to parse JSON strings for known array/object fields
                            try:
                                if isinstance(field_value, str) and field_value.strip():
                                    if (field_value.startswith('[') and field_value.endswith(']')) or \
                                    (field_value.startswith('{') and field_value.endswith('}')):
                                        issue_fields[field_name] = json.loads(field_value)
                                    else:
                                        issue_fields[field_name] = field_value
                                else:
                                    issue_fields[field_name] = field_value
                            except json.JSONDecodeError:
                                # Keep as string if JSON parsing fails
                                issue_fields[field_name] = field_value
                        else:
                            issue_fields[field_name] = field_value

                    # Create the issue object with id, key and fields
                    issue = {
                        "id": r.get("id"),
                        "key": r.get("key") or f"ISSUE-{r.get('id')}",
                        "fields": issue_fields
                    }

                    issues.append(issue)

                return {"total": len(issues), "issues": issues}
            except Exception as e:
                self.logger.error(f"Error in search_issues: {str(e)}")
                return {"error": str(e), "total": 0, "issues": []}

        @mcp.tool(
            name="create_issue",
            description="Create a new Jira issue.",
            tags=[self.domain.value]
        )
        def jira_create_issue(fields: Dict[str, Any]) -> Dict[str, Any]:
            """
            Create a new Jira issue with the specified fields.

            Args:
                fields: A dictionary of field values to set on the new issue.
                        Must include required fields like Issue Type and Issue Description.

            Returns:
                The created issue data.
            """
            try:
                rows, fieldnames = self._load_issues()

                # Prepare new issue dict using existing fieldnames
                new = {k: "" for k in fieldnames}

                for k, v in fields.items():
                    # Handle special field formatting for certain fields
                    if k.lower() in ["discussion"] and isinstance(v, list):
                        # Convert array to JSON string for Discussion field
                        new[k] = json.dumps(v)
                    elif v is None:
                        # Handle None values
                        new[k] = ""
                    else:
                        # Convert to string, but preserve the value
                        new[k] = str(v)

                    # Add field to fieldnames if it's new
                    if k not in fieldnames:
                        fieldnames = list(fieldnames) + [k]

                # Set current date/time if Created At is empty
                if ('Created At' in fieldnames and not new.get('Created At')):
                    from datetime import datetime
                    new['Created At'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Assign id
                max_id = 0
                for r in rows:
                    try:
                        iid = int(r.get("id") or 0)
                    except:
                        iid = 0
                    if iid > max_id:
                        max_id = iid

                new_id = str(max_id + 1)
                new['id'] = new_id

                # Set the issue key
                if 'key' in new and (not new.get('key')):
                    new['key'] = f"ISSUE-{new_id}"
                if 'key' not in new:
                    new['key'] = f"ISSUE-{new_id}"

                # If Issue ID is a field, set it to match the id
                if 'Issue ID' in fieldnames:
                    new['Issue ID'] = new_id

                # Add the new row to the dataset
                rows.append(new)

                # Ensure fieldnames include any new keys
                all_fieldnames = list(dict.fromkeys(list(fieldnames)))

                # Save the updated dataset
                self._save_issues(rows, all_fieldnames)

                return {"id": new_id, "key": new.get("key"), "fields": new}

            except Exception as e:
                self.logger.error(f"Error creating issue: {str(e)}")
                return {"error": str(e)}

        @mcp.tool(
            name="update_issue",
            description="Update an existing Jira issue with new field values.",
            tags=[self.domain.value])
        def jira_update_issue(issue_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
            """
            Update an existing Jira issue with new field values.

            Args:
                issue_id: The ID of the issue to update
                fields: A dictionary of field values to update

            Returns:
                Status of the update operation
            """
            try:
                rows, fieldnames = self._load_issues()

                # Construct a JQL query for the issue ID
                jql = f"id = {issue_id}"
                updated = []

                for r in rows:
                    if self._jql_match(r, jql):
                        # Apply updates with proper type handling
                        for k, v in fields.items():
                            # Add new field to fieldnames if needed
                            if k not in fieldnames:
                                fieldnames = list(fieldnames) + [k]

                            # Handle special field formatting
                            if v is None:
                                r[k] = ""
                            elif isinstance(v, (list, dict)):
                                # Convert complex types to JSON string
                                r[k] = json.dumps(v)
                            else:
                                # Convert to string
                                r[k] = str(v)

                        updated.append(r.get("id"))

                # Only save if changes were made
                if updated:
                    # Ensure unique fieldnames
                    all_fieldnames = list(dict.fromkeys(fieldnames))
                    self._save_issues(rows, all_fieldnames)

                return {
                    "success": len(updated) > 0,
                    "updated_count": len(updated),
                    "updated_ids": updated
                }

            except Exception as e:
                self.logger.error(f"Error updating issue: {str(e)}")
                return {"error": str(e), "success": False}

        @mcp.tool(
            name="get_jql_instructions",
            description="Get Jira Query Language (JQL) instructions and examples.",
            tags=[self.domain.value]
        )
        def jira_get_jql_instructions() -> Dict[str, str]:
            """
            Get Jira Query Language (JQL) instructions and examples.

            Returns:
                A dictionary containing JQL instructions and examples.
            """
            try:
                if self.jql_instruction_file.exists():
                    jql_content = self.jql_instruction_file.read_text(encoding='utf-8')
                    return {
                        "status": "success",
                        "instructions": jql_content
                    }
                else:
                    self.logger.warning(f"JQL cheatsheet file not found at {self.jql_instruction_file}")
                    return {
                        "status": "error",
                        "error": "JQL cheatsheet file not found",
                        "instructions": "JQL instructions file is not available."
                    }
            except Exception as e:
                self.logger.error(f"Error reading JQL instructions: {str(e)}")
                return {
                    "status": "error",
                    "error": str(e),
                    "instructions": "Failed to load JQL instructions."
                }

        @mcp.tool(
            name="health",
            description="Check the health status of the Jira service.",
            tags=[self.domain.value]
        )
        def jira_health() -> Dict[str, str]:
            """
            Check the health status of the Jira service.

            Returns:
                A dictionary with health status information.
            """
            return {
                "status": "ok",
                "file": str(self.data_file),
            }

    @property
    def tool_count(self) -> int:
        """Return the number of tools provided by this service."""
        return 6

    def _load_issues(self) -> tuple:
        """
        Load issues from the CSV file with comprehensive error handling and data cleaning.

        Returns:
            Tuple containing (rows, fieldnames)
        """
        rows = []
        fieldnames = []

        try:
            # Check if file exists first
            if not self.data_file.exists():
                self.logger.info(f"Creating new issues dataset at {self.data_file}")
                # Ensure the directory exists
                self.data_file.parent.mkdir(parents=True, exist_ok=True)
                # Return empty dataset if file doesn't exist
                return [], []

            # Try reading with different encodings
            encodings = ['utf-8-sig', 'utf-8', 'latin-1']
            content = None

            for encoding in encodings:
                try:
                    with open(self.data_file, mode='r', newline='', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            # If we couldn't read the file with any encoding
            if content is None:
                self.logger.error("Failed to read the CSV file with any encoding")
                return [], []

            # Check if content is empty
            if not content.strip():
                self.logger.warning("CSV file is empty")
                return [], []

            # Process CSV content in memory using DictReader
            reader = csv.DictReader(content.splitlines())

            # Clean up field names - remove BOM characters if present
            clean_fieldnames = []
            if reader.fieldnames:
                for field in reader.fieldnames:
                    # Handle None field case to prevent AttributeError
                    if field is None:
                        continue
                    # Remove BOM character if present
                    if field.startswith('\ufeff'):
                        clean_fieldnames.append(field.replace('\ufeff', ''))
                    else:
                        clean_fieldnames.append(field)
            else:
                # If no fieldnames are found, return empty dataset
                self.logger.error("No field names found in CSV header")
                return [], []

            # Create rows with cleaned field names
            rows = []
            for row_dict in reader:
                clean_row = {}
                for k, v in row_dict.items():
                    # Handle None key case to prevent AttributeError
                    if k is None:
                        # Skip None keys
                        continue
                    clean_key = k.replace('\ufeff', '') if k.startswith('\ufeff') else k

                    # Process value - handle special cases
                    clean_value = v if v is not None else ""

                    clean_row[clean_key] = clean_value
                rows.append(clean_row)

            fieldnames = clean_fieldnames

        except Exception as e:
            self.logger.error(f"Error loading issues: {str(e)}")
            import traceback
            traceback.print_exc()
            # Return empty dataset in case of error
            return [], []

        # Ensure each has an 'id' field: if CSV doesn't contain 'id' create one
        for i, row in enumerate(rows):
            if 'id' not in row or row.get('id','')=='':
                row['id'] = str(i+1)

            # Ensure key field exists
            if 'key' not in row or row.get('key','')=='':
                row['key'] = f"ISSUE-{row['id']}"

        return rows, fieldnames

    def _save_issues(self, rows, fieldnames):
        """
        Save issues to the CSV file.

        Args:
            rows: List of dictionaries representing issues
            fieldnames: List of field names to include in the CSV
        """
        try:
            # Create a string buffer to write CSV data
            import io
            from csv import writer, QUOTE_ALL

            # Create a string buffer to write CSV data
            output_buffer = io.StringIO()
            csv_writer = writer(output_buffer, quoting=QUOTE_ALL)

            # Write header
            csv_writer.writerow(fieldnames)

            # Write rows with proper escaping
            for r in rows:
                # Prepare row data with proper string handling
                row_data = []
                for field in fieldnames:
                    # Get the value or empty string, convert to string
                    value = r.get(field)
                    if value is None:
                        row_data.append('')
                    else:
                        row_data.append(str(value))

                # Write the row with proper escaping
                csv_writer.writerow(row_data)

            # Get the complete CSV content
            csv_content = output_buffer.getvalue()

            # Write all at once to minimize file operations
            with open(self.data_file, mode='w', newline='', encoding='utf-8') as f:
                f.write(csv_content)

        except Exception as e:
            self.logger.error(f"Error saving issues to CSV: {str(e)}")
            raise

    def _infer_type(self, value):
        """Simple type inference for field values"""
        # Simple inference
        if value is None or value == '':
            return "string"
        try:
            int(value)
            return "number"
        except:
            pass
        try:
            float(value)
            return "number"
        except:
            pass
        # Dates not inferred reliably
        return "string"

    def _jql_match(self, item, jql):
        """
        Match an item against a JQL query.

        Args:
            item: Dictionary representing a Jira issue
            jql: JQL query string

        Returns:
            Boolean indicating if the item matches the query
        """
        # Very small JQL parser: supports clauses like field = "value" or field = value, and AND, OR, ~ (contains)
        # Remove outer whitespace
        if not jql or jql.strip() == "" or jql.strip() == "ALL":
            return True

        expr = jql.strip()
        # Split by OR first
        or_parts = [p.strip() for p in re.split(r'\bOR\b', expr, flags=re.IGNORECASE)]
        for part in or_parts:
            and_parts = [p.strip() for p in re.split(r'\bAND\b', part, flags=re.IGNORECASE)]
            all_and = True
            for clause in and_parts:
                m = re.match(r'(?P<field>[\w\s\.\-]+)\s*(?P<op>=|~)\s*(?P<quote>["\']?)(?P<val>.*?)(?P=quote)\s*$', clause)
                if not m:
                    # Unsupported clause -> conservative False
                    all_and = False
                    break
                field_name = m.group('field').strip()
                op = m.group('op')
                val = m.group('val').strip()

                # Try both exact and case-insensitive field name match
                # First, try direct access with the field name
                item_val = item.get(field_name)

                # If not found, try case-insensitive match with various field name formats
                if item_val is None:
                    # Try common Jira field mappings
                    if field_name.lower() == 'status':
                        item_val = item.get('Issue Status') or item.get('issue_status')
                    elif field_name.lower() == 'description':
                        item_val = item.get('Issue Description') or item.get('issue_description')
                    elif field_name.lower() == 'id':
                        item_val = item.get('Issue ID') or item.get('issue_id')
                    elif field_name.lower() == 'type':
                        item_val = item.get('Issue Type') or item.get('issue_type')
                    # Try case-insensitive field match as a last resort
                    else:
                        for k in item.keys():
                            if k.lower() == field_name.lower():
                                item_val = item.get(k)
                                break

                # Convert to string and strip
                item_val = str(item_val or "").strip()

                if op == '=':
                    if item_val != val:
                        all_and = False
                        break
                elif op == '~':
                    if val.lower() not in item_val.lower():
                        all_and = False
                        break
            if all_and:
                return True
        return False

    def _load_field_descriptions(self):
        """
        Load field descriptions from the JSON file.

        Returns:
            Dictionary mapping field names to their descriptions
        """
        descriptions = {}

        if self.description_file.exists():
            try:
                with open(self.description_file, 'r', encoding='utf-8') as f:
                    field_descriptions = json.load(f)

                    # Create a dictionary with all field descriptions
                    name_to_desc = {}
                    for field in field_descriptions:
                        name_to_desc[field.get('id', '').lower()] = field.get('description', '')

                    # Fill descriptions dictionary using field mappings
                    for csv_field, desc_field in self.field_mappings.items():
                        # Use original CSV field name for the key to ensure exact match
                        if desc_field.lower() in name_to_desc:
                            descriptions[csv_field] = name_to_desc[desc_field.lower()]
                            # Also add lowercase version for case-insensitive lookup
                            descriptions[csv_field.lower()] = name_to_desc[desc_field.lower()]

            except Exception as e:
                self.logger.error(f"Error reading field descriptions: {e}")

        return descriptions

    def _get_display_name(self, field_name):
        """
        Convert technical field names to display names.

        Args:
            field_name: The technical field name

        Returns:
            A user-friendly display name
        """
        # If the field already has a nice name like "Issue ID", keep it
        if " " in field_name:  # Field already has spaces, likely already formatted nicely
            return field_name

        # Convert technical names to display names
        field_name_lower = field_name.lower()
        if field_name_lower in ["issue_id", "id"]:
            return "Issue ID"
        elif field_name_lower in ["creator_id", "creator"]:
            return "Creator"
        elif field_name_lower in ["created_at", "createdat"]:
            return "Created Date"
        elif field_name_lower in ["issue_type", "issuetype"]:
            return "Issue Type"
        elif field_name_lower in ["issue_description", "summary", "description"]:
            return "Description"
        elif field_name_lower in ["issue_status", "status"]:
            return "Status"
        elif field_name_lower == "severity":
            return "Severity"
        elif field_name_lower == "discussion":
            return "Discussion"
        elif field_name_lower == "resolution":
            return "Resolution"
        elif field_name_lower == "linked_issues":
            return "Linked Issues"
        elif field_name_lower == "owning_team":
            return "Owning Team"
        elif field_name_lower == "affected_version":
            return "Affected Version"
        elif field_name_lower == "affected_service":
            return "Affected Service"
        elif field_name_lower == "escalation_manager":
            return "Escalation Manager"
        elif field_name_lower == "key":
            return "Issue Key"
        else:
            # For other fields, convert snake_case to Title Case
            return ' '.join(word.capitalize() for word in field_name.split('_'))
