# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
import subprocess
import shutil
import json
import asyncio

import aiohttp_cors
from aiohttp import web
from opentelemetry import trace
from redis.asyncio import Redis

from config import DefaultConfig
from models.devops_settings import DevOpsSettings
from models.devops_mcp_settings import DevOpsMcpSettings
from models.jira_settings import JiraSettings
from models.visualization_settings import VisualizationSettings
from agents.agent_orchestrator import AgentOrchestrator
from plugins.az_devops_plugin import AzDevOpsPluginFactory, AzDevOpsPluginInitializationError

from common.contracts.common.answer import Answer
from common.contracts.common.error import Error
from common.contracts.orchestrator.request import Request as OrchestratorRequest
from common.contracts.orchestrator.response import Response as OrchestratorResponse
from common.utilities.files import load_file
from common.utilities.redis_message_handler import RedisMessageHandler
from common.utilities.runtime_config import get_orchestrator_runtime_config
from common.utilities.thread_safe_cache import ThreadSafeCache

AGENT_CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

DefaultConfig.initialize()

tracer_provider = DefaultConfig.tracer_provider
tracer_provider.set_up()
tracer = trace.get_tracer(__name__)

# get the logger that is already initialized
logger = DefaultConfig.logger
logger.set_base_properties(
    {
        "ApplicationName": "ORCHESTRATOR_SERVICE",
    }
)

# Create route definitions for API endpoints
routes = web.RouteTableDef()

# Redis client for messaging
redis_messaging_client = Redis(
    host=DefaultConfig.REDIS_HOST,
    port=DefaultConfig.REDIS_PORT,
    password=DefaultConfig.REDIS_PASSWORD,
    ssl=False,
    decode_responses=True,
)

# Thread-safe cache to handle session to orchestrator mapping
orchestrators = ThreadSafeCache[AgentOrchestrator](logger)

# Global MCP plugin factory for Azure DevOps
mcp_plugin_factory = None

default_runtime_config = load_file(
    os.path.join(
        os.path.dirname(__file__),
        "static",
        "release_manager_config.yaml",
    ),
    "yaml",
)


# Health check endpoint
@routes.get("/health")
async def health_check(request: web.Request):
    return web.Response(text="Orchestrator is running!", status=200)


async def run_agent_orchestration(request_payload: str, message_handler: RedisMessageHandler):
    try:
        orchestrator_request = OrchestratorRequest(**request_payload)
    except Exception as e:
        logger.error(f"Failed to parse request data: {e} \n Request payload: {request_payload}")
        error = Error(
            error_str=f"Failed to parse request data: {e} \n Request payload: {request_payload}", retry=False
        )
        response = OrchestratorResponse(answer=Answer(is_final=True), error=error)

        await message_handler.send_final_response(response)
        return

    await message_handler.send_update("Processing your request...", orchestrator_request.dialog_id)

    logger.set_base_properties(
        {
            "ApplicationName": "ORCHESTRATOR_SERVICE",
            "session_id": orchestrator_request.session_id,
            "user_id": orchestrator_request.user_id,
        }
    )
    logger.info(f"Received orchestration request: {request_payload} for session: {orchestrator_request.session_id}")

    try:
        # Lookup agent orchestrator for given session id
        # If not found, create one just in time
        agent_orchestrator = await orchestrators.get_async(orchestrator_request.session_id)
        if not agent_orchestrator:
            logger.info(f"Agent orchestrator not found for session {orchestrator_request.session_id}. Creating..")

            orchestrator_runtime_config = await get_orchestrator_runtime_config(
                logger=logger,
                default_runtime_config=default_runtime_config
            )
            logger.info(f"Resolved orchestrator runtime config: {orchestrator_runtime_config}")

            agent_orchestrator = AgentOrchestrator(
                logger=logger,
                message_handler=message_handler,
                jira_settings=JiraSettings(
                    server_url=DefaultConfig.JIRA_SERVER_ENDPOINT,
                    username=DefaultConfig.JIRA_SERVER_USERNAME,
                    password=DefaultConfig.JIRA_SERVER_PASSWORD,
                    config_file_path=AGENT_CONFIG_FILE_PATH,
                    use_mcp_server=DefaultConfig.USE_JIRA_MCP_SERVER,
                ),
                devops_settings=DevOpsSettings(
                    use_mcp_server=DefaultConfig.USE_AZURE_DEVOPS_MCP_SERVER,
                    mcp_server_endpoint=DefaultConfig.AZURE_DEVOPS_MCP_SERVER_ENDPOINT,
                    mcp_plugin_factory=mcp_plugin_factory,
                ),
                visualization_settings=VisualizationSettings(
                    storage_account_name=DefaultConfig.STORAGE_ACCOUNT_NAME,
                    visualization_data_blob_container=DefaultConfig.VISUALIZATION_DATA_CONTAINER,
                ),
                configuration=orchestrator_runtime_config,
                project_endpoint=DefaultConfig.AZURE_AI_PROJECT_ENDPOINT,
            )

            # Initialize workflow
            await agent_orchestrator.initialize_agent_workflow()

            # Add to session cache
            await orchestrators.add_async(orchestrator_request.session_id, agent_orchestrator)
            logger.info(f"Agent orchestrator created successfully for session {orchestrator_request.session_id}")

        # Invoke agent workflow
        response = await agent_orchestrator.start_agent_workflow(orchestrator_request)

        logger.info(f"Orchestration completed for session {orchestrator_request.session_id} with response: {response.model_dump_json()}")
        await message_handler.send_final_response(response)
    except Exception as e:
        logger.exception(f"Exception in /run_agent_orchestration: {e}")
        error = Error(error_str="An error occurred. Please retry..", retry=False)
        response = OrchestratorResponse(
            session_id=orchestrator_request.session_id,
            dialog_id=orchestrator_request.dialog_id,
            user_id=orchestrator_request.user_id,
            answer=Answer(is_final=True),
            error=error,
        )
        await message_handler.send_final_response(response)


