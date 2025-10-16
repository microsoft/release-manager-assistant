# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
import csv
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
from core.factory import MCPToolBase, Domain


class AzureDevopsService(MCPToolBase):
    def __init__(self):
        super().__init__(Domain.AZURE_DEVOPS)
        self.logger = logging.getLogger("azure_devops_service")
        self.data_file = Path(__file__).parent.parent / "static" / "devops.csv"

        # Define mappings between CSV column headers and internal field names
        self.field_mappings = {
            # CSV column headers exactly as they appear in the CSV file
            "ISSUE_ID": "issue_id",
            "STREAM_NAME": "stream_name", 
            "RELEASE": "release",
            "WORK_ITEM_ID": "work_item_id",
            "WORK_ITEM_STATUS": "work_item_status",
            "COMMIT_ID": "commit_id",
            "CHECK_IN_DATE": "check_in_date",
            # Map standard Azure DevOps field names
            "id": "work_item_id",
            "status": "work_item_status",
            "project": "stream_name"
        }

    def register_tools(self, mcp):
        @mcp.tool(
            name="list_projects",
            description="""
            Retrieve a list of projects in your Azure DevOps organization.
            Returns unique projects (stream names) available in the system.
            """,
            tags=[self.domain.value]
        )
        def azure_devops_list_projects() -> List[Dict[str, Any]]:
            """
            Retrieve a list of projects in your Azure DevOps organization.
            
            Returns:
                A list of project dictionaries with project information.
            """
            self.logger.info("Azure DevOps MCP Server: Received list_projects request.")

            try:
                rows, _ = self._load_work_items()
                
                # Get unique stream names (projects)
                projects = {}
                for row in rows:
                    stream_name = row.get("STREAM_NAME", "")
                    if stream_name and stream_name not in projects:
                        projects[stream_name] = {
                            "id": stream_name.lower().replace("-", "_"),
                            "name": stream_name,
                            "description": f"Project for {stream_name} stream"
                        }

                project_list = list(projects.values())
                self.logger.info(f"Found {len(project_list)} projects")
                return project_list
                
            except Exception as e:
                self.logger.error(f"Error listing projects: {str(e)}")
                return []

        @mcp.tool(
            name="list_releases",
            description="""
            Retrieves a list of all releases from the work items.
            Returns unique release versions available in the system.
            """,
            tags=[self.domain.value]
        )
        def azure_devops_list_releases() -> List[Dict[str, Any]]:
            """
            Retrieves a list of all releases from the work items.
            
            Returns:
                A list of release dictionaries with release information.
            """
            self.logger.info("Azure DevOps MCP Server: Received list_releases request.")

            try:
                rows, _ = self._load_work_items()
                
                # Get unique releases
                releases = {}
                for row in rows:
                    release = row.get("RELEASE", "")
                    if release and release not in releases:
                        releases[release] = {
                            "id": release,
                            "name": release,
                            "version": release
                        }

                release_list = list(releases.values())
                self.logger.info(f"Found {len(release_list)} releases")
                return release_list
                
            except Exception as e:
                self.logger.error(f"Error listing releases: {str(e)}")
                return []

        @mcp.tool(
            name="get_work_item",
            description="""
            Get a single work item by ID.
            Retrieves detailed information about a specific work item.
            """,
            tags=[self.domain.value]
        )
        def azure_devops_get_work_item(work_item_id: str) -> Dict[str, Any]:
            """
            Get a single work item by ID.
            
            Args:
                work_item_id: The ID of the work item to retrieve
                
            Returns:
                A dictionary containing the work item details, or error if not found.
            """
            self.logger.info(f"Azure DevOps MCP Server: Received get_work_item request for ID: {work_item_id}")

            try:
                rows, _ = self._load_work_items()
                
                # Find the work item by ID - check both WORK_ITEM_ID and ISSUE_ID
                for row in rows:
                    work_item_id_str = str(row.get("WORK_ITEM_ID", ""))
                    issue_id_str = str(row.get("ISSUE_ID", ""))
                    
                    if work_item_id_str == str(work_item_id) or issue_id_str == str(work_item_id):
                        self.logger.info(f"Found work item {work_item_id} (WORK_ITEM_ID: {work_item_id_str}, ISSUE_ID: {issue_id_str})")
                        return row  # Return the row data directly like Jira service
                
                # Work item not found
                self.logger.warning(f"Work item {work_item_id} not found")
                return {
                    "error": f"Work item {work_item_id} not found",
                    "id": work_item_id
                }
                
            except Exception as e:
                self.logger.error(f"Error getting work item: {str(e)}")
                return {"error": str(e), "id": work_item_id}

        @mcp.tool(
            name="get_work_items",
            description="""
            Retrieve a list of work items by IDs in batch.
            Allows retrieving multiple work items efficiently in a single request.
            """,
            tags=[self.domain.value]
        )
        def azure_devops_get_work_items(work_item_ids: List[str]) -> List[Dict[str, Any]]:
            """
            Retrieve a list of work items by IDs in batch.
            
            Args:
                work_item_ids: List of work item IDs to retrieve
                
            Returns:
                A list of work item dictionaries.
            """
            self.logger.info(f"Azure DevOps MCP Server: Received get_work_items request for IDs: {work_item_ids}")

            try:
                rows, _ = self._load_work_items()
                work_items = []
                
                # Convert work_item_ids to strings for comparison
                target_ids = [str(wid) for wid in work_item_ids]
                
                # Find matching work items - check both WORK_ITEM_ID and ISSUE_ID
                for row in rows:
                    work_item_id_str = str(row.get("WORK_ITEM_ID", ""))
                    issue_id_str = str(row.get("ISSUE_ID", ""))
                    
                    if work_item_id_str in target_ids or issue_id_str in target_ids:
                        work_items.append(row)  # Return the row data directly like Jira service
                
                self.logger.info(f"Found {len(work_items)} work items out of {len(work_item_ids)} requested")
                return work_items
                
            except Exception as e:
                self.logger.error(f"Error getting work items: {str(e)}")
                return []

        @mcp.tool(
            name="update_work_item",
            description="""
            Update a work item by ID with specified fields.
            Allows modifying field values of an existing work item.
            """,
            tags=[self.domain.value]
        )
        def azure_devops_update_work_item(work_item_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
            """
            Update a work item by ID with specified fields.
            
            Args:
                work_item_id: The ID of the work item to update
                fields: Dictionary of field names and values to update
                
            Returns:
                Status of the update operation.
            """
            self.logger.info(f"Azure DevOps MCP Server: Received update_work_item request for ID: {work_item_id} with fields: {fields}")

            try:
                rows, fieldnames = self._load_work_items()
                updated = False
                
                # Find and update the work item
                for row in rows:
                    if str(row.get("WORK_ITEM_ID", "")) == str(work_item_id):
                        # Update the fields
                        for field_name, field_value in fields.items():
                            # Map field names if needed
                            actual_field = field_name
                            for csv_field, internal_field in self.field_mappings.items():
                                if internal_field == field_name.lower():
                                    actual_field = csv_field
                                    break
                            
                            # Add new field to fieldnames if needed
                            if actual_field not in fieldnames:
                                fieldnames = list(fieldnames) + [actual_field]
                            
                            # Update the field value
                            row[actual_field] = str(field_value) if field_value is not None else ""
                        
                        updated = True
                        break
                
                if updated:
                    # Save the updated data
                    self._save_work_items(rows, fieldnames)
                    self.logger.info(f"Successfully updated work item {work_item_id}")
                    return {
                        "success": True,
                        "id": work_item_id,
                        "message": f"Work item {work_item_id} updated successfully"
                    }
                else:
                    self.logger.warning(f"Work item {work_item_id} not found for update")
                    return {
                        "success": False,
                        "id": work_item_id,
                        "error": f"Work item {work_item_id} not found"
                    }
                
            except Exception as e:
                self.logger.error(f"Error updating work item: {str(e)}")
                return {
                    "success": False,
                    "id": work_item_id,
                    "error": str(e)
                }

        @mcp.tool(
            name="create_work_item",
            description="""
            Create a new work item in a specified project and work item type.
            Creates a new work item with the specified field values.
            """,
            tags=[self.domain.value]
        )
        def azure_devops_create_work_item(project: str, work_item_type: str = "Task", fields: Dict[str, Any] = None) -> Dict[str, Any]:
            """
            Create a new work item in a specified project and work item type.
            
            Args:
                project: The project (stream name) where the work item will be created
                work_item_type: Type of work item (defaults to "Task")
                fields: Additional field values for the work item
                
            Returns:
                The created work item data.
            """
            self.logger.info(f"Azure DevOps MCP Server: Received create_work_item request for project: {project}")

            try:
                rows, fieldnames = self._load_work_items()
                fields = fields or {}
                
                # Generate new work item ID
                max_work_item_id = 0
                max_issue_id = 0
                
                for row in rows:
                    try:
                        work_item_id = int(row.get("WORK_ITEM_ID", 0))
                        issue_id = int(row.get("ISSUE_ID", 0))
                        max_work_item_id = max(max_work_item_id, work_item_id)
                        max_issue_id = max(max_issue_id, issue_id)
                    except (ValueError, TypeError):
                        continue
                
                new_work_item_id = str(max_work_item_id + 1)
                new_issue_id = str(max_issue_id + 1)
                
                # Create new work item
                new_work_item = {
                    "ISSUE_ID": new_issue_id,
                    "STREAM_NAME": project,
                    "RELEASE": fields.get("release", ""),
                    "WORK_ITEM_ID": new_work_item_id,
                    "WORK_ITEM_STATUS": fields.get("status", "New"),
                    "COMMIT_ID": "",
                    "CHECK_IN_DATE": ""
                }
                
                # Add any additional fields
                for field_name, field_value in fields.items():
                    if field_name not in ["release", "status"]:
                        # Map field names if needed
                        actual_field = field_name.upper()
                        if actual_field not in fieldnames:
                            fieldnames = list(fieldnames) + [actual_field]
                        new_work_item[actual_field] = str(field_value) if field_value is not None else ""
                
                # Add to rows and save
                rows.append(new_work_item)
                self._save_work_items(rows, fieldnames)
                
                self.logger.info(f"Created work item {new_work_item_id} in project {project}")
                return {
                    "id": new_work_item_id,
                    "fields": new_work_item,
                    "success": True
                }
                
            except Exception as e:
                self.logger.error(f"Error creating work item: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }

        @mcp.tool(
            name="get_work_items_for_release",
            description="""
            Retrieve a list of work items for a specified release.
            Filters work items by release version.
            """,
            tags=[self.domain.value]
        )
        def azure_devops_get_work_items_for_release(release: str) -> List[Dict[str, Any]]:
            """
            Retrieve a list of work items for a specified release.
            
            Args:
                release: The release version to filter by
                
            Returns:
                A list of work items for the specified release.
            """
            self.logger.info(f"Azure DevOps MCP Server: Received get_work_items_for_release request for release: {release}")

            try:
                rows, _ = self._load_work_items()
                work_items = []
                
                # Filter by release
                for row in rows:
                    if row.get("RELEASE", "") == release:
                        work_items.append(row)  # Return the row data directly like Jira service
                
                self.logger.info(f"Found {len(work_items)} work items for release {release}")
                return work_items
                
            except Exception as e:
                self.logger.error(f"Error getting work items for release: {str(e)}")
                return []

        @mcp.tool(
            name="get_work_items_by_date",
            description="""
            Retrieve a list of work items for a specified date (on and after).
            Filters work items by check-in date, returning items checked in on or after the specified date.
            """,
            tags=[self.domain.value]
        )
        def azure_devops_get_work_items_by_date(date: str) -> List[Dict[str, Any]]:
            """
            Retrieve a list of work items for a specified date (on and after).
            
            Args:
                date: The date in format MM/DD/YY or YYYY-MM-DD to filter by (items on and after this date)
                
            Returns:
                A list of work items checked in on or after the specified date.
            """
            self.logger.info(f"Azure DevOps MCP Server: Received get_work_items_by_date request for date: {date}")

            try:
                rows, _ = self._load_work_items()
                work_items = []
                
                # Parse the input date
                try:
                    if "/" in date:
                        # Handle MM/DD/YY format
                        target_date = datetime.strptime(date, "%m/%d/%y")
                    else:
                        # Handle YYYY-MM-DD format
                        target_date = datetime.strptime(date, "%Y-%m-%d")
                except ValueError:
                    self.logger.error(f"Invalid date format: {date}")
                    return []
                
                # Filter by check-in date
                for row in rows:
                    check_in_date_str = row.get("CHECK_IN_DATE", "")
                    if not check_in_date_str:
                        continue
                    
                    try:
                        # Parse the check-in date (format: M/D/YY H:MM or variations)
                        # Remove time part if present
                        date_part = check_in_date_str.split(" ")[0]
                        check_in_date = datetime.strptime(date_part, "%m/%d/%y")
                        
                        # Include if check-in date is on or after target date
                        if check_in_date >= target_date:
                            work_items.append(row)  # Return the row data directly like Jira service
                    except (ValueError, IndexError):
                        # Skip invalid date formats
                        continue
                
                self.logger.info(f"Found {len(work_items)} work items for date >= {date}")
                return work_items
                
            except Exception as e:
                self.logger.error(f"Error getting work items by date: {str(e)}")
                return []

        @mcp.tool(
            name="health",
            description="Check the health status of the Azure DevOps service.",
            tags=[self.domain.value]
        )
        def azure_devops_health() -> Dict[str, str]:
            """
            Check the health status of the Azure DevOps service.

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
        return 10

    def _load_work_items(self) -> tuple:
        """
        Load work items from the CSV file with comprehensive error handling and data cleaning.

        Returns:
            Tuple containing (rows, fieldnames)
        """
        rows = []
        fieldnames = []

        try:
            # Check if file exists first
            if not self.data_file.exists():
                self.logger.info(f"Creating new work items dataset at {self.data_file}")
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
            self.logger.error(f"Error loading work items: {str(e)}")
            import traceback
            traceback.print_exc()
            # Return empty dataset in case of error
            return [], []

        return rows, fieldnames

    def _save_work_items(self, rows, fieldnames):
        """
        Save work items to the CSV file.

        Args:
            rows: List of dictionaries representing work items
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
            self.logger.error(f"Error saving work items to CSV: {str(e)}")
            raise

    def _infer_type(self, value):
        """Simple type inference for field values"""
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
        # Check if it looks like a date
        if "/" in str(value) and any(char.isdigit() for char in str(value)):
            return "datetime"
        return "string"

    def _get_display_name(self, field_name):
        """
        Convert technical field names to user-friendly display names.

        Args:
            field_name: The technical field name

        Returns:
            A user-friendly display name
        """
        display_names = {
            "ISSUE_ID": "Issue ID",
            "STREAM_NAME": "Project/Stream Name",
            "RELEASE": "Release Version",
            "WORK_ITEM_ID": "Work Item ID",
            "WORK_ITEM_STATUS": "Work Item Status", 
            "COMMIT_ID": "Commit ID",
            "CHECK_IN_DATE": "Check-in Date"
        }
        
        return display_names.get(field_name, field_name.replace("_", " ").title())

    def _get_field_description(self, field_name):
        """
        Get detailed description for Azure DevOps work item fields.

        Args:
            field_name: The field name

        Returns:
            A detailed description of the field
        """
        descriptions = {
            "ISSUE_ID": "Unique identifier for the issue record in the tracking system",
            "STREAM_NAME": "Name of the project or development stream (e.g., APP-Analytics, Platform-ServiceFramework)",
            "RELEASE": "Version number of the release (e.g., 4.0.0.4000, 1.0.0.1000)",
            "WORK_ITEM_ID": "Unique identifier for the work item in Azure DevOps",
            "WORK_ITEM_STATUS": "Current status of the work item (New, Active, In Review, Completed, Checked in)",
            "COMMIT_ID": "Git commit identifier associated with the work item (if checked in)",
            "CHECK_IN_DATE": "Date and time when the work item was checked in or completed"
        }
        
        return descriptions.get(field_name, f"Field for {field_name.lower().replace('_', ' ')}")
