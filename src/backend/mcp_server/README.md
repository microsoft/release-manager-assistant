# Release Manager Assistant MCP Server

A FastMCP-based Model Context Protocol (MCP) server for the Release Manager Assistant solution accelerator.

## Features

- **FastMCP Server**: Pure FastMCP implementation supporting multiple transport protocols
- **Factory Pattern**: Reusable MCP tools factory for easy service management
- **Support for multiple tools**: Multiple tools supported by the same MCP server - Jira and Azure DevOps
- **Multiple Transports**: STDIO, HTTP (Streamable), and SSE transport support
- **Docker Support**: Containerized deployment with health checks

## Architecture

```
src/backend/mcp_server/
├── core/                           # Core factory and base classes
│   ├── __init__.py
│   └── factory.py                  # MCPToolFactory and base classes
├── services/                       # Domain-specific service implementations
│   ├── __init__.py
│   ├── jira_service.py             # Jira Service
│   ├── azure_devops_service.py     # Azure DevOps
├── config/                         # Configuration management
│   ├── __init__.py
│   └── settings.py                 # Settings and configuration
├── app.py                          # MCP server implementation
├── .env.template                   # The environment template file.
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container configuration
└── README                          # Instructions on how to run and test.
```

## Available Services

### Jira Service

### Azure DevOps Service

## Quick Start

### Development Setup

1. **Clone and Navigate**:

   ```bash
   cd src/backend/mcp
   ```

2. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**:

   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

4. **Start the Server**:

   ```bash
   # Default STDIO transport (for local MCP clients)
   python app.py

   # HTTP transport (for web-based clients)
   python app.py --transport http --port 12321

   # Using FastMCP CLI (recommended)
   fastmcp run app.py -t streamable-http --port 12321 -l DEBUG

   # Debug mode with authentication disabled
   python app.py --transport http --debug
   ```

### Transport Options

**1. STDIO Transport (default)**

- 🔧 Perfect for: Local tools, command-line integrations, Claude Desktop
- 🚀 Usage: `python app.py` or `python app.py --transport stdio`

**2. HTTP (Streamable) Transport**

- 🌐 Perfect for: Web-based deployments, microservices, remote access
- 🚀 Usage: `python app.py --transport http --port 12321`
- 🌐 URL: `http://127.0.0.1:12321/mcp/`

### FastMCP CLI Usage

```bash
# Standard HTTP server
fastmcp run app.py -t streamable-http --port 12321 -l DEBUG

# With custom host
fastmcp run app.py -t streamable-http --host 0.0.0.0 --port 12321 -l DEBUG

# STDIO transport (for local clients)
fastmcp run app.py -t stdio

# Development mode with MCP Inspector
fastmcp dev app.py -t streamable-http --port 12321
```

### Docker Deployment

1. **Build and Run**:

   ```bash
   docker-compose up --build
   ```

2. **Access the Server**:
   - MCP endpoint: http://localhost:12321/mcp/
   - Health check available via custom routes

### VS Code Development

1. **Open in VS Code**:

   ```bash
   code .
   ```

2. **Use Debug Configurations**:
   - `Debug MCP Server (STDIO)`: Run with STDIO transport
   - `Debug MCP Server (HTTP)`: Run with HTTP transport

## Configuration

### Environment Variables

Create a `.env` file based on `.env.template`:

```env
# Server Settings
MCP_HOST=0.0.0.0
MCP_PORT=12321
MCP_DEBUG=false
MCP_SERVER_NAME=ReleaseManagerAssistantMcpServer
```

## MCP Client Usage

### Python Client

```python
from fastmcp import Client

# Connect to HTTP server
client = Client("http://localhost:12321")

async with client:
    # List available tools
    tools = await client.list_tools()
    print(f"Available tools: {[tool.name for tool in tools]}")

    # Call a tool
    result = await client.call_tool("greet", {"name": "World"})
    print(result)
```

### Command Line Testing

```bash
# Test the server is running
curl http://localhost:12321/mcp/

# With FastMCP CLI for testing
fastmcp dev app.py -t streamable-http --port 12321
```

## Quick Test

**Test HTTP Transport:**

```bash
# Start HTTP server
python app.py --transport http --port 12321 --debug

# Test with FastMCP client
python -c "
from fastmcp import Client
import asyncio
async def test():
    async with Client('http://localhost:12321') as client:
        result = await client.call_tool('greet', {'name': 'Test'})
        print(result)
asyncio.run(test())
"
```

**Test with FastMCP CLI:**

```bash
# Start with FastMCP CLI
fastmcp run app.py -t streamable-http --port 12321 -l DEBUG

# Server will be available at: http://127.0.0.1:12321/mcp/
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're in the correct directory and dependencies are installed
2. **Port Conflicts**: Change the port in configuration if 12321 is already in use
3. **Missing fastmcp**: Install with `pip install fastmcp`

### Debug Mode

Enable debug mode for detailed logging:

```bash
python app.py --debug
```

Or set in environment:

```env
MCP_DEBUG=true
```

### Logs

Check container logs:

```bash
docker-compose logs rma-mcp-server
```

## Server Arguments

```bash
usage: app.py [-h] [--transport {stdio,http,streamable-http,sse}]
                     [--host HOST] [--port PORT] [--debug]

Release Manager Assistant MCP Server

options:
  -h, --help            show this help message and exit
  --transport, -t       Transport protocol (default: stdio)
  --host HOST           Host to bind to for HTTP transport (default: 127.0.0.1)
  --port, -p PORT       Port to bind to for HTTP transport (default: 12321)
  --debug               Enable debug mode
```