async def __validate_mcp_prerequisites() -> bool:
    """Validate that Node.js and npm are available for MCP server."""
    try:
        # Check if Node.js is installed
        node_result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if node_result.returncode != 0:
            logger.warning("Node.js not found. Please install Node.js to enable MCP functionality.")
            return False

        # Check if npx is available
        npx_cmd = shutil.which("npx")
        if not npx_cmd:
            logger.warning("npx is not available")
            return False

        logger.info(f"Node.js version: {node_result.stdout.strip()}")
        logger.info("MCP prerequisites validated successfully")
        return True
    except Exception as e:
        logger.warning(f"MCP prerequisite validation failed: {e}")
        return False

async def __initialize_azure_devops_mcp() -> bool:
    """Initialize Azure DevOps MCP server if configured."""
    global mcp_plugin_factory

    # Skip if Azure DevOps is not configured
    if not DefaultConfig.AZURE_DEVOPS_ORG_NAME:
        logger.info("Azure DevOps organization not configured - skipping MCP initialization")
        return False

    # Validate prerequisites
    if not await __validate_mcp_prerequisites():
        logger.warning("MCP prerequisites not met - Azure DevOps functionality may be limited")
        return False

    try:
        # Create DevOps settings based on the mcp.json specification
        devops_settings = DevOpsMcpSettings(
            azure_org_name=DefaultConfig.AZURE_DEVOPS_ORG_NAME,
            mcp_server_command="npx",
            mcp_server_args=[
                "-y",
                "@azure-devops/mcp",
                DefaultConfig.AZURE_DEVOPS_ORG_NAME
            ],
            mcp_timeout=30,
            auto_start_server=True,
            max_retries=3,
            retry_delay=5,
            essential_tool_categories={
                "work_items": ["wit", "work", "item"],
                "repositories": ["repo", "git"],
                "builds": ["build", "pipeline"],
                "releases": ["release"]
            }
        )

        # Initialize the MCP plugin factory
        mcp_plugin_factory = AzDevOpsPluginFactory(logger)

        # Create and test the plugin connection
        _, status = await mcp_plugin_factory.create_plugin(
            devops_settings,
            plugin_name="AzureDevOpsMCP"
        )

        # Log initialization results
        logger.info(f"Azure DevOps MCP initialized with {status.tools_available} tools")
        if status.warnings:
            for warning in status.warnings:
                logger.warning(f"MCP initialization warning: {warning}")

        if status.missing_categories:
            logger.warning(f"Missing essential tool categories: {status.missing_categories}")

        return True

    except AzDevOpsPluginInitializationError as e:
        logger.error(f"Azure DevOps MCP initialization failed: {e}")
        mcp_plugin_factory = None
        return False
    except Exception as e:
        logger.exception(f"Unexpected error during MCP initialization: {e}")
        mcp_plugin_factory = None
        return False


