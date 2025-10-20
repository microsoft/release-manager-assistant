# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import os
from typing import List

from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import MessageRole as FoundryMessageRole, ThreadMessage
from agent_framework import ChatAgent, HostedCodeInterpreterTool
from agent_framework_azure_ai import AzureAIAgentClient

from common.utilities.blob_store_helper import BlobStoreHelper
from common.utilities.redis_message_handler import RedisMessageHandler
from common.telemetry.app_logger import AppLogger
from common.agent_factory.agent_base import AgentBase
from common.contracts.configuration.agent_config import AzureAIAgentConfig

LOCAL_VISUALIZATION_DATA_DIR = "visualization"

class FinalAnswerGeneratorAgent(AgentBase):
    """
    The Final Answer Generator Agent interface that uses Code Interpreter tool to generate final answers.
    """
    def __init__(self, logger: AppLogger):
        """Initialize the FinalAnswerGeneratorAgent instance."""
        super().__init__(logger)


    async def create_agent(
        self,
        client: AzureAIAgentClient,
        configuration: AzureAIAgentConfig,
    ) -> ChatAgent:
        """
        Create the actual FinalAnswerGeneratorAgent in AI Foundry.

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
            raise ValueError("Foundry agent configuration is required for FinalAnswerGeneratorAgent.")

        self._logger.info(f"Creating final answer generator agent: {configuration.agent_name}")

        try:
            agent = client.create_agent(
                name=configuration.agent_name,
                instructions=configuration.instructions,
                tools=[HostedCodeInterpreterTool()],
            )

            self._logger.info(f"Successfully created final answer generator agent: {configuration.agent_name}")
            return agent
        except Exception as e:
            self._logger.error(f"Failed to create final answer generator agent: {e}")
            raise

    async def generate_visualization_data(
        self,
        project_client: AIProjectClient,
        blob_store_helper: BlobStoreHelper,
        message_handler: RedisMessageHandler,
        thread_id: str,
        dialog_id: str,
    ) -> List[str]:
        visualization_image_sas_urls = []

        try:
            last_message: ThreadMessage = await project_client.agents.messages.get_last_message_by_role(
                thread_id=thread_id,
                role=FoundryMessageRole.AGENT
            )

            if len(last_message.image_contents) > 0:
                await message_handler.send_update(update_message="Generating visualization...", dialog_id=dialog_id)

                for image_content in last_message.image_contents:
                    try:
                        self._logger.info(f"Image File ID: {image_content.image_file.file_id}")
                        file_name = f"{image_content.image_file.file_id}_image_file.png"

                        # Save the image file to the target directory
                        await project_client.agents.files.save(
                            file_id=image_content.image_file.file_id,
                            file_name=file_name,
                            target_dir=LOCAL_VISUALIZATION_DATA_DIR,
                        )

                        # Upload image file to storage and get the URL
                        image_url = await blob_store_helper.upload_file_from_path_and_get_sas_url(
                            local_file_path=os.path.join(LOCAL_VISUALIZATION_DATA_DIR, file_name),
                            blob_name=file_name,
                        )
                        visualization_image_sas_urls.append(image_url)
                    except Exception as e:
                        self._logger.exception(f"Error processing image file ID {image_content.image_file.file_id}: {e}. Skipping this file.")
                        continue  # Continue to the next file if an error occurs
                
                self._logger.info(f"Visualization data generated successfully with {len(visualization_image_sas_urls)} image(s).")
                await message_handler.send_update(update_message="Successfully generated visualization data. Almost there..", dialog_id=dialog_id)
                return visualization_image_sas_urls
            
        except Exception as e:
            self._logger.exception(f"Error generating visualization data: {e}. Skipping...")
            return []
