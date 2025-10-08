# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from agent_framework import ChatAgent, HostedCodeInterpreterTool
from agent_framework_azure_ai import AzureAIAgentClient

from common.telemetry.app_logger import AppLogger
from common.agent_factory.agent_base import AgentBase
from common.contracts.configuration.agent_config import AzureAIAgentConfig


class VisualizationAgent(AgentBase):
    """
    The Visualization Agent interface that uses Code Interpreter tool to generate visualizations.
    """
    def __init__(self, logger: AppLogger):
        """Initialize the VisualizationAgent instance."""
        super().__init__(logger)


    async def create_agent(
        self,
        client: AzureAIAgentClient,
        configuration: AzureAIAgentConfig,
    ) -> ChatAgent:
        """
        Create the actual Visualization agent in AI Foundry.

        Args:
            logger: Application logger for logging errors and info
            configuration: Agent configuration containing Azure AI agent settings
            foundry_client: The Foundry client for creating agents

        Returns:
            The created AI Foundry agent

        Raises:
            ValueError: If Foundry agent configuration is missing
        """
        if not configuration:
            self._logger.error("Foundry agent configuration is missing.")
            raise ValueError("Foundry agent configuration is required for VisualizationAgent.")

        self._logger.info(f"Creating visualization agent: {configuration.agent_name}")

        try:
            agent = client.create_agent(
                name=configuration.agent_name,
                instructions=configuration.instructions,
                tools=[HostedCodeInterpreterTool()],
            )
            
            self._logger.info(f"Successfully created visualization agent: {configuration.agent_name}")
            return agent
        except Exception as e:
            self._logger.error(f"Failed to create visualization agent: {e}")
            raise
