# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import asyncio
from dataclasses import dataclass
from typing import Union, Dict, Callable, Optional

from agent_framework.azure import AzureAIAgentClient, AzureOpenAIResponsesClient

from models.agents import Agent
from models.devops_settings import DevOpsSettings
from models.jira_settings import JiraSettings

from common.agent_factory.agent_base import AgentBase
from common.contracts.configuration.agent_config import (
    AzureOpenAIResponsesAgentConfig,
    AzureAIAgentConfig
)
from common.telemetry.app_tracer_provider import AppTracerProvider
from common.telemetry.app_logger import AppLogger

from .azure_devops_agent import AzureDevOpsAgent
from .fallback_agent import FallbackAgent
from .jira_agent import JiraAgent
from .planner_agent import PlannerAgent
from .final_answer_generator_agent import FinalAnswerGeneratorAgent


@dataclass
class AgentCreationContext:
    """Context object containing all necessary information for agent creation."""
    configuration: Union[AzureAIAgentConfig, AzureOpenAIResponsesAgentConfig]
    jira_settings: Optional[JiraSettings] = None
    devops_settings: Optional[DevOpsSettings] = None


class ReleaseManagerAgentFactory:
    """
    Factory class for managing agent creation and reuse in the Release Manager solution.
    Implements a singleton pattern and leverages the base singleton patterns in agent base classes.
    """

    _instance = None
    _lock = asyncio.Lock()

    def __init__(self):
        self._agent_creators: Dict[Agent, Callable] = {}
        self._initialized = False
        self._setup_agent_creators()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ReleaseManagerAgentFactory, cls).__new__(cls)
        return cls._instance

    def _setup_agent_creators(self):
        """Setup the agent creation registry mapping."""
        self._agent_creators = {
            Agent.FINAL_ANSWER_GENERATOR_AGENT: self._create_final_answer_generator_agent,
            Agent.PLANNER_AGENT: self._create_planner_agent,
            Agent.JIRA_AGENT: self._create_jira_agent,
            Agent.AZURE_DEVOPS_AGENT: self._create_azure_devops_agent,
            Agent.FALLBACK_AGENT: self._create_fallback_agent,
        }

    @classmethod
    async def get_instance(cls):
        """Get the singleton instance of ReleaseManagerAgentFactory."""
        if not cls._lock:
            cls._lock = asyncio.Lock()

        async with cls._lock:
            if cls._instance is None:
                cls._instance = ReleaseManagerAgentFactory()
        return cls._instance

    async def initialize(
        self,
        logger: AppLogger,
        tracer_provider: AppTracerProvider,
        foundry_client: Optional[AzureAIAgentClient] = None,
        azure_openai_responses_client: Optional[AzureOpenAIResponsesClient] = None
    ):
        """Initialize the factory with required dependencies."""
        async with self._lock:
            if self._initialized:
                return

            if not logger:
                raise ValueError("Logger is required for factory initialization")

            self.logger = logger
            self.tracer_provider = tracer_provider
            self.foundry_client = foundry_client
            self.azure_openai_responses_client = azure_openai_responses_client

            self._initialized = True
            self.logger.info("ReleaseManagerAgentFactory initialized")


    async def create_agent(
        self,
        agent_type: Agent,
        configuration: Union[AzureAIAgentConfig, AzureOpenAIResponsesAgentConfig],
        **kwargs
    ) -> AgentBase:
        """
        Generic method to create any type of agent using the registry pattern.

        Args:
            agent_type: The type of agent to create
            configuration: Agent configuration (Foundry or Azure Responses)
            **kwargs: Additional settings specific to the agent type
                - For JIRA: jira_settings (JiraSettings)
                - For AZURE_DEVOPS: mcp_plugin_factory (AzDevOpsPluginFactory)

        Returns:
            ChatAgent: The created agent instance

        Raises:
            ValueError: If agent_type is not supported or required kwargs are missing
            RuntimeError: If factory is not initialized or required clients are missing
        """
        if not self._initialized:
            raise RuntimeError("Factory not initialized. Call initialize() first.")

        if agent_type not in self._agent_creators:
            raise ValueError(f"Unsupported agent type: {agent_type}")

        context = AgentCreationContext(
            configuration=configuration,
            jira_settings=kwargs.get('jira_settings'),
            devops_settings=kwargs.get('devops_settings')
        )

        if context.configuration is AzureAIAgentConfig and not self.foundry_client:
            raise RuntimeError(f"Foundry client required for {agent_type.value} but not configured")

        if context.configuration is AzureOpenAIResponsesAgentConfig and not self.azure_openai_responses_client:
            raise RuntimeError(f"Azure OpenAI Responses client required for {agent_type.value} but not configured")

        try:
            agent_creator_func = self._agent_creators[agent_type]
            return await agent_creator_func(context)
        except Exception as e:
            self.logger.error(f"Failed to create {agent_type.value}: {str(e)}")
            raise

    async def _create_final_answer_generator_agent(self, context: AgentCreationContext) -> FinalAnswerGeneratorAgent:
        """Create the Final Answer Generator Agent (singleton)."""
        async with self._lock:
            final_answer_generator_agent = await FinalAnswerGeneratorAgent.get_instance(self.logger, self.tracer_provider)
            await final_answer_generator_agent.initialize(
                client=self.foundry_client,
                configuration=context.configuration
            )

        self.logger.info("Final Answer Generator Agent initialized or retrieved.")
        return final_answer_generator_agent

    async def _create_planner_agent(self, context: AgentCreationContext) -> PlannerAgent:
        """Create a new instance of PlannerAgent."""
        async with self._lock:
            planner_agent = await PlannerAgent.get_instance(self.logger, self.tracer_provider)
            await planner_agent.initialize(
                client=self.azure_openai_responses_client,
                configuration=context.configuration
            )

        self.logger.info("Planner Agent initialized or retrieved.")
        return planner_agent

    async def _create_jira_agent(self, context: AgentCreationContext) -> JiraAgent:
        """Create a new instance of JiraAgent."""
        if not context.jira_settings:
            raise ValueError("jira_settings is required for JIRA agent")

        async with self._lock:
            jira_agent = await JiraAgent.get_instance(self.logger, self.tracer_provider)
            await jira_agent.initialize(
                client=self.azure_openai_responses_client,
                configuration=context.configuration,
                server_url=context.jira_settings.server_url,
                username=context.jira_settings.username,
                password=context.jira_settings.password,
                config_file_path=context.jira_settings.config_file_path,
                use_mcp_server=context.jira_settings.use_mcp_server
            )

        self.logger.info("Created new JIRA agent instance")
        return jira_agent

    async def _create_azure_devops_agent(self, context: AgentCreationContext) -> AzureDevOpsAgent:
        """Create a new instance of AzureDevOpsAgent with MCP server integration."""
        if not context.devops_settings:
            raise ValueError("devops_settings is required for Azure DevOps agent")

        if not context.devops_settings.use_mcp_server and not context.devops_settings.mcp_plugin_factory:
            raise ValueError("Either use_mcp_server or mcp_plugin_factory must be set for Azure DevOps agent")

        try:
            async with self._lock:
                azure_devops_agent = await AzureDevOpsAgent.get_instance(self.logger, self.tracer_provider)
                await azure_devops_agent.initialize(
                    client=self.azure_openai_responses_client,
                    configuration=context.configuration,
                    use_mcp_server=context.devops_settings.use_mcp_server,
                    mcp_server_endpoint=context.devops_settings.mcp_server_endpoint,
                    mcp_plugin_factory=context.devops_settings.mcp_plugin_factory
                )

            self.logger.info("Created new Azure DevOps agent instance with MCP integration")
            return azure_devops_agent
        except ValueError as e:
            self.logger.error(f"Invalid configuration: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to create Azure DevOps agent: {e}")
            raise

    async def _create_fallback_agent(self, context: AgentCreationContext) -> FallbackAgent:
        """Create a new instance of FallbackAgent."""
        async with self._lock:
            fallback_agent = await FallbackAgent.get_instance(logger=self.logger, tracer_provider=self.tracer_provider)
            await fallback_agent.initialize(client=self.azure_openai_responses_client, configuration=context.configuration)

        self.logger.info("Created new Fallback agent instance")
        return fallback_agent