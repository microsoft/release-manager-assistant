# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pathlib import Path

from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIResponsesClient

from models.jira_settings import JiraSettings
from plugins.jira_plugin import JiraPlugin

from common.telemetry.app_logger import AppLogger
from common.agent_factory.agent_base import AgentBase
from common.contracts.configuration.agent_config import AzureOpenAIResponsesAgentConfig


class JiraAgent(AgentBase):
    """
    JiraAgent provides integration with JIRA systems for the Release Manager.
    This agent is designed to be instantiated per session rather than shared.
    """
    def __init__(self, logger: AppLogger):
        """Initialize the JiraAgent instance."""
        super().__init__(logger)

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

            try:
                agent = client.create_agent(
                    name=configuration.agent_name,
                    instructions=configuration.instructions,
                    tools=[
                        JiraPlugin.create_issue, 
                        JiraPlugin.update_issue, 
                        JiraPlugin.search_issues,
                        JiraPlugin.get_jira_field_info,
                        JiraPlugin.get_jira_jql_instructions,
                    ],
                )

                self._logger.info(f"Successfully created visualization agent: {configuration.agent_name}")
                return agent
            except Exception as e:
                self._logger.error(f"Failed to create visualization agent: {e}")
                raise
        except Exception as ex:
            self._logger.error(f"Error creating Jira agent: {ex}")
            return None