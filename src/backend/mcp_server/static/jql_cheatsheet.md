# JQL (Jira Query Language) Guide for AI Agents

## Basic Query Pattern

```
FIELD OPERATOR VALUE
```

Examples:

- `"Issue Status" = "Open"`
- `"Priority Level" = "High"`
- `"Assignee ID" = "john.doe@example.com"`

## Combining Queries

Use `AND`, `OR`, and parentheses `()` to combine conditions:

- `"Issue Status" = "Open" AND "Priority Level" = "High"`
- `("Issue Status" = "Open" OR "Issue Status" = "In Progress") AND "Assignee ID" = "john.doe"`

## Essential Operators

### Exact Match

- `=` equals: `"Issue Status" = "Open"`
- `!=` not equals: `"Issue Status" != "Closed"`

### Text Search

- `~` contains: `"Issue Description" ~ "bug"`
- `!~` does not contain: `"Issue Description" !~ "test"`

### Lists

- `IN` matches any: `"Issue Status" IN ("Open", "In Progress")`
- `NOT IN` excludes: `"Priority Level" NOT IN ("Low", "Lowest")`

### Comparison (for dates/numbers)

- `>` greater than: `"Created Date" > "2024-01-01"`
- `<` less than: `"Updated Date" < "2024-12-31"`

### Issue Types

- `"Issue Type"`: "Bug", "Story"

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
Issue Status IN ("Open", "In Progress") AND "Owning Team" = "Platform Team"
```

## Practical Query Examples

### Find Open Issues

```jql
"Issue Status" = "Open"
```

### Find High Priority Bugs

```jql
"Issue Type" = "Bug" AND "Priority Level" = "High"
```

### Find My Assigned Issues

```jql
"Assignee ID" = "your.email@company.com"
```

### Find Recent Issues

```jql
"Created Date" >= "-7d"
```

### Find Issues by Text Content

```jql
"Issue Description" ~ "login" OR "Issue Details" ~ "login"
```

### Complex Query Example

```jql
"Project Key" = "MYPROJ" AND "Issue Status" IN ("Open", "In Progress") AND "Priority Level" IN ("High", "Highest") AND "Assignee ID" != empty
```

## Date Shortcuts

- `-1d` = yesterday
- `-1w` = last week
- `-1M` = last month
- `startOfWeek()` = beginning of current week
- `endOfDay()` = end of today

## Tips for AI Agents

1. **Always quote string values**: Use `"Issue Status" = "Open"` not `"Issue Status" = Open`

2. **Use IN for multiple values**: `"Issue Status" IN ("Open", "Resolved")` instead of `"Issue Status" = "Open" OR "Issue Status" = "Resolved"`

3. **Common patterns**:
   - Find all open issues: `"Issue Status" = "Open"`
   - Find user's work: `"Assignee ID" = "user@email.com"`
   - Find urgent items: `"Priority Level" IN ("High", "Highest")`
   - Find recent activity: `"Updated Date" >= "-1d"`

4. **When searching text**, use `~` operator: `"Issue Description" ~ "keyword"`

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
"Issue Status" IN ("Open", "To Do", "In Progress")

# Find completed work
"Issue Status" IN ("Done", "Closed", "Resolved")

# Find work needing attention
"Issue Status" = "Open" AND "Assignee ID" IS NOT EMPTY
```

### Priority-Based Queries

```jql
# Critical issues
"Priority Level" IN ("Highest", "High")

# All bugs with medium+ priority
"Issue Type" = "Bug" AND "Priority Level" IN ("High", "Medium", "Highest")
```

### Time-Based Queries

```jql
# Created in last 7 days
"Created Date" >= "-7d"

# Updated recently
"Updated Date" >= "-1d"

# Old unresolved issues
"Created Date" <= "-30d" AND "Issue Status" != "Done"
```

### User Assignment Queries

```jql
# Unassigned work
"Assignee ID" IS EMPTY

# My work
"Assignee ID" = currentUser()

# Work created by me
"Creator ID" = currentUser()
```
