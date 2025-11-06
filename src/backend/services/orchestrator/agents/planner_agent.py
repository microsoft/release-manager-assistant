# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pydantic import BaseModel

from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIResponsesClient

from common.telemetry.app_logger import AppLogger
from common.telemetry.app_tracer_provider import AppTracerProvider
from common.agent_factory.agent_base import AgentBase
from common.contracts.configuration.agent_config import AzureOpenAIResponsesAgentConfig

class PlannerAgentResponse(BaseModel):
    plan_id: str
    agents: list[str]
    justification: str

class PlannerAgent(AgentBase):
    """
    The Planner Agent interface helps generate orchestration plans for the Release Manager.
    """
    def __init__(self, logger: AppLogger, tracer_provider: AppTracerProvider):
        """Initialize the Planner Agent instance."""
        super().__init__(logger, tracer_provider)


    async def create_agent(
        self,
        client: AzureOpenAIResponsesClient,
        configuration: AzureOpenAIResponsesAgentConfig
    ) -> ChatAgent:
        """
        Create the actual Planner agent in AI Foundry.

        Args:
            client: The Azure Responses client for creating agents
            configuration: Agent configuration containing Azure Responses agent settings

        Returns:
            The created AI Foundry agent

        Raises:
            ValueError: If Azure AI agent configuration is missing
        """
        if not configuration:
            self._logger.error("Azure Responses configuration is missing.")
            raise ValueError("Azure Responses configuration is required for PlannerAgent.")

        self._logger.info(f"Creating planner agent: {configuration.agent_name}")

        try:
            agent = client.create_agent(
                name=configuration.agent_name,
                instructions=configuration.instructions,
            )

            self._logger.info(f"Successfully created planner agent: {configuration.agent_name}")
            return agent
        except Exception as e:
            self._logger.error(f"Failed to create planner agent: {e}")
            raise