async def worker():
    """
    Worker function to process tasks from the Redis task queue.
    Continuously polls the Redis task queue for new tasks and processes them.
    """
    while True:
        task_data = await redis_messaging_client.lpop(DefaultConfig.REDIS_TASK_QUEUE_CHANNEL)
        if task_data:
            try:
                task = json.loads(task_data)

                session_id = task.get("session_id")
                thread_id = task.get("thread_id")
                user_id = task.get("user_id")
            except Exception as e:
                logger.error(f"Failed to parse task data: {e}")
                continue
            with tracer.start_as_current_span("process_task_at_orchestrator") as span:
                span.set_attribute("session_id", session_id)
                logger.info(f"Received task data: {task_data}")
                message_handler = RedisMessageHandler(
                    session_id=session_id,
                    thread_id=thread_id,
                    user_id=user_id,
                    redis_client=redis_messaging_client,
                    redis_message_queue_channel=DefaultConfig.REDIS_MESSAGE_QUEUE_CHANNEL,
                )
                await run_agent_orchestration(task, message_handler)
        else:
            await asyncio.sleep(1)


async def run_workers():
    await asyncio.gather(*[worker() for _ in range(DefaultConfig.AGENT_ORCHESTRATOR_MAX_CONCURRENCY)])

async def on_startup(app):
    """Initialize resources and connections during server startup."""
    logger.info("Starting Release Manager orchestrator service...")

    if DefaultConfig.USE_AZURE_DEVOPS_MCP_SERVER:
        logger.info("Azure DevOps MCP server usage is enabled. Skipping official MCP server initialization.")
    else:
        # Initialize Azure DevOps MCP server
        mcp_success = await __initialize_azure_devops_mcp()
        if not mcp_success:
            logger.warning("Azure DevOps MCP initialization failed - functionality may be limited.")

    logger.info("Initializing Agent Orchestrator workers..")
    asyncio.create_task(run_workers())

    logger.info("Release Manager orchestrator service startup completed")


async def on_shutdown(app):
    """Cleanup resources and connections during server shutdown."""
    logger.info("Shutting down Release Manager orchestrator service...")

    # Cleanup MCP plugin factory
    global mcp_plugin_factory
    if mcp_plugin_factory:
        try:
            await mcp_plugin_factory.cleanup()
            logger.info("Azure DevOps MCP plugin cleaned up successfully")
        except Exception as e:
            logger.warning(f"Error cleaning up MCP plugin: {e}")
        finally:
            mcp_plugin_factory = None

    # Cleanup orchestrator cache
    try:
        orchestrators._cache.clear()
        logger.info("Orchestrator cache cleaned up successfully")
    except Exception as e:
        logger.warning(f"Error cleaning up orchestrator cache: {e}")

    logger.info("Release Manager orchestrator service shutdown completed")


def start_server(host: str, port: int):
    """Start the Release Manager orchestrator server."""
    logger.info(f"Initializing Release Manager orchestrator server on {host}:{port}")

    app = web.Application()
    app.add_routes(routes)

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

    # Register startup and shutdown handlers
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    logger.info("Starting server - Azure DevOps MCP will be initialized during startup")

    # Start server - on_startup will handle MCP initialization
    web.run_app(app, host=host, port=port)


if __name__ == "__main__":
    print("=" * 60)
    print("  RELEASE MANAGER ORCHESTRATOR SERVICE")
    print("=" * 60)
    print(f"Host: {DefaultConfig.SERVICE_HOST}")
    print(f"Port: {DefaultConfig.SERVICE_PORT}")
    print(f"Azure DevOps Org: {DefaultConfig.AZURE_DEVOPS_ORG_NAME or 'Not configured'}")
    print("=" * 60)

    try:
        start_server(host=DefaultConfig.SERVICE_HOST, port=DefaultConfig.SERVICE_PORT)
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        raise