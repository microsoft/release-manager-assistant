# Release Manager Assistant Setup Instructions

## Overview

The Release Manager solution is designed to assist in decision-making for software delivery releases by integrating three key agents:

- **JIRA Agent**: Fetches and processes data from JIRA backend to track issues, including custom fields. Agent has access to make changes in the JIRA system.
- **Azure DevOps Agent**: Interfaces with Azure DevOps via Model Context Protocol (MCP) to retrieve work items, builds, releases, and project information.
- **Visualization Agent**: Provides actionable insights and visual representations of release progress and associated tasks.

By combining these agents, the Release Manager enables streamlined release planning and execution with robust error handling and flexible authentication options.

## Prerequisites

Before setting up the solution, ensure the following:

1. **System Requirements**:
    - **Operating System**: Windows (can be extended to Linux/macOS)
    - **Python 3.12 or higher** installed with pip
    - **[Node.js 20+](https://nodejs.org/en/download)** installed (required for Azure DevOps MCP Server)
    - **[Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)** installed and configured
    - **[Visual Studio Code](https://code.visualstudio.com/)** with [Python Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
    - **Docker** runtime installed to run a Redis container (Redis acts as a message broker in the backend system)

      **Setting up Redis Container:**
      ```bash
      # Pull and run Redis container with authentication
      docker pull redis:latest
      docker run --name redis-container -d -p 6379:6379 \
        -e REDIS_PASSWORD=redis_password \
        redis:latest --requirepass redis_password

      # Verify container is running
      docker ps | grep redis-container
      ```

2. **Access Credentials & Permissions**:
    - **JIRA System**: Username, password, and API access permissions
    - **Azure DevOps**: Organization access with appropriate work item, build, and release permissions
    - **Azure Subscription**: With permissions to create/manage Azure AI Foundry resources
    - **Azure Key Vault**: Access for secure credential storage (recommended for production)

3. **Cloud Service Dependencies**:
    - **Azure AI Foundry Agent Service**: [Setup Guide](https://learn.microsoft.com/en-us/azure/ai-services/agents/overview)
    - **Azure OpenAI Service**: For LLM capabilities and agent interactions
    - **Azure Storage Account**: For visualization data and artifact storage
    - **Application Insights**: For monitoring and telemetry (optional but recommended)

4. **Azure DevOps MCP Server Setup**:
    
    The Azure DevOps Agent requires the Azure DevOps MCP Server to be configured with comprehensive tool discovery capabilities. The MCP server provides access to:
    - Work Items (CRUD operations, batch processing, search)
    - Builds and Releases (status tracking, artifact management)  
    - Repositories and Pull Requests (code change tracking)
    - Teams, Iterations, and Project management
    - Advanced search across all Azure DevOps entities
    
    **Authentication Options (Choose One):**
    
    **Option A: Azure CLI Authentication (Recommended for Development)**
    
    a. **Login to Azure CLI**:
       ```bash
       az login
       ```
       This provides automatic authentication to Azure DevOps organizations. No additional environment variables required.
    
    b. **Multi-tenant Support** (if applicable):
       ```bash
       az login --tenant YOUR_TENANT_ID
       ```
    
    **Option B: Personal Access Token (Required for CI/CD or Production)**
    
    a. **Create Enhanced Personal Access Token**:
       - Navigate to: https://dev.azure.com/YOUR_ORG/_usersSettings/tokens
       - Click "New Token" with the following comprehensive scopes:
         - **Work Items**: Read & Write (for issue tracking)
         - **Build**: Read (for build status monitoring)
         - **Release**: Read & Write (for release management)
         - **Code**: Read (for repository access)
         - **Project and Team**: Read (for organizational structure)
         - **Test Management**: Read (for test plan integration)
       - Set appropriate expiration date (90 days recommended for development)
       - Copy the token value immediately (it won't be shown again)
    
    b. **Configure Environment Variable**:
       Create a `.env` file in your project root:
       ```bash
       # Azure DevOps Authentication
       AZURE_DEVOPS_EXT_PAT=your_personal_access_token_here
       
       # Optional: Specify tenant for multi-tenant scenarios
       AZURE_TENANT_ID=your_tenant_id_here
       ```
    
    **MCP Server Configuration (Required for All Authentication Methods)**
    
    c. **Enhanced MCP Server Configuration**:
       Create or update `.vscode/mcp.json` in your workspace:
       ```json
       {
         "inputs": [
           {
             "id": "ado_org",
             "type": "promptString", 
             "description": "Azure DevOps organization name (e.g. 'contoso')"
           }
         ],
         "servers": {
           "ado": {
             "type": "stdio",
             "command": "npx",
             "args": ["-y", "@azure-devops/mcp", "${input:ado_org}"],
             "env": {
               "AZURE_DEVOPS_EXT_PAT": "${env:AZURE_DEVOPS_EXT_PAT}"
             }
           }
         }
       }
       ```
    
    d. **Verify MCP Server Connection**:
       Test the MCP server connectivity:
       ```bash
       # Test with organization name
       npx -y @azure-devops/mcp YOUR_ORG_NAME
       
       # Should return available tools and connection status
       ```
    
    e. **Tool Discovery and Validation**:
       The MCP server automatically discovers and configures available tools based on your permissions. Essential tool categories include:
       - **Core**: Projects, teams, iterations
       - **Work**: Work item management and queries
       - **Build**: Build definition and execution tracking
       - **Release**: Release pipeline management
       - **Repository**: Code repository access
       - **Search**: Cross-platform search capabilities

---

## Setup Instructions

### Local Development Setup & Execution Guide (VSCode)

This guide outlines the steps to set up and run the **Release Manager** service locally using Visual Studio Code (VSCode). It leverages VSCode's task and launch configurations (`tasks.json` and `launch.json`) to automate environment preparation and service startup.

---

## ⚙️ Project Structure

```
release_manager/
│
├── .vscode/
│   ├── launch.json                                # VSCode launch configuration
│   ├── tasks.json                                 # VSCode task configuration  
│   └── mcp.json                                   # Model Context Protocol server config
├── agents/                                        # Core Agent Implementations
│   ├── agent_factory.py                          # Agent creation and initialization
│   ├── jira_agent/                               # JIRA integration agent
│   ├── azure_devops_agent/                       # Azure DevOps MCP agent
|   ├── devops_agent/                             # Deprecated DevOps database agent
│   ├── visualization_agent/                      # Chart/graph generation agent
│   └── fallback_agent/                           # Error handling and guidance agent
├── orchestrator/                                  # Multi-Agent Orchestration
│   └── agent_orchestrator.py                     # Planning and coordination logic
├── plugins/                                       # Agent Plugin System
│   ├── jira_plugin/                              # JIRA SDK integration
│   ├── devops_plugin/                            # Database DevOps plugin
│   └── notification_plugin/                      # Microsoft Graph notifications
├── azure_mcp/                                    # Azure DevOps MCP Integration
│   ├── azure-devops-mcp/                         # Full TypeScript MCP server implementation
│   │   ├── src/                                  # MCP server source code
│   │   ├── docs/                                 # Documentation and examples
│   │   └── README.md                             # MCP server setup guide
│   ├── client.py                                 # Python MCP client wrapper
│   ├── plugin.py                                 # Azure DevOps agent MCP plugin integration
│   ├── pool_config.py                            # Connection pool configuration
│   ├── internal/                                 # Internal MCP utilities
│   └── tests/                                    # MCP integration tests
├── evaluation/                                    # Comprehensive Testing Framework
│   ├── README.md                                 # Evaluation setup guide
│   ├── static/eval_config.yaml                   # Evaluation configuration
│   └── agents/                                   # Agent-specific test suites
├── frontend/                                      # Web Interface
│   └── index.html                                # Simple query interface
├── static/                                        # Configuration Files
│   ├── release_manager_config.yaml               # Agent and system configuration
│   ├── jql_cheatsheet.md                        # JIRA Query Language reference
│   └── jira_customfield_description.json        # JIRA field mappings
├── models/                                        # Data Models and Settings
│   ├── agents.py                                 # Agent enumeration and types
│   ├── jira_settings.py                         # JIRA connection settings
│   ├── devops_settings.py                       # DevOps MCP configuration
│   └── visualization_settings.py                # Visualization storage settings
├── requirements.txt                              # Python dependencies
├── Dockerfile                                     # Container deployment config
├── app.py                                        # Main application entry point
├── config.py                                     # Application configuration
├── README.md                                     # Solution overview and features
├── SETUP.md                                      # This setup guide
├── DEMO_SCRIPT.md                                # Interactive demonstration guide
└── LICENSE                                       # MIT License
```

## 🚀 Running the Service

### Option 1: Azure Deployment (Recommended for Production)

**Deploy to Azure using the deploy.ps1 script:**

1. **Run the Deployment Script**:
   ```powershell
   ./deploy.ps1
   ```
   This script will:
   - Create necessary Azure resources
   - Deploy container images
   - Configure environment variables and secrets
   - Set up networking and security

   For detailed deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md)

### Option 2: Docker Deployment (Recommended for Development)

**Streamlined container-based deployment with pre-configured services:**

For the best production-ready experience, use Docker execution with VS Code tasks:

1. **Launch Docker Services**:
   - Open VS Code in the workspace root
   - Press `Ctrl+Shift+P` and select `Tasks: Run Task`
   - Choose: `Release Manager: Build and Run in Docker`
   - This will:
     - Build all required Docker images
     - Start Redis container with authentication
     - Launch Session Manager and Release Manager services
     - Configure networking and environment variables

2. **Force Rebuild** (if needed):
   - Use task: `Release Manager: Build and Run Docker Images [FORCE INSTALL]`
   - Clears cache and rebuilds all components

3. **Service Verification**:
   - Session Manager: http://localhost:5000
   - Release Manager: http://localhost:6000
   - Redis: localhost:6379 (internal communication)

For detailed Docker execution guide: [Docker Execution Documentation](../../DOCKER.README.md)

### Option 3: Local Development Setup (Advanced)

**Full debugging capabilities with VS Code integration:**

1. **Environment Preparation**:
   - Ensure all prerequisites are installed
   - Configure `.env` file with all required credentials
   - Verify MCP server connectivity

2. **VS Code Launch Configuration**:
   - Press `Ctrl+Shift+D` (Run and Debug)
   - Select launch configuration:
     ```
     Session Manager: Launch & Attach server
     ```
     Then separately:
     ```
     Release Manager: Launch & Attach server
     ```
   - Click the green **Run** button or press `F5`

3. **Automated Setup Process**:
   The launch task automatically:
   - Creates Python virtual environment (`.venv`)
   - Installs all dependencies from `requirements.txt`
   - Loads environment variables from `.env`
   - Starts background services (Redis, Session Manager)
   - Launches main service with debugging enabled
   - Configures telemetry and monitoring

### Option 4: Manual Setup (Development/Troubleshooting)

**Step-by-step manual configuration:**

1. **Virtual Environment**:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1  # Windows
   # source .venv/bin/activate  # Linux/macOS
   ```

2. **Install Dependencies**:
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Environment Configuration**:
   ```powershell
   # Copy template and configure
   cp .env.template .env
   # Edit .env with your specific values
   ```

4. **Service Startup**:
   ```powershell
   # Start Redis (if not using Docker)
      docker run -d --name redis-container -p 6379:6379 redis
   
   # Start Session Manager (separate terminal)
   cd ../session_manager
   python app.py
   
   # Start Release Manager (main terminal)
   python app.py
   ```

---

## 🧪 Verifying the Setup

After deployment, perform these verification steps:

### 1. **Service Health Checks**
- **Release Manager**: http://localhost:6000/health
- **Session Manager**: http://localhost:5000/health  
- **Redis Connectivity**: Check VS Code terminal for Redis connection logs

### 2. **Agent Functionality Verification**
Test each agent component:

```bash
# Test JIRA Agent connectivity
curl -X POST http://localhost:6000/test-jira \
  -H "Content-Type: application/json" \
  -d '{"test": "connection"}'

# Test DevOps MCP Server
npx -y @azure-devops/mcp YOUR_ORG_NAME

# Test Azure AI Foundry connection (check logs)
```

### 3. **End-to-End Workflow Test**
Using the web interface or API:

1. **Simple Query**: "Show me issues for release 1.0"
2. **Cross-System Query**: "What work items are related to RM-123?"
3. **Visualization Request**: "Chart the progress of release 2.0"

### 4. **Common Success Indicators**
- ✅ No authentication errors in logs
- ✅ MCP tools discovered and available
- ✅ Agent orchestrator initialized successfully
- ✅ Redis message handling working
- ✅ Azure AI Foundry agents responding

### 5. **Log Monitoring**
Monitor VS Code Debug Console and terminal for:
- Agent initialization confirmations
- MCP server connection status
- Tool discovery and registration
- Query processing workflows

---

## 📄 Stopping the Service

### Docker Deployment:
```powershell
# Stop all services
docker-compose down

# Or stop specific containers
docker stop release_manager session_manager redis
```

### VS Code Development:
1. Press `Ctrl+C` in the terminal
2. Click **Stop** button in Debug panel  
3. Terminate any background processes if needed

---

## 📝 Configuration Notes

### Environment Variables (.env):
```bash
# Core Azure Services
AZURE_OPENAI_ENDPOINT=your_endpoint_here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4o

# Azure AI Foundry
AZURE_AI_AGENT_ENDPOINT=your_agent_endpoint_here
AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME=gpt-4o

# JIRA Configuration
JIRA_SERVER_ENDPOINT=https://your-company.atlassian.net
JIRA_SERVER_USERNAME=your_username
JIRA_SERVER_PASSWORD=your_api_token

# Azure DevOps (choose one method)
AZURE_DEVOPS_ORG_NAME=your_org_name
AZURE_DEVOPS_EXT_PAT=your_pat_token  # If not using Azure CLI

# Storage and Monitoring
STORAGE_ACCOUNT_NAME=your_storage_account
VISUALIZATION_DATA_CONTAINER=visualizations
APPLICATION_INSIGHTS_CNX_STR=your_app_insights_connection

# Security (Production)
KEYVAULT_URI=https://your-keyvault.vault.azure.net/
```

### Agent Configuration (release_manager_config.yaml):
- **System Config**: Application name and global settings
- **Service Configs**: LLM service endpoints and deployment names
- **Agent Configs**: Individual agent prompts and behaviors
- **Orchestration Plans**: Multi-agent workflow definitions

---

## 📂 Related Files

* `.vscode/launch.json`: Contains the main launch configuration.
* `.vscode/tasks.json`: Contains all prerequisite tasks and automation scripts.

---

## Troubleshooting

### **JIRA Agent Issues**
- **Connection Problems**: 
  - Verify JIRA endpoint accessibility: `curl -I https://your-jira.atlassian.net`
  - Check username and API token validity
  - Ensure IP allowlisting if using Jira Cloud
- **Custom Fields**: 
  - Verify custom field IDs in `jira_customfield_description.json`
  - Test JQL queries in JIRA web interface first
  - Check field permissions and project visibility
- **Authentication Errors**: 
  - For Jira Cloud: Use email + API token, not username + password
  - For Jira Server: Verify basic authentication is enabled
  - Test authentication: `curl -u email:token https://your-jira.atlassian.net/rest/api/2/myself`

### **Azure DevOps Agent Issues**
- **Enhanced Authentication Troubleshooting**:
  - **Azure CLI Method**: 
    - Verify login: `az account show`
    - Check organization access: `az devops project list --org https://dev.azure.com/YOUR_ORG`
    - For multi-tenant: Use `az login --tenant TENANT_ID`
    - Refresh token: `az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798`
  - **PAT Method**: 
    - Verify PAT is not expired (check expiration date in Azure DevOps)
    - Enhanced PAT scopes required:
      - Work Items: Read & Write
      - Build: Read 
      - Release: Read & Write
      - Code: Read
      - Project and Team: Read
      - Test Management: Read (optional)
    - Test PAT comprehensively: 
      ```bash
      # Test basic connectivity
      curl -u :YOUR_PAT https://dev.azure.com/YOUR_ORG/_apis/projects
      # Test work item access
      curl -u :YOUR_PAT https://dev.azure.com/YOUR_ORG/_apis/wit/workitems?ids=1
      ```
- **Enhanced MCP Server Troubleshooting**:
  - **Installation Problems**: 
    - Ensure Node.js 20+ is installed: `node --version`
    - Clear npm cache: `npm cache clean --force`
    - Global vs local installation: `npm list -g @azure-devops/mcp`
    - Reinstall: `npm uninstall -g @azure-devops/mcp && npm install -g @azure-devops/mcp`
  - **Advanced Connection Testing**: 
    - Direct server test: `npx -y @azure-devops/mcp YOUR_ORG_NAME --verbose`
    - Check VS Code MCP server logs in output panel
    - Monitor MCP server process: Task Manager → Node.js processes
    - Test tool discovery: Should show 50+ available tools
  - **Tool Discovery and Registration Issues**: 
    - Verify organization name is exact match (case-sensitive)
    - Check user permissions in Azure DevOps (Project Collection Valid Users minimum)
    - Monitor MCP server startup logs for tool registration messages
    - Essential tool categories should include: Core, Work, Build, Release, Repository
  - **Network and Firewall Issues**:
    - Corporate firewall blocking npm/node processes
    - Proxy settings for npm: `npm config list`
    - DNS resolution for dev.azure.com
- **Multi-tenant Enhanced Support**: 
  - Specify tenant in mcp.json environment variables
  - Use AZURE_TENANT_ID environment variable consistently
  - Verify user account tenant membership and permissions
  - Test tenant-specific authentication: `az login --tenant TENANT_ID --allow-no-subscriptions`

### **Visualization Agent Issues**
- **Azure AI Foundry Connection**: 
  - Verify endpoint and deployment name in configuration
  - Check Azure AI Foundry project exists and is accessible
  - Ensure code interpreter tool is enabled in project
  - Test connection: Check agent initialization logs
- **Chart Generation Problems**: 
  - Monitor code interpreter execution logs
  - Verify data format is compatible with visualization libraries
  - Check Azure Storage account for generated artifacts

**Quick Diagnostic Commands:**
```bash
# Test Azure CLI authentication
az account show

# Test Azure DevOps connectivity
az devops project list --org https://dev.azure.com/YOUR_ORG

# Test MCP server installation
npx -y @azure-devops/mcp YOUR_ORG --help

# Test JIRA connectivity
curl -u username:token https://your-jira.atlassian.net/rest/api/2/serverInfo

# Check Python dependencies
pip check

# Verify Docker services
docker ps
docker logs redis-container
```

---

Release Manager should be up and running 🚀
