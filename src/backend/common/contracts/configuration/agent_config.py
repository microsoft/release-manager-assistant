# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

from common.contracts.configuration.config_base import ConfigBase
from common.contracts.configuration.config_type import ConfigType


class BaseAgentConfig(BaseModel):
    """
    AgentConfig is a configuration model for an AI Agent.

    Attributes: 
        agent_name (str): The name of the agent. MUST be set.
        instructions (str): Specific instructions or prompt for the agent. MUST be set.
        model (str): The name or identifier of the model to be used. MUST be set.
        content_type (Optional[Literal["application/json", "text/plain"]]):
            The content type for the agent's input/output. Defaults to "application/json".
        description (Optional[str]): A brief description of the agent. Defaults to None.
        temperature (Optional[float]): A value between 0.0 and 1.0 that controls the randomness of the agent's responses.
            Defaults to None. Must be within the range [0.0, 1.0].
        top_p (Optional[float]): The cumulative probability for nucleus sampling. Defaults to None.
        max_prompt_tokens (Optional[int]): The maximum number of tokens allowed in the prompt. Defaults to None.
        max_completion_tokens (Optional[int]): The maximum number of tokens allowed in the completion. Defaults to None.
        parallel_tool_calls (Optional[bool]): Whether the agent supports parallel tool calls. Defaults to None.
        
        Notes:
            - The `temperature` attribute controls the randomness of the agent's responses. Lower values make the output more
            deterministic, while higher values increase randomness.
            - The `top_p` attribute is used for nucleus sampling, where the model considers the smallest set of tokens whose
            cumulative probability exceeds the specified value.
            - Future support for truncation strategy and response format is planned.
    """
    agent_name: str
    instructions: str
    model: Optional[str] = None
    content_type: Optional[Literal["application/json", "text/plain"]] = "application/json"
    description: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0)
    top_p: Optional[float] = None
    max_prompt_tokens: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    parallel_tool_calls: Optional[bool] = None


class AzureOpenAIResponsesAgentConfig(BaseAgentConfig):
    """
    AzureOpenAIResponsesAgentConfig is a configuration class for an Azure Responses Agent.
    """
    type: Literal["AzureOpenAIResponsesAgentConfig"] = "AzureOpenAIResponsesAgentConfig"


class AzureAIAgentConfig(BaseAgentConfig):
    """
    AzureAIAgentConfig is a configuration class for an Azure AI Foundry Agent.
    """
    type: Literal["AzureAIAgentConfig"] = "AzureAIAgentConfig"

class AgentConfig(ConfigBase):
    """
    AgentConfig is a configuration class that inherits from ConfigBase.
    It represents the configuration details specific to an agent.

    Attributes:
        config_type (str): A string representing the type of configuration.
            Defaults to the value of `ConfigType.AGENT.value`.
        config_body (AgentConfigUnion): The body of the agent configuration,
            which can be one of the types defined in the AgentConfigUnion.
    """
    config_type: str = ConfigType.AGENT.value
    config_body: Union[AzureOpenAIResponsesAgentConfig, AzureAIAgentConfig]