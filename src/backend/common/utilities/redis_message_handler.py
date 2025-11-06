# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
from typing import Optional
from redis.asyncio import Redis

from common.contracts.common.answer import Answer
from common.contracts.orchestrator.response import OrchestratorResponse
from common.telemetry.app_tracer_provider import AppTracerProvider

class RedisMessageHandler:
    """
    Handles sending messages to a Redis channel.
    """
    def __init__(
        self,
        redis_client: Redis,
        redis_message_queue_channel: str,
        tracer_provider: Optional[AppTracerProvider] = None
    ) -> None:
        self.redis_client = redis_client
        self.redis_message_queue_channel = redis_message_queue_channel
        self.tracer_provider = tracer_provider

    async def send_update(
        self, 
        update_message: str, 
        session_id: str, 
        user_id: str, 
        dialog_id: str
    ) -> None:
        """
        Sends an update message to the Redis channel.
        """
        answer = Answer(answer_string=update_message, is_final=False)
        response = OrchestratorResponse(
            session_id=session_id,
            dialog_id=dialog_id,
            user_id=user_id,
            answer=answer,
        )
        return await self.__send_response(response)

    async def send_final_response(self, response: OrchestratorResponse) -> None:
        """
        Sends the final response to the Redis channel.
        """
        return await self.__send_response(response)

    async def __send_response(self, response: OrchestratorResponse) -> None:
        response_payload = {
            "payload": response.model_dump(),
        }

        # Append Trace Context if tracer_provider is set
        if self.tracer_provider:
            trace_context = {}
            self.tracer_provider.inject_trace_context(trace_context)
            response_payload["trace_context"] = trace_context or {}

        await self.redis_client.publish(self.redis_message_queue_channel, json.dumps(response_payload))
