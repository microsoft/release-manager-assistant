# JQL (Jira Query Language) Guide for AI Agents

## Basic Query Pattern
```
FIELD OPERATOR VALUE
```

Examples:
- `status = "Open"`
- `priority = "High"`
- `assignee = "john.doe@example.com"`

## Combining Queries
Use `AND`, `OR`, and parentheses `()` to combine conditions:
- `status = "Open" AND priority = "High"`
- `(status = "Open" OR status = "In Progress") AND assignee = "john.doe"`

## Essential Operators

### Exact Match
- `=` equals: `status = "Open"`
- `!=` not equals: `status != "Closed"`

### Text Search
- `~` contains: `summary ~ "bug"`
- `!~` does not contain: `summary !~ "test"`

### Lists
- `IN` matches any: `status IN ("Open", "In Progress")`
- `NOT IN` excludes: `priority NOT IN ("Low", "Lowest")`

### Comparison (for dates/numbers)
- `>` greater than: `created > "2024-01-01"`
- `<` less than: `updated < "2024-12-31"`

## Common Fields and Values

### Standard Fields
- `status`: "Open", "In Progress", "Done", "Closed", "Resolved"
- `priority`: "Highest", "High", "Medium", "Low", "Lowest"
- `assignee`: email addresses or usernames
- `creator`: email addresses or usernames
- `summary`: issue title/description
- `project`: project key or name
- `created`: date field
- `updated`: date field

### Issue Types
- `issuetype`: "Bug", "Story", "Task", "Epic", "Subtask"

## Custom Fields - IMPORTANT for AI Agents

**⚠️ Critical Rule: When using custom fields, you MUST use the exact field name from the schema, not standard Jira field names.**

### How to Handle Custom Fields

1. **Always check the schema first** using the `jira_get_fields` tool
2. **Use the exact field name** as it appears in the schema
3. **Custom fields override standard field names** in this system

### Example Schema vs Query Usage

If the schema shows these custom fields:
```json
{
  "id": "creator_id",
  "name": "Creator ID",
  "description": "Person who created the issue"
}
```

**✅ CORRECT - Use schema field name:**
```jql
"Creator ID" = "john.doe@example.com"
```

**❌ WRONG - Don't use standard Jira field:**
```jql
creator = "john.doe@example.com"  # This won't work with custom fields
```

### Common Custom Field Patterns

Based on the schema, you might see fields like:
- `"Creator ID"` instead of `creator`
- `"Issue Status"` instead of `status`
- `"Issue Type"` instead of `issuetype`
- `"Issue Description"` instead of `summary`
- `"Owning Team"` (custom field)
- `"Affected Service"` (custom field)
- `"Escalation Manager"` (custom field)

### Best Practice for AI Agents

1. **Always call `jira_get_fields` first** to get the current schema
2. **Map user requests to schema field names** before building queries
3. **Use quoted field names** for custom fields with spaces
4. **When in doubt, use the schema field name** rather than guessing

### Custom Field Query Examples
```jql
# Using custom field names from schema
"Issue Status" = "Open"
"Creator ID" = "jane.smith@company.com"
"Owning Team" = "Backend Services"
"Affected Service" ~ "API"

# Complex query with custom fields
"Issue Status" IN ("Open", "In Progress") AND "Owning Team" = "Platform Team"
```

## Practical Query Examples

### Find Open Issues
```
status = "Open"
```

### Find High Priority Bugs
```
issuetype = "Bug" AND priority = "High"
```

### Find My Assigned Issues
```
assignee = "your.email@company.com"
```

### Find Recent Issues
```
created >= "-7d"
```

### Find Issues by Text Content
```
summary ~ "login" OR description ~ "login"
```

### Complex Query Example
```
project = "MYPROJ" AND status IN ("Open", "In Progress") AND priority IN ("High", "Highest") AND assignee != empty
```

## Date Shortcuts
- `-1d` = yesterday
- `-1w` = last week
- `-1M` = last month
- `startOfWeek()` = beginning of current week
- `endOfDay()` = end of today

## Tips for AI Agents

1. **Always quote string values**: Use `status = "Open"` not `status = Open`

2. **Use IN for multiple values**: `status IN ("Open", "Resolved")` instead of `status = "Open" OR status = "Resolved"`

3. **Common patterns**:
   - Find all open issues: `status = "Open"`
   - Find user's work: `assignee = "user@email.com"`
   - Find urgent items: `priority IN ("High", "Highest")`
   - Find recent activity: `updated >= "-1d"`

4. **When searching text**, use `~` operator: `summary ~ "keyword"`

5. **For empty fields**: Use `IS EMPTY` or `IS NOT EMPTY`

6. **Case sensitivity**: Field names are case-insensitive, values depend on your Jira setup

## Quick Reference Values

### Common Status Values
- "Open", "In Progress", "Done", "Closed", "Resolved", "To Do"
- "Reopened", "Under Review", "Approved", "Cancelled"

### Common Priority Values
- "Highest", "High", "Medium", "Low", "Lowest"

### Common Issue Types
- "Bug", "Story", "Task", "Epic", "Subtask"
- "Change", "Incident", "Service Request"

## Query Templates for Common Tasks

### Workflow Queries
```jql
# Find all open work
status IN ("Open", "To Do", "In Progress")

# Find completed work
status IN ("Done", "Closed", "Resolved")

# Find work needing attention
status = "Open" AND assignee IS NOT EMPTY
```

### Priority-Based Queries
```jql
# Critical issues
priority IN ("Highest", "High")

# All bugs with medium+ priority
issuetype = "Bug" AND priority IN ("High", "Medium", "Highest")
```

### Time-Based Queries
```jql
# Created in last 7 days
created >= "-7d"

# Updated recently
updated >= "-1d"

# Old unresolved issues
created <= "-30d" AND status != "Done"
```

### User Assignment Queries
```jql
# Unassigned work
assignee IS EMPTY

# My work
assignee = currentUser()

# Work created by me
reporter = currentUser()
```