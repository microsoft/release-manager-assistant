# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from agent_framework import (
    AgentRunResponse,
    AgentThread,
    ChatMessage,
    Role,
)
from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework_azure_ai import AzureAIAgentClient
from agents.agent_factory import ReleaseManagerAgentFactory
from azure.ai.projects.aio import AIProjectClient
from azure.ai.agents.models import AgentThread as FoundryAgentThread, MessageRole as FoundryMessageRole
from azure.core.exceptions import HttpResponseError
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from azure.identity import DefaultAzureCredential

from models.agents import Agent
from models.jira_settings import JiraSettings
from models.visualization_settings import VisualizationSettings
from plugins.az_devops_plugin import AzDevOpsPluginFactory

from common.agent_factory.agent_base import AgentBase
from common.contracts.common.answer import Answer
from common.contracts.configuration.orchestrator_config import ResolvedOrchestratorConfig
from common.contracts.orchestrator.request import Request
from common.contracts.orchestrator.response import Response
from common.telemetry.app_logger import AppLogger
from common.utilities.blob_store_helper import BlobStoreHelper
from common.utilities.redis_message_handler import RedisMessageHandler
from common.contracts.configuration.agent_config import (
    AzureOpenAIResponsesAgentConfig,
    AzureAIAgentConfig
)

LOCAL_VISUALIZATION_DATA_DIR = "visualization"

# Initialize the update messages to be displayed to the user
update_messages = [
    "Aggregating relevant information for your request...",
    "Compiling data for your query...",
    "Generating plan to provide accurate results...",
]


@dataclass
class AgentRuntimeConfig:
    agent: AgentBase
    agent_thread: AgentThread


