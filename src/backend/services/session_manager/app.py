# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
import asyncio
import aiohttp_cors
from aiohttp import web

from config import DefaultConfig
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from handlers.client_manager import ClientManager

from common.contracts.orchestrator.response import OrchestratorResponse
from common.utilities.message_queue_manager import MessageQueueManager
from common.utilities.task_queue_manager import TaskQueueManager
from common.utilities.thread_safe_cache import ThreadSafeCache

routes = web.RouteTableDef()

DefaultConfig.initialize()

tracer_provider = DefaultConfig.tracer_provider
tracer_provider.initialize()

# get the logger that is already initialized
logger = DefaultConfig.logger
logger.set_base_properties(
    {
        "ApplicationName": "SESSION_MANAGER_SERVICE",
    }
)

request_task_manager = TaskQueueManager(
    logger,
    queue_name=DefaultConfig.SESSION_MANAGER_CHAT_REQUEST_TASK_QUEUE_CHANNEL,
    redis_host=DefaultConfig.REDIS_HOST,
    redis_port=DefaultConfig.REDIS_PORT,
    redis_password=DefaultConfig.REDIS_PASSWORD,
    redis_ssl=False,
)

clients = ThreadSafeCache[ClientManager](logger)

response_message_queue = MessageQueueManager(
    logger=logger,
    redis_host=DefaultConfig.REDIS_HOST,
    redis_port=DefaultConfig.REDIS_PORT,
    redis_password=DefaultConfig.REDIS_PASSWORD,
    redis_ssl=False,
)

# AI Foundry Project Client
ai_foundry_project_client = AIProjectClient(
    endpoint=DefaultConfig.AZURE_AI_PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)


@routes.get("/health")
async def health_check(request: web.Request):
    return web.Response(text="Session manager is running!", status=200)


@routes.get("/api/query")
async def ws_chat(request: web.Request):
    session_id = request.rel_url.query.get("session_id")
    if not session_id:
        return web.json_response({"error": "session_id is required"}, status=400)
    
    with tracer_provider.trace_session(
        session_id=session_id,
        request_path="/api/query"
    ):
        logger = DefaultConfig.logger
        base_properties = {
            "ApplicationName": "SESSION_MANAGER_SERVICE",
            "path": "/api/query",
            "session_id": session_id,
        }
        logger.set_base_properties(base_properties)

        logger.log_request_received(f"Request received for session {session_id}.")

        client_manager = None
        try:
            # Create new client manager and add it to cache.
            client_manager = ClientManager(
                session_id=session_id,
                logger=logger,
                tracer_provider=tracer_provider,
                ai_foundry_project_client=ai_foundry_project_client,
                task_manager=request_task_manager,
                max_response_timeout=DefaultConfig.SESSION_MAX_RESPONSE_TIMEOUT_IN_SECONDS,
            )

            await clients.add_async(session_id, client_manager)
            return await client_manager.try_accept_connection_async(session_id=session_id, client_request=request)
        finally:
            if client_manager:
                await client_manager.close_connection_async(session_id)
                await clients.remove_async(session_id)


async def on_chat_message_response(message: str):
    if not message:
        raise Exception("Incorrect message payload.")

    response_payload = json.loads(message)
    payload = response_payload.get("payload", {})
    orchestrator_response = OrchestratorResponse(**payload)

    client_manager = None
    
    # Extract trace context from request before agent orchestration
    trace_context = response_payload.get("trace_context", {})
    ctx = tracer_provider.extract_trace_context(trace_context)
    with tracer_provider.trace_message_dequeue(
        session_id=orchestrator_response.session_id,
        message_type=OrchestratorResponse.__name__,
        message_queue_name="Orchestrator-SessionManager",
        context=ctx
    ):
        try:
            logger = DefaultConfig.logger

            base_properties = {
                "ApplicationName": "SESSION_MANAGER_SERVICE",
                "session_id": orchestrator_response.session_id,
                "thread_id": orchestrator_response.thread_id,
                "user_id": orchestrator_response.user_id,
            }
            logger.set_base_properties(base_properties)

            logger.info(
                f"ConversationHandler: message response received for connection {orchestrator_response.session_id}."
            )

            client_manager = await clients.get_async(orchestrator_response.session_id)
            return await client_manager.handle_chat_response_async(orchestrator_response)
        except Exception as ex:
            logger.error(f"Failed to send a response to client for connection {orchestrator_response.session_id}: {ex}")
            if client_manager:
                await client_manager.close_connection_async(orchestrator_response.session_id, message="Internal Error.")


def start_server(host: str, port: int):
    app = web.Application(logger=logger)
    app.add_routes(routes)

    app.on_startup.append(on_startup)

    # Configure default CORS settings.
    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
        },
    )

    # Configure CORS on all routes.
    for route in list(app.router.routes()):
        cors.add(route)

    # Start server
    web.run_app(app, host=host, port=port)


async def on_startup(app):
    asyncio.create_task(
        response_message_queue.subscribe_async(
            channels=[DefaultConfig.SESSION_MANAGER_CHAT_RESPONSE_MESSAGE_QUEUE_CHANNEL],
            on_message_received=on_chat_message_response,
        )
    )


if __name__ == "__main__":
    asyncio.to_thread(start_server(host=DefaultConfig.SERVICE_HOST, port=DefaultConfig.SERVICE_PORT))
