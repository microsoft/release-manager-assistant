# Release Manager Assistant - Azure Deployment Guide

This guide walks you through deploying the Release Manager Assistant to Azure using Azure Developer CLI (azd).

## 📑 Table of Contents

- [📋 Prerequisites](#-prerequisites)
  - [Required Tools](#required-tools)
  - [Azure Requirements](#azure-requirements)
- [🔧 Pre-Deployment Configuration](#-pre-deployment-configuration)
  - [1. Environment Setup](#1-environment-setup)
  - [2. Azure Login](#2-azure-login)
  - [3. Choose Azure Region](#3-choose-azure-region)
- [🚀 Deployment Steps](#-deployment-steps)
  - [Step 1: Quick Deploy](#step-1-quick-deploy)
    - [Option 1: Using deploy.ps1 Script (Windows) or deploy.sh Script (Linux/macOS)](#option-1-using-deployps1-script-windows-or-deploysh-script-linuxmacos)
    - [Option 2: Using azd Commands Directly](#option-2-using-azd-commands-directly)
  - [Step 2: Monitor Deployment](#step-2-monitor-deployment)
  - [Step 3: Verify Deployment](#step-3-verify-deployment)
- [🌐 Access Your Application](#-access-your-application)
- [⚙️ Post-Deployment Configuration](#-post-deployment-configuration)
  - [1. Verify BYOAI Configuration](#1-verify-byoai-configuration)
  - [2. Configure External Integrations](#2-configure-external-integrations)
  - [3. Frontend Configuration](#3-frontend-configuration)
  - [4. Test the Application](#4-test-the-application)
- [🔍 Monitoring and Troubleshooting](#-monitoring-and-troubleshooting)
  - [View Logs](#view-logs)
  - [Common Issues and Solutions](#common-issues-and-solutions)
  - [Health Checks](#health-checks)
- [🔄 Managing Your Deployment](#-managing-your-deployment)
  - [Update Application](#update-application)
  - [Environment Management](#environment-management)
  - [Clean Up Resources](#clean-up-resources)
- [📞 Documentation](#-documentation)
- [Quick Reference Commands](#quick-reference-commands)

---

## 📋 Prerequisites

### Required Tools

1. **Azure Developer CLI (azd)**

   ```bash
   # Windows (PowerShell)
   winget install microsoft.azd

   # macOS
   brew tap azure/azd && brew install azd

   # Linux
   curl -fsSL https://aka.ms/install-azd.sh | bash
   ```

2. **Azure CLI**

   ```bash
   # Windows
   winget install Microsoft.AzureCLI

   # macOS
   brew install azure-cli

   # Linux
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```

3. **Node.js 20+ and npm**
   - Download from [nodejs.org](https://nodejs.org/)
   - Or use package managers:
     - **Windows**: `winget install OpenJS.NodeJS --version 20.18.0` (or latest 20.x)
     - **Linux (Ubuntu/Debian)**: `curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt-get install -y nodejs`
     - **macOS**: `brew install node@20`

4. **Python 3.12+**
   - Download from [python.org](https://python.org/)
   - Or use package managers:
     - **Windows**: `winget install Python.Python.3.12`
     - **Linux (Ubuntu/Debian)**: `sudo apt update && sudo apt install python3.12 python3-pip`
     - **macOS**: `brew install python@3.12`

### Azure Requirements

- **Azure Subscription** with the following permissions:
  - Contributor role on the subscription
  - Ability to create resource groups
  - Ability to create and assign managed identities

- **Required Azure Resource Providers** (auto-registered during deployment):
  - Microsoft.App (Container Apps)
  - Microsoft.CognitiveServices (Azure AI)
  - Microsoft.Web (Static Web Apps)
  - Microsoft.KeyVault
  - Microsoft.Storage
  - Microsoft.Insights

## 🔧 Pre-Deployment Configuration

### 1. Environment Setup

1. **Copy the environment template:**

   ```bash
   cp .env.template .env
   ```

   > **Note:** When using the `deploy.ps1` script, it will automatically create a `.env` file from the template if one doesn't exist and prompt you to edit it.

2. **Configure required variables in `.env`:**

   ```bash
   # Required - Choose your deployment settings
   AZURE_ENV_NAME=myreleasemgr           # Unique name for your environment
   AZURE_LOCATION=eastus2                # Azure region
   AZURE_SUBSCRIPTION_ID=your-sub-id     # Your Azure subscription ID

   # BYOAI - Bring Your Own AI resources (Required)
   AZURE_AI_FOUNDRY_RESOURCE_GROUP=your-ai-resource-group
   AZURE_AI_FOUNDRY_RESOURCE_NAME=your-ai-resource-name
   AZURE_AI_FOUNDRY_PROJECT_NAME=your-project-name
   AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4o

   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=gpt-4o
   AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=text-embedding-ada-002

   AZURE_CONTENT_SAFETY_RESOURCE_NAME=your-content-safety-resource

   # External integrations (Optional)
   USE_JIRA_MCP_SERVER=true              # Enable JIRA MCP server integration
   JIRA_SERVER_ENDPOINT=https://your-org.atlassian.net
   JIRA_SERVER_USERNAME=your-email@domain.com
   JIRA_SERVER_PASSWORD=your-api-token

   USE_AZURE_DEVOPS_MCP_SERVER=true
   AZURE_DEVOPS_ORG_NAME=your-org
   AZURE_DEVOPS_EXT_PAT=your-personal-access-token
   ```

> ⚠️ **IMPORTANT:** Due to Azure capacity constraints, you must provide a valid Azure AI Foundry project and Azure OpenAI resource for deployment to succeed.

### 2. Azure Login

```bash
# Login to Azure
az login

# Set your subscription (if you have multiple)
az account set --subscription "your-subscription-id"

# Verify your login
az account show
```

### 3. Choose Azure Region

Select a region that supports all required services:

**Recommended regions:**

- `eastus2` (Default)
- `westus2`
- `centralus`
- `westeurope`
- `eastasia`

**Verify region capabilities:**

```bash
# Check if the Azure resource provider Container Apps is registered in your subscription.
# Output: "registered" | "unregistered"
az provider show --namespace Microsoft.App --query "registrationState"

# Check if Azure AI services are available (ContentSafety)
az cognitiveservices account list-skus --location eastus2
```

> **Important:** Ensure the Microsoft.App resource provider is registered in your subscription. If it's not registered, the Container Apps deployment will fail.

## 🚀 Deployment Steps

### Step 1: Quick Deploy

#### Option 1: Using deploy.ps1 Script (Windows) or deploy.sh Script (Linux/macOS)

The easiest way to deploy the Release Manager Assistant is to use the included deployment script:

**For Windows (PowerShell):**

```powershell
# Clone and navigate to the project
cd scripts/

# Run the deployment script
./deploy.ps1
```

**For Linux/macOS (Bash):**

```bash
# Clone and navigate to the project
cd scripts/

# Make the script executable and run it
chmod +x deploy.sh
./deploy.sh
```

These scripts handle the entire deployment process including:

- Environment setup and validation
- Azure infrastructure provisioning
- Building and pushing container images
- Deploying all services with automatic retries for resilience (PowerShell script)
- Setting up secrets and configurations

#### Option 2: Using azd Commands Directly

If you prefer more control over the deployment process:

```bash
# 1. Set environment variables
# Make sure all required environment variables are loaded before deployment. (see `env.template` for required variables)

# 2. Deploy to Azure
azd up

# This command will:
# 1. Build the frontend application
# 2. Provision Azure infrastructure
# 3. Deploy all services:
#    - MCP Server (Model Context Protocol server for JIRA and Azure DevOps)
#    - Orchestrator (Main AI orchestration service)
#    - Session Manager (WebSocket and session management)
#    - Frontend (React-based user interface)
# 4. Configure networking and security
```

### Step 2: Monitor Deployment

The deployment process will show progress for:

1. **Infrastructure Provisioning** (~5-10 minutes)
   - Resource Group
   - Container Apps Environment
   - Azure AI Foundry with models
   - Key Vault
   - Storage Account
   - Static Web App

2. **Application Deployment** (~3-5 minutes)
   - Frontend build and upload
   - MCP Server deployment (JIRA and Azure DevOps with synthetic data)
   - Orchestrator deployment (AI orchestration service)
   - Session Manager deployment (WebSocket management)
   - Redis container deployment

### Step 3: Verify Deployment

```bash
# Check deployment status
azd show

# Get service endpoints
azd show --output json
```

## 🌐 Access Your Application

After successful deployment, you'll receive:

### Frontend Application

- **URL**: `https://<app-name>.azurestaticapps.net`
- **Purpose**: React-based user interface

### API Endpoints

- **MCP Server**: `https://<mcp-server>.azurecontainerapps.io`
- **Session Manager**: `https://<session-manager>.azurecontainerapps.io`
- **Orchestrator**: `https://<orchestrator>.azurecontainerapps.io`

### Azure Resources

- **Resource Group**: `rg-release-manager-assistant-<env-name>`
- **Azure Portal**: Access via [portal.azure.com](https://portal.azure.com)

## ⚙️ Post-Deployment Configuration

### 1. Verify BYOAI Configuration

> ⚠️ **WARNING:** If model deployments are missing, the solution will not work. Ensure models are deployed with sufficient quota and rate limits in place.

When using your own AI models (BYOAI mode), ensure your configuration is properly connected and role assignment (`Azure AI User`) is in place:

```bash
# Verify that both Session Manager and Orchestrator have "Azure AI User" role on your AI Foundry Project

# 1. Get the system-assigned managed identity IDs
ORCHESTRATOR_IDENTITY=$(az containerapp show --name orchestrator --resource-group rg-<env-name> --query identity.principalId -o tsv)
SESSION_MANAGER_IDENTITY=$(az containerapp show --name session-manager --resource-group rg-<env-name> --query identity.principalId -o tsv)

# 2. Check role assignments on your AI Foundry Project (replace with your actual resource group and project name)
az role assignment list --assignee $ORCHESTRATOR_IDENTITY --scope "/subscriptions/<subscription-id>/resourceGroups/<ai-resource-group>/providers/Microsoft.CognitiveServices/accounts/<ai-account-name>/projects/<ai-project-name>" --role "Azure AI User"
az role assignment list --assignee $SESSION_MANAGER_IDENTITY --scope "/subscriptions/<subscription-id>/resourceGroups/<ai-resource-group>/providers/Microsoft.CognitiveServices/accounts/<ai-account-name>/projects/<ai-project-name>" --role "Azure AI User"
```

The application relies on your pre-configured AI models:

- Chat completion model (e.g., `gpt-4o`)
- Embeddings model (e.g., `text-embedding-ada-002`)

> ⚠️ **IMPORTANT:** You may swap the models mentioned above with others from the same supported family, such as using `gpt-4.1` instead of `gpt-4o`, and `text-embedding-3-large` instead of `text-embedding-ada-002`. Supported model families include GPT-4 (e.g., `gpt-4o`, `gpt-4.1`) for chat completion and Text Embedding (e.g., `text-embedding-ada-002`, `text-embedding-3-large`) for embeddings. While these models are generally compatible, minor differences in output quality, latency, or cost may occur; in most practical scenarios, swapping within the same family will not noticeably impact solution performance or user experience.

### 2. Configure External Integrations

#### JIRA Integration (Optional)

The solution uses a plugin for Jira Servers or an MCP Server with synthetic data in case a Jira server is not available. Configuration can be done via environment variables:

> ⚠️ **Warning:**
> - If `USE_JIRA_MCP_SERVER` is set to `true`, the MCP Server will be used for JIRA integration and the values of `JIRA_SERVER_ENDPOINT`, `JIRA_SERVER_USERNAME`, and `JIRA_SERVER_PASSWORD` are optional and will be ignored.
> - If `USE_JIRA_MCP_SERVER` is set to `false`, you must provide valid values for `JIRA_SERVER_ENDPOINT`, `JIRA_SERVER_USERNAME`, and `JIRA_SERVER_PASSWORD` to enable direct JIRA server integration.

- Configure in `.env` file:

   ```bash
   USE_JIRA_MCP_SERVER=true
   JIRA_SERVER_ENDPOINT=https://your-org.atlassian.net
   JIRA_SERVER_USERNAME=your-email@domain.com
   JIRA_SERVER_PASSWORD=your-api-token
   ```

#### Azure DevOps Integration (Optional)

The solution uses official Azure DevOps MCP Server if required settings are provided. It falls back to using an MCP Server with synthetic data if needed. Configuration can be done via environment variables:

> ⚠️ **Warning:**
> - If `USE_AZURE_DEVOPS_MCP_SERVER` is set to `true`, the MCP Server will be used for Azure DevOps integration and the values of `AZURE_DEVOPS_ORG_NAME` and `AZURE_DEVOPS_EXT_PAT` are optional and will be ignored.
> - If `USE_AZURE_DEVOPS_MCP_SERVER` is set to `false`, you must provide valid values for `AZURE_DEVOPS_ORG_NAME` and `AZURE_DEVOPS_EXT_PAT` to enable direct Azure DevOps integration.

1. **Create Personal Access Token:**
   - Go to Azure DevOps → User Settings → Personal Access Tokens
   - Create token with the following scopes:
     - `Work Items (Read & Write)`
     - `Code (Read)`
     - `Release (Read)`
     - `Project and Team (Read)`

2. **Configure in `.env` file:**

   ```bash
   USE_AZURE_DEVOPS_MCP_SERVER=true
   AZURE_DEVOPS_ORG_NAME=ContosoAzureDevopsOrg
   AZURE_DEVOPS_EXT_PAT=<my-PAT-token>
   ```

> You can see instructions on how to create PAT tokens in the [Azure DevOps Personal Access Token documentation](https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops)

### 3. Frontend Configuration

The frontend application needs to know the Session Manager URL to establish WebSocket connections. This is automatically configured during deployment:

```bash
# Check the configured Session Manager URL
azd env get-values | grep SESSION_MANAGER_URL

# Manually set the Session Manager URL if needed
azd env set VITE_SESSION_MANAGER_URL=https://your-session-manager-url
```

The deployment process:

1. Gets the Session Manager URL from the environment
2. Sets it as an environment variable for the frontend build
3. Configures it in the Static Web App settings
4. Updates the basic HTML frontend with the correct WebSocket URL

### 4. Test the Application

1. **Access the frontend** at the provided URL
2. **Create a test session** to verify backend connectivity
3. **Check logs** in Application Insights for any issues

## 🔍 Monitoring and Troubleshooting

### View Logs

```bash
# Stream live logs
azd monitor --live

# View logs in Azure Portal
azd monitor
```

### Common Issues and Solutions

#### 1. Deployment Fails - Resource Provider Not Registered

```bash
# Register required providers
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.CognitiveServices
az provider register --namespace Microsoft.Web
az provider register --namespace Microsoft.KeyVault
az provider register --namespace Microsoft.Storage
```

#### 2. Container Apps Deployment Failures

If Container Apps deployment fails during the initial deployment, try using the `deploy.ps1` script which includes automatic retry logic:

```powershell
./deploy.ps1
```

The script will detect failures and retry deployments with increasing backoff intervals.

You can also check container logs:

```bash
# Check container logs
az containerapp logs show --name mcp-server --resource-group <rg-name>
az containerapp logs show --name session-manager --resource-group <rg-name>
az containerapp logs show --name orchestrator --resource-group <rg-name>
```

#### 3. Frontend WebSocket Connection Issues

If the frontend cannot connect to the Session Manager service:

```bash
# Verify the Session Manager URL in environment
azd env get-values | grep SESSION_MANAGER_URL

# Check the frontend environment settings
az staticwebapp appsettings show --name <staticwebapp-name> --resource-group <rg-name>

# Redeploy the frontend with correct Session Manager URL
azd deploy frontend --force
```

#### 4. Frontend Build Fails

```bash
# Manual frontend build
cd src/frontend/react-app
npm install
npm run build
```

#### 4. AI Models Not Available

```bash
# Check AI service status
az cognitiveservices account show --name <ai-account> --resource-group <rg-name>

# Redeploy models if needed
azd deploy
```

### Health Checks

All services include health check endpoints:

- **MCP Server**: `https://<mcp-server-url>/health`
- **Session Manager**: `https://<session-manager-url>/health`
- **Orchestrator**: `https://<orchestrator-url>/health`
- **Frontend**: Automatically monitored by Static Web Apps

## 🔄 Managing Your Deployment

### Update Application

```bash
# Update using deployment scripts (recommended for reliability)
# Windows
./deploy.ps1

# Linux/macOS
./deploy.sh

# Or update with azd commands
azd deploy

# Update only specific service
azd deploy mcp-server
azd deploy session-manager
azd deploy orchestrator
azd deploy frontend
```

### Environment Management

```bash
# Create additional environments
azd env new production
azd env select production
azd up

# List environments
azd env list

# Switch environments
azd env select development
```

### Clean Up Resources

```bash
# Remove all Azure resources
azd down

# Remove and purge all resources for permanent deletions (recommended)
azd down --force --purge
```

## 📞 Documentation

- **Azure Developer CLI**: [GitHub Issues](https://github.com/Azure/azure-dev/issues)
- **Azure Documentation**: [docs.microsoft.com](https://docs.microsoft.com/azure)
- **Container Apps**: [Container Apps Documentation](https://docs.microsoft.com/azure/container-apps)

---

## Quick Reference Commands

```bash
# Full deployment (recommended)
# Windows
./deploy.ps1

# Linux/macOS
./deploy.sh

# Alternative deployment
azd up

# Update application only
azd deploy

# View deployment info
azd show

# Monitor logs
azd monitor --live

# Clean up
azd down --force --purge
```

Happy deploying! 🚀
