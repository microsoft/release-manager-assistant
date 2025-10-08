# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar, Dict, Optional, Type, TypeVar, Union

from agent_framework import AgentRunResponse, AgentThread, ChatAgent, ChatMessage
from agent_framework.azure import AzureAIAgentClient, AzureOpenAIResponsesClient

from common.contracts.configuration.agent_config import (
    AzureOpenAIResponsesAgentConfig,
    AzureAIAgentConfig
)
from common.telemetry.app_logger import AppLogger
from pydantic import BaseModel

T = TypeVar("T", bound="AgentBase")


class AgentBase(ABC):
    """Base class for all agents with built-in singleton pattern support."""

    _instances: ClassVar[Dict[Type[T], T]] = {}
    _locks: ClassVar[Dict[Type[T], asyncio.Lock]] = {}

    def __init__(self, logger: AppLogger):
        self._logger = logger

        self._agent: ChatAgent = None
        self._config: Optional[Any] = None
        self._initialized: bool = False

    @classmethod
    def _is_singleton(cls) -> bool:
        return False

    @classmethod
    async def get_instance(cls: Type[T], logger: AppLogger) -> T:
        if not cls._is_singleton():
            return cls(logger)

        if cls not in cls._instances:
            if cls not in cls._locks:
                cls._locks[cls] = asyncio.Lock()

            async with cls._locks[cls]:
                if cls not in cls._instances:
                    cls._instances[cls] = cls(logger)

        return cls._instances[cls]

    async def initialize(
        self,
        client: Union[AzureOpenAIResponsesClient, AzureAIAgentClient],
        configuration: Union[AzureOpenAIResponsesAgentConfig, AzureAIAgentConfig],
        **kwargs,
    ) -> None:
        """
        Initialize the agent with the provided configuration and optional kernel.

        Args:
            configuration: The configuration for the agent. Can be either AzureOpenAIResponsesAgentConfig or AzureAIAgentConfig.
            client: The client for provisioning Azure AI Foundry agents. REQUIRED for AzureOpenAIResponsesAgentConfig and AzureAIAgentConfig.
            **kwargs: Additional arguments for agent creation.
        """
        if not self._is_singleton():
            self._initialized = False

        if self._is_singleton() and self._initialized and self._agent:
            return self._agent

        if type(self) not in self._locks:
            self._locks[type(self)] = asyncio.Lock()

        async with self._locks[type(self)]:
            if self._is_singleton() and self._initialized and self._agent:
                return self._agent

            self._config = configuration

            if not (isinstance(configuration, AzureOpenAIResponsesAgentConfig) or isinstance(configuration, AzureAIAgentConfig)):
                raise ValueError("Unsupported agent configuration type.")
            elif isinstance(configuration, AzureOpenAIResponsesAgentConfig) and not isinstance(client, AzureOpenAIResponsesClient):
                raise ValueError("AzureOpenAIResponsesClient is required for AzureOpenAIResponsesAgentConfig.")
            elif isinstance(configuration, AzureAIAgentConfig) and not isinstance(client, AzureAIAgentClient):
                raise ValueError("AzureAIAgentClient is required for AzureAIAgentConfig.")

            self._agent = await self.create_agent(client=client, configuration=configuration, **kwargs)
            self._initialized = True

    @abstractmethod
    async def create_agent(
        self,
        client: Union[AzureOpenAIResponsesClient, AzureAIAgentClient],
        configuration: Union[AzureAIAgentConfig, AzureOpenAIResponsesAgentConfig],
        tools: Callable[..., Any] | list[Callable[..., Any]] | None = None,
        **kwargs,
    ) -> ChatAgent:
        """
        Creates an agent.

        Args:
            configuration: The configuration for the agent.
            client: The client to be used by the agent.
            tools: Optional tools to be used by the agent.
            **kwargs: Additional arguments for agent creation.

        Returns:
            The created ChatAgent.
        """
        pass

    def get_agent(self) -> Optional[Any]:
        return self._agent

    def new_agent_thread(self) -> Optional[AgentThread]:
        if self._agent:
            return self._agent.get_new_thread()

        return None

    async def run(
        self,
        messages: str | ChatMessage | list[str | ChatMessage],
        thread: AgentThread,
        runtime_configuration: Union[AzureOpenAIResponsesAgentConfig, AzureAIAgentConfig],
        tools: Callable[..., Any] | list[Callable[..., Any]] | None = None,
        response_format: type[BaseModel] | None = None,
        **kwargs,
    ) -> AgentRunResponse:
        """
        Runs the agent with the provided messages and thread.

        Args:
            messages: The input messages for the agent.
            thread: The agent thread to maintain context.
            tools: Optional tools to be used by the agent.
            response_format: Optional Pydantic model to enforce response structure.
            max_tokens: Optional maximum number of tokens for the response.
            model: Optional model to be used for the response.
            temperature: Optional temperature for the response.
            top_p: Optional top_p for the response.
            **kwargs: Additional arguments for agent run.

        Returns:
            The response from the agent.
        """
        response = await self._agent.run(
            messages=messages,
            thread=thread,
            tools=tools,
            response_format=response_format,
            max_tokens=runtime_configuration.max_completion_tokens,
            model=runtime_configuration.model,
            temperature=runtime_configuration.temperature,
            top_p=runtime_configuration.top_p,
            **kwargs
        )

        # Log agent response with structured format
        # Check if usage details are available
        if response.usage_details:
            usage_info = (
            f"  Usage Details:\n"
            f"    Input Tokens:  {response.usage_details.input_token_count}\n"
            f"    Output Tokens: {response.usage_details.output_token_count}\n"
            f"    Total Tokens:  {response.usage_details.total_token_count}"
            )
        else:
            usage_info = "  Usage Details: Not available"

        self._logger.info(
            f"Agent response received:\n"
            f"  Created At: {response.created_at}\n"
            f"  Response ID: {response.response_id}\n"
            f"  Response: {response}\n"
            f"{usage_info}"
        )

        return response
