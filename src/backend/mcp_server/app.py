# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
import os

from config.settings import config
from core.factory import MCPToolFactory
from services.jira_service import JiraService
from services.azure_devops_service import AzureDevopsService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VALID_TRANSPORTS = ["stdio", "http", "streamable-http", "sse"]

# Global factory instance
factory = MCPToolFactory()

# Initialize services
factory.register_service(JiraService())
factory.register_service(AzureDevopsService())

def create_fastmcp_server():
    """Create and configure FastMCP server."""
    try:
        # Create MCP server
        mcp_server = factory.create_mcp_server(name=config.server_name)

        logger.info("✅ FastMCP server created successfully")
        return mcp_server

    except ImportError:
        logger.warning("⚠️ FastMCP not available. Install with: pip install fastmcp")
        return None


# Create FastMCP server instance for fastmcp run command
mcp = create_fastmcp_server()


def log_server_info():
    """Log server initialization info."""
    if not mcp:
        logger.error("❌ FastMCP server not available")
        return

    summary = factory.get_tool_summary()
    logger.info(f"🚀 {config.server_name} initialized")
    logger.info(f"📊 Total services: {summary['total_services']}")
    logger.info(f"🔧 Total tools: {summary['total_tools']}")

    for domain, info in summary["services"].items():
        logger.info(
            f"   📁 {domain}: {info['tool_count']} tools ({info['class_name']})"
        )


def run_server(transport: str, host: str, port: int, **kwargs):
    """Run the FastMCP server with specified transport."""
    if not mcp:
        logger.error("❌ Cannot start FastMCP server - not available")
        return

    log_server_info()

    logger.info(f"🤖 Starting FastMCP server with {transport} transport")
    if transport in ["http", "streamable-http", "sse"]:
        logger.info(f"🌐 Server will be available at: http://{host}:{port}/mcp/")
        mcp.run(transport=transport, host=host, port=port, **kwargs)
    else:
        # For STDIO transport, only pass kwargs that are supported
        stdio_kwargs = {k: v for k, v in kwargs.items() if k not in ["log_level"]}
        mcp.run(transport=transport, **stdio_kwargs)


if __name__ == "__main__":
    import os

    # Read environment variables with defaults
    transport = os.environ.get("MCP_TRANSPORT", "http").lower()
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "12321"))

    config.server_name = os.environ.get("MCP_SERVER_NAME", "ReleaseManagerMcpServer")
    config.debug = os.environ.get("MCP_DEBUG", "").lower() in ("true", "1", "yes", "y")

    # Validate transport option
    if transport not in VALID_TRANSPORTS:
        logger.warning(f"Invalid transport: {transport}. MCP Server will default to stdio")
        transport = "stdio"

    # Run the server
    run_server(
        transport=transport,
        host=host,
        port=port,
        log_level="debug" if config.debug else "info",
    )
