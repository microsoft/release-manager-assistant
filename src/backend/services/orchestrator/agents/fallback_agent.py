# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from agent_framework import ChatAgent
from agent_framework_azure_ai import AzureAIAgentClient

from common.telemetry.app_logger import AppLogger
from common.agent_factory.agent_base import AgentBase
from common.contracts.configuration.agent_config import AzureAIAgentConfig


class FallbackAgent(AgentBase):
    """
    FallbackAgent provides fallback option when planner fails to generate a plan.
    This agent is designed to be instantiated per session rather than shared.
    """

    def __init__(self, logger: AppLogger):
        """Initialize the FallbackAgent instance."""
        super().__init__(logger)

    async def create_agent(
        self,
        client: AzureAIAgentClient,
        configuration: AzureAIAgentConfig,
        **kwargs,
    ) -> ChatAgent:
        """
        Create the Fallback Agent.

        Args:
            configuration: Agent configuration
            **kwargs: Additional arguments for agent creation

        Returns:
            ChatAgent: The initialized Fallback agent
        """
        if not configuration:
            self._logger.error("Azure Responses configuration is missing.")
            raise ValueError("Azure Responses configuration is required for FallbackAgent.")

        self._logger.info(f"Creating fallback agent: {configuration.agent_name}")

        try:
            agent = client.create_agent(
                name=configuration.agent_name,
                instructions=configuration.instructions,
            )

            self._logger.info(f"Successfully created fallback agent: {configuration.agent_name}")
            return agent
        except Exception as e:
            self._logger.error(f"Failed to create fallback agent: {e}")
            raise