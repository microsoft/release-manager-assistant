# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pathlib import Path
from typing import List, Any

from agent_framework import ChatAgent, MCPStreamableHTTPTool
from agent_framework.azure import AzureOpenAIResponsesClient

from models.jira_settings import JiraSettings
from plugins.jira_plugin import JiraPlugin

from common.telemetry.app_tracer_provider import AppTracerProvider
from common.telemetry.app_logger import AppLogger
from common.agent_factory.agent_base import AgentBase
from common.contracts.configuration.agent_config import AzureOpenAIResponsesAgentConfig


class JiraAgent(AgentBase):
    """
    JiraAgent provides integration with JIRA systems for the Release Manager.
    This agent is designed to be instantiated per session rather than shared.
    """
    def __init__(self, logger: AppLogger, tracer_provider: AppTracerProvider):
        """Initialize the JiraAgent instance."""
        super().__init__(logger, tracer_provider)

    async def create_agent(
        self,
        client: AzureOpenAIResponsesClient,
        configuration: AzureOpenAIResponsesAgentConfig,
        **kwargs
    ) -> ChatAgent:
        """
        Create a Semantic Kernel ChatCompletionAgent for JIRA integration.

        Args:
            configuration: Agent configuration
            jira_server_url: JIRA server URL
            jira_server_username: JIRA server username
            jira_server_password: JIRA server password
            **kwargs: Additional arguments for agent creation

        Returns:
            ChatCompletionAgent: The initialized JIRA agent
        """
        try:
            # Read JIRA instructions and field mapping from static files
            settings = JiraSettings(**kwargs)
            tools = await self._get_tools(settings)

            try:
                agent = client.create_agent(
                    name=configuration.agent_name,
                    instructions=configuration.instructions,
                    tools=tools,
                )

                self._logger.info(f"Successfully created visualization agent: {configuration.agent_name}")
                return agent
            except Exception as e:
                self._logger.error(f"Failed to create visualization agent: {e}")
                raise
        except Exception as ex:
            self._logger.error(f"Error creating Jira agent: {ex}")
            return None

    async def _get_tools(self, settings: JiraSettings) -> List[Any] | MCPStreamableHTTPTool:
        """
        Create MCP client tools for Jira integration.

        Args:
            settings: JiraSettings containing MCP server configuration

        Returns:
            List of MCP tools for the agent
        """
        # Determine which tools to use based on settings
        if settings.use_mcp_server:
            self._logger.info("Using MCP server for Jira integration")
            return MCPStreamableHTTPTool(
                name="jira-mcp-server",
                description="Jira MCP server to create, update and search Jira Issues.",
                url=settings.server_url
            )
        else:
            self._logger.info("Using traditional Jira plugin for integration")

            config_path = Path(settings.config_file_path)

            def _read_file(path: Path, default: str = "") -> str:
                try:
                    return path.read_text(encoding="utf-8")
                except FileNotFoundError:
                    self._logger.warning(f"File not found: {path}. Using default empty content.")
                    return default
                except Exception as err:
                    self._logger.error(f"Failed to read {path}: {err}")
                    return default

            jql_instructions = _read_file(config_path / "jql_cheatsheet.md")
            jira_customfield_description = _read_file(config_path / "jira_customfield_description.json")

            # Create Jira plugin
            jira_plugin = JiraPlugin(
                logger=self._logger,
                settings=settings,
                customfield_description_str=jira_customfield_description,
                jql_instructions=jql_instructions,
            )
            await jira_plugin.initialize()

            return [
                JiraPlugin.create_issue,
                JiraPlugin.update_issue,
                JiraPlugin.search_issues,
                JiraPlugin.get_jira_field_info,
                JiraPlugin.get_jira_jql_instructions,
            ]

