# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIResponsesClient

from common.telemetry.app_logger import AppLogger
from common.agent_factory.agent_base import AgentBase
from common.contracts.configuration.agent_config import AzureOpenAIResponsesAgentConfig

from plugins.az_devops_plugin import AzDevOpsPluginFactory


class AzureDevOpsAgent(AgentBase):
    """
    AzureDevOpsAgent provides integration with Azure DevOps system for the Release Manager using MCP.
    This agent is designed to be instantiated per session rather than shared across instances.
    """
    def __init__(self, logger: AppLogger):
        """Initialize the AzureDevOpsAgent instance."""
        super().__init__(logger)


    async def create_agent(
        self,
        client: AzureOpenAIResponsesClient,
        configuration: AzureOpenAIResponsesAgentConfig,
        **kwargs
    ) -> ChatAgent:
        """
        Creates Azure DevOps Agent.

        Args:
            configuration: Agent configuration
            **kwargs: Additional arguments for agent creation

        Returns:
            ChatAgent: The initialized Azure DevOps agent
        """
        try:
            mcp_plugin_factory: AzDevOpsPluginFactory = kwargs.get('mcp_plugin_factory')

            # Use pre-initialized plugin factory if available, otherwise create new one
            if mcp_plugin_factory and not mcp_plugin_factory.is_initialized:
                self._logger.error("Provided MCP plugin factory is not initialized")

            self._logger.info("Using pre-initialized Azure DevOps MCP plugin")
            azure_devops_agent = client.create_agent(
                name=configuration.agent_name,
                instructions=configuration.instructions,
                tools=[mcp_plugin_factory.plugin],
            )

            self._logger.info(f"Successfully created Azure DevOps agent: {configuration.agent_name}")
            return azure_devops_agent
        except Exception as ex:
            self._logger.error(f"Error creating Azure DevOps agent: {ex}")
            return None
