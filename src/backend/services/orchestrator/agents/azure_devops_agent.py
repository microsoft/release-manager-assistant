# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from agent_framework import ChatAgent, MCPStdioTool, MCPStreamableHTTPTool
from agent_framework.azure import AzureOpenAIResponsesClient

from common.telemetry.app_tracer_provider import AppTracerProvider
from common.telemetry.app_logger import AppLogger
from common.agent_factory.agent_base import AgentBase
from common.contracts.configuration.agent_config import AzureOpenAIResponsesAgentConfig

from models.devops_settings import DevOpsSettings


class AzureDevOpsAgent(AgentBase):
    """
    AzureDevOpsAgent provides integration with Azure DevOps system for the Release Manager using MCP.
    This agent is designed to be instantiated per session rather than shared across instances.
    """
    def __init__(self, logger: AppLogger, tracer_provider: AppTracerProvider):
        """Initialize the AzureDevOpsAgent instance."""
        super().__init__(logger, tracer_provider)


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
            settings = DevOpsSettings(**kwargs)
            tools = await self._get_tools(settings)

            azure_devops_agent = client.create_agent(
                name=configuration.agent_name,
                instructions=configuration.instructions,
                tools=[tools],
            )

            self._logger.info(f"Successfully created Azure DevOps agent: {configuration.agent_name}")
            return azure_devops_agent
        except Exception as ex:
            self._logger.error(f"Error creating Azure DevOps agent: {ex}")
            return None

    async def _get_tools(self, settings: DevOpsSettings) -> MCPStdioTool | MCPStreamableHTTPTool:
        """
        Create MCP client tools for Jira integration.

        Args:
            settings: JiraSettings containing MCP server configuration

        Returns:
            List of MCP tools for the agent
        """
        # Determine which tools to use based on settings
        if settings.use_mcp_server:
            self._logger.info("Using MCP server for Azure DevOps integration")
            return MCPStreamableHTTPTool(
                name="azure-devops-mcp-server",
                description="Azure DevOps MCP server to create, update and search Azure DevOps work items.",
                url=settings.mcp_server_endpoint,
            )
        else:
            if not settings.mcp_plugin_factory or not settings.mcp_plugin_factory.plugin:
                raise ValueError("MCP plugin factory must be provided when not using mock MCP server")

            self._logger.info("Using pre-initialized Azure DevOps MCP plugin")
            return settings.mcp_plugin_factory.plugin
