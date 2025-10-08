# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
import aiohttp
from typing import Any

from jira import JIRA as JiraClient
from models.jira_settings import JiraSettings

from common.telemetry.app_logger import AppLogger


class JiraPlugin:
    """
    A plugin for interacting with Jira using the JIRA Python library.
    """
    def __init__(
        self,
        logger: AppLogger,
        settings: JiraSettings,
        customfield_description_str: str,
        jql_instructions: str,
    ):
        self.logger = logger

        self.settings = settings
        self.jira_client = JiraClient(
            server=settings.server_url,
            basic_auth=(settings.username, settings.password)
        )

        self.jql_instructions = jql_instructions
        self.custom_field_description_json = json.loads(customfield_description_str)
        self.jira_field_map = []

    async def __fetch_jira_schema(self):
        self.logger.info(f"Fetching Jira fields from server {self.settings.server_url}")

        try:
            # Jira Client SDK does not support fetching fields directly.
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.settings.server_url}/rest/api/2/field",
                    auth=aiohttp.BasicAuth(self.settings.username, self.settings.password)
                ) as response:
                    response.raise_for_status()
                    fields = await response.json()

            # Only target fields that are in custom_field_description_json
            custom_field_names = {item.get("name") for item in self.custom_field_description_json}
            for field in fields:
                name = field.get("name")
                if name not in custom_field_names:
                    continue

                id = field.get("id")
                type = field.get("schema", {}).get("type", "unknown")
                name = field.get("name")
                custom = field.get("custom", False)
                description = next((item.get("description", "") for item in self.custom_field_description_json if item.get("name") == name), "")

                self.jira_field_map.append({
                    "id": id,
                    "name": name,
                    "type": type,
                    "custom": custom,
                    "description": description
                })

            self.logger.info(f"Successfully fetched {len(self.jira_field_map)} Jira fields.")
        except aiohttp.ClientError as e:
            self.logger.error(f"Failed to fetch Jira fields: {e}")

    async def initialize(self):
        """
        Initialize the Jira plugin with schema information.
        """
        self.logger.info("Initializing Jira plugin..")
        await self.__fetch_jira_schema()
        self.logger.info("Jira plugin initialized successfully.")

    async def get_jira_field_info(self) -> str:
        """
        Get a summary of Jira fields including their names, IDs, types, and descriptions.

        Returns:
        str: A formatted string containing the field information.
        """
        if not self.jira_field_map:
            return "No Jira fields available."

        formatted_fields = []
        for field in self.jira_field_map:
            field_info = f"Field: {field['name']}\n"
            field_info += f"  ID: {field['id']}\n"
            field_info += f"  Type: {field['type']}\n"
            field_info += f"  Custom: {field['custom']}\n"

            if field['description']:
                field_info += f"  Description: {field['description']}\n"

            formatted_fields.append(field_info)

        return "\n".join(formatted_fields)

    async def get_jira_jql_instructions(self) -> str:
        """
        Get JQL instructions for querying Jira issues.

        Returns:
        str: A formatted string containing the JQL instructions.
        """
        return self.jql_instructions

    def create_issue(self, project_key: str, summary: str, description: str, issuetype: str) -> str:
        """
        Create a new issue in Jira.

        Args:
        project_key (str): The key of the project to create the issue in.
        summary (str): The summary of the issue.
        description (str): The description of the issue.
        issuetype (str): The type of the issue (e.g., 'Task', 'Bug', 'Story').

        Returns:
        str: The key of the newly created issue.
        """
        issue_dict = {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issuetype},
        }
        new_issue = self.jira_client.create_issue(fields=issue_dict)

        self.logger.info(f"Issue created: {new_issue.key}")
        return new_issue.key

    def search_issues(self, jql_query: str) -> Any:
        """
        Search for issues in Jira using a JQL query.

        Args:
        jql_query (str): The JQL query to search for issues.

        Returns:
        list: A list of issue keys that match the JQL query.
        """
        self.logger.info(f"Searching for issues with JQL: {jql_query}")
        issues = self.jira_client.search_issues(jql_query)

        formatted_issues = []
        for issue in issues:
            issue_data = {
                "key": issue.key,
                "fields": {
                    field["name"]: issue.raw["fields"].get(field["id"])
                    for field in self.jira_field_map
                    if issue.raw["fields"].get(field["id"]) is not None
                },
            }
            formatted_issues.append(issue_data)

        self.logger.info(f"Found {len(formatted_issues)} issues")
        return formatted_issues

    def update_issue(self, issue_key: str, field: str, value):
        """
        Update an existing issue in Jira.

        Args:
        issue_key (str): The key of the issue to update.
        field (str): The field to update.
        value: The new value for the field.

        Returns:
        str: The key of the updated issue.
        """
        issue = self.jira_client.issue(issue_key)
        issue.update(fields={field: value})

        self.logger.info(f"Issue updated: {issue.key} - {field}: {value}")
        return issue.key