class AgentOrchestrator:
    def __init__(
        self,
        logger: AppLogger,
        message_handler: RedisMessageHandler,
        jira_settings: JiraSettings,
        mcp_plugin_factory: AzDevOpsPluginFactory,
        visualization_settings: VisualizationSettings,
        project_endpoint: str,
        configuration: ResolvedOrchestratorConfig = None
    ) -> None:
        self.logger = logger
        self.message_handler = message_handler

        self.jira_settings = jira_settings
        self.mcp_plugin_factory = mcp_plugin_factory

        self.blob_store_helper = BlobStoreHelper(
            logger=self.logger,
            storage_account_name=visualization_settings.storage_account_name,
            container_name=visualization_settings.visualization_data_blob_container
        )

        self.chat_history: List[ChatMessage] = []

        # Agent threads
        self.planner_agent_thread: AgentThread = None
        self.jira_agent_thread: AgentThread = None
        self.azure_devops_agent_thread: AgentThread = None
        self.visualization_agent_thread: AgentThread = None
        self.fallback_agent_thread: AgentThread = None

        # Currently, configuration is updated only once per session i.e. for consecutive requests from the same session, configuration is not updated.
        # This is to avoid re-initializing the kernel and agents for every request.
        self.config: ResolvedOrchestratorConfig = configuration

        # Initialize agent name to agent instance map
        self.agent_runtime_config_map: Dict[Agent, AgentRuntimeConfig] = {}
        self.project_endpoint: str = project_endpoint


    async def __invoke_agent(
        self,
        agent: Agent,
        messages: str | ChatMessage | list[str | ChatMessage]
    ) -> AgentRunResponse:
        """
        Invoke the specified agent with the provided messages and thread.
        """
        self.logger.info(f"Invoking agent of type: {agent}")

        agent_runtime_config = self.config.get_agent_config(agent.value)
        response: AgentRunResponse = await self.agent_runtime_config_map.get(agent).agent.run(
            messages=messages,
            thread=self.agent_runtime_config_map.get(agent).agent_thread,
            runtime_configuration=agent_runtime_config
        )

        if response is None:
            self.logger.warning(f"Agent {agent.name} response is empty.")

        return response

    async def __create_agent(
        self,
        agent: Agent,
        session_thread_id: str
    ) -> AgentRuntimeConfig:
        agent_config = self.config.get_agent_config(agent.value)
        if not agent_config:
            raise ValueError(f"Agent {agent.value} configuration not found in the provided config.")

        kwargs = {}
        if agent == Agent.JIRA_AGENT:
            kwargs['jira_settings'] = self.jira_settings
        elif agent == Agent.AZURE_DEVOPS_AGENT:
            kwargs['mcp_plugin_factory'] = self.mcp_plugin_factory

        try:
            _agent = await self.agent_factory.create_agent(
                agent_type=agent,
                configuration=agent_config,
                **kwargs
            )
        except Exception as e:
            self.logger.error(f"Failed to create agent {agent.value}: {str(e)}")
            raise

        agent_thread: AgentThread = None
        if isinstance(agent_config, AzureAIAgentConfig):
            agent_thread = AgentThread(service_thread_id=session_thread_id)
        elif isinstance(agent_config, AzureOpenAIResponsesAgentConfig):
            agent_thread = _agent.new_agent_thread() # Responses API expects a new thread per agent
        else:
            raise ValueError(f"Unsupported agent configuration type for agent {agent.value}.")

        return AgentRuntimeConfig(agent=_agent, agent_thread=agent_thread)

    async def initialize_agent_workflow(self) -> None:
        """
        Initialize the agent workflow by setting up the kernel, agents, and threads.
        """
        self.logger.info("Initializing agent workflow...")
        project_client = AIProjectClient(endpoint=self.project_endpoint, credential=AsyncDefaultAzureCredential())
        session_thread: FoundryAgentThread = await project_client.agents.threads.create()
        self.logger.info(f"Thread {session_thread.id} created successfully in Azure AI Foundry!")

        # AZURE AI FOUNDRY SETUP
        self.foundry_client = AzureAIAgentClient(
            project_client=project_client,
            thread_id=session_thread.id,
            async_credential=AsyncDefaultAzureCredential()
        )
        self.azure_openai_responses_client = AzureOpenAIResponsesClient(credential=DefaultAzureCredential())

        # AGENTS SETUP
        self.agent_factory: ReleaseManagerAgentFactory = await ReleaseManagerAgentFactory.get_instance()
        await self.agent_factory.initialize(
            logger=self.logger,
            foundry_client=self.foundry_client,
            azure_openai_responses_client=self.azure_openai_responses_client,
        )

        # 1. PLANNER AGENT SETUP
        self.planner_agent_thread = AgentThread(service_thread_id=session_thread.id)
        self.agent_runtime_config_map[Agent.PLANNER_AGENT] = await self.__create_agent(
            agent=Agent.PLANNER_AGENT,
            session_thread_id=session_thread.id
        )

        # 2. JIRA AGENT SETUP
        self.jira_agent_thread = AgentThread(service_thread_id=session_thread.id)
        self.agent_runtime_config_map[Agent.JIRA_AGENT] = await self.__create_agent(
            agent=Agent.JIRA_AGENT,
            session_thread_id=session_thread.id
        )

        # 3. AZURE DEVOPS AGENT SETUP
        self.agent_runtime_config_map[Agent.AZURE_DEVOPS_AGENT] = await self.__create_agent(
            agent=Agent.AZURE_DEVOPS_AGENT,
            session_thread_id=session_thread.id
        )

        # 4. VISUALIZATION AGENT SETUP
        self.agent_runtime_config_map[Agent.VISUALIZATION_AGENT] = await self.__create_agent(
            agent=Agent.VISUALIZATION_AGENT,
            session_thread_id=session_thread.id,
        )

        # FALLBACK AGENT SETUP
        self.agent_runtime_config_map[Agent.FALLBACK_AGENT] = await self.__create_agent(
            agent=Agent.FALLBACK_AGENT,
            session_thread_id=session_thread.id,
        )

    async def __parse_planner_agent_response(self, planner_agent_response: AgentRunResponse) -> Dict[str, Any]:
        """
        Parse the planner agent response to extract the plan.
        """
        try:
            response_dict = json.loads(planner_agent_response.text)

            return {
                "plan_id": response_dict.get("plan_id"),
                "agents": response_dict.get("agents", []),
                "justification": response_dict.get("justification", "").strip(),
            }
        except json.JSONDecodeError as e:
            self.logger.exception(f"Failed to parse planner agent response as JSON: {e}")
            raise ValueError("Invalid JSON response from planner agent.")

    async def __execute_planner(
        self,
        messages: Optional[str | ChatMessage | List[str | ChatMessage]]
    ) -> Dict[str, Any]:
        """
        Execute the planner agent with the provided messages.

        If no message(s) provided, entire chat history is used instead.
        """
        self.logger.info("Executing Planner Agent to generate orchestration plan...")

        planner_agent_response = await self.__invoke_agent(
            agent=Agent.PLANNER_AGENT,
            messages=messages if messages is not None else self.chat_history,
        )

        parsed_response = await self.__parse_planner_agent_response(planner_agent_response)
        return parsed_response

    async def __generate_visualization_data(self, thread_id: str, dialog_id: str) -> List[str]:
        visualization_image_sas_urls = []

        try:
            messages = await self.foundry_client.project_client.agents.messages.get_last_message_by_role(
                thread_id=thread_id,
                role=FoundryMessageRole.AGENT
            )

            if len(messages.image_contents) > 0:
                await self.message_handler.send_update(update_message="Generating visualization...", dialog_id=dialog_id)

            for image_content in messages.image_contents:
                try:
                    self.logger.info(f"Image File ID: {image_content.image_file.file_id}")
                    file_name = f"{image_content.image_file.file_id}_image_file.png"

                    # Save the image file to the target directory
                    await self.foundry_client.project_client.agents.files.save(
                        file_id=image_content.image_file.file_id,
                        file_name=file_name,
                        target_dir=LOCAL_VISUALIZATION_DATA_DIR,
                    )

                    # Upload image file to storage and get the URL
                    image_url = await self.blob_store_helper.upload_file_from_path_and_get_sas_url(
                        local_file_path=os.path.join(LOCAL_VISUALIZATION_DATA_DIR, file_name),
                        blob_name=file_name,
                    )
                    visualization_image_sas_urls.append(image_url)
                except Exception as e:
                    self.logger.exception(f"Error processing image file ID {image_content.image_file.file_id}: {e}. Skipping this file.")
                    continue  # Continue to the next file if an error occurs
        except Exception as e:
            self.logger.exception(f"Error generating visualization data: {e}. Skipping...")
            return []

        self.logger.info(f"Visualization data generated successfully with {len(visualization_image_sas_urls)} image(s).")
        await self.message_handler.send_update(update_message="Successfully generated visualization data. Almost there..", dialog_id=dialog_id)

        return visualization_image_sas_urls

    async def start_agent_workflow(self, request: Request) -> Response:
        """
        Start the agent workflow by invoking the JIRA and Azure DevOps agents, and generating visualization data.

        Args:
            request (Request): The request object containing user input and session information.

        Returns:
            Response: The response object containing the final answer and visualization data.
        """
        self.logger.info("Starting agent workflow orchestration...")

        self.logger.set_base_properties(
            {
                "ApplicationName": "ORCHESTRATOR_SERVICE",
                "user_id": request.user_id,
                "session_id": request.session_id,
                "dialog_id": request.dialog_id,
            }
        )
        self.logger.info("Received agent workflow orchestration request.")

        try:
            message = ChatMessage(role=Role.USER, text=request.message)
            self.chat_history.append(ChatMessage(role=Role.USER, text=request.message))

            await self.message_handler.send_update("Generating plan...", dialog_id=request.dialog_id)

            try:
                # Execute Planner agent to generate the plan
                plan = await self.__execute_planner(self.chat_history)

                if not plan or Agent.FALLBACK_AGENT.value in plan.get("agents"):
                    self.logger.error(
                        "No plan generated by the Planner agent or no agents found in the plan. Invoking fallback agent.."
                    )

                    fallback_response = await self.__invoke_agent(Agent.FALLBACK_AGENT, message)
                    return Response(
                        session_id=request.session_id,
                        dialog_id=request.dialog_id,
                        user_id=request.user_id,
                        answer=Answer(
                            answer_string=fallback_response.text,
                            is_final=True,
                            data_points=[],
                            speaker_locale=request.locale,
                        ),
                    )

                self.logger.info(f"Orchestration Plan generated successfully: {plan}")

                intermediate_context = ""
                visualization_image_sas_urls: list[str] = []

                # Iterate through the agents in the plan and invoke them
                for agent_name in plan["agents"]:
                    agent = Agent(agent_name)

                    if agent not in self.agent_runtime_config_map:
                        raise ValueError(f"Agent {agent} not found in configuration.")

                    # Invoke the agent with the plan
                    agent_response = await self.__invoke_agent(
                        agent=agent,
                        messages=self.chat_history,
                    )
                    self.logger.info(f"Agent {agent.name} response: {agent_response}")

                    # Visualization Agent responds with visualization data in the form of file IDs
                    # If the agent is the Visualization Agent, handle the response accordingly.
                    if agent == Agent.VISUALIZATION_AGENT:
                        visualization_image_sas_urls = await self.__generate_visualization_data(
                            thread_id=self.agent_runtime_config_map.get(agent).agent_thread.service_thread_id,
                            dialog_id=request.dialog_id
                        )
                    else:
                        # Clean up the response to remove any unwanted characters
                        clean_agent_response = agent_response.text.replace("\n", "").replace("\r", "")

                        # Pass full clean context to next agent
                        intermediate_context += f"{clean_agent_response}\n\n"

                # Update the chat history with the final response
                self.chat_history.append(intermediate_context)

                return Response(
                    session_id=request.session_id,
                    dialog_id=request.dialog_id,
                    user_id=request.user_id,
                    answer=Answer(
                        answer_string=intermediate_context,
                        is_final=True,
                        data_points=(visualization_image_sas_urls if visualization_image_sas_urls else []),
                        speaker_locale=request.locale,
                    ),
                )
            except HttpResponseError as http_error:
                self.logger.exception(f"HTTP error during agent invocation: {http_error}")
                raise
            except Exception as e:
                self.logger.exception(f"Error during agent invocation: {e}")
                raise
        except Exception as e:
            self.logger.exception(f"Exception occurred while orchestrating agents: {e}")
            raise