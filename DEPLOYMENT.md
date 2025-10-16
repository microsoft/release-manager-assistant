# Release Manager Assistant - Azure Deployment Guide

This guide walks you through deploying the Release Manager Assistant to Azure using Azure Developer CLI (azd).

## 📑 Table of Contents
- [🚀 Quick Start](#-quick-start)
   - [Option 1: Using Deployment Scripts](#option-1-using-deployps1-script-windows-or-deploysh-script-linuxmacos)
   - [Option 2: Using azd Commands Directly](#option-2-using-azd-commands-directly)
- [📋 Prerequisites](#-prerequisites)
   - [Required Tools](#required-tools)
   - [Azure Requirements](#azure-requirements)
- [🔧 Pre-Deployment Configuration](#-pre-deployment-configuration)
   - [Environment Setup](#1-environment-setup)
   - [Azure Login](#2-azure-login)
   - [Choose Azure Region](#3-choose-azure-region)
- [🚀 Deployment Steps](#-deployment-steps)
   - [Option 1: Using Deployment Scripts (Recommended)](#option-1-using-deployment-scripts-recommended)
   - [Option 2: Manual Deployment Steps](#option-2-manual-deployment-steps)
   - [Monitor Deployment](#step-3-monitor-deployment)
   - [Verify Deployment](#step-4-verify-deployment)
- [🌐 Access Your Application](#-access-your-application)
- [⚙️ Post-Deployment Configuration](#️-post-deployment-configuration)
   - [Verify BYOAI Configuration](#1-verify-byoai-configuration)
   - [Configure External Integrations](#2-configure-external-integrations)
   - [Frontend Configuration](#3-frontend-configuration)
   - [Test the Application](#4-test-the-application)
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

## 🚀 Quick Start

### Option 1: Using deploy.ps1 Script (Windows) or deploy.sh Script (Linux/macOS)

The easiest way to deploy the Release Manager Assistant is to use the included deployment script:

**For Windows (PowerShell):**
```powershell
# Clone and navigate to the project
cd release_manager

# Run the deployment script
./deploy.ps1
```

**For Linux/macOS (Bash):**
```bash
# Clone and navigate to the project
cd release_manager

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

### Option 2: Using azd Commands Directly

If you prefer more control over the deployment process:

```bash
# Clone and navigate to the project
cd release_manager

# Initialize azd (if not already done)
azd init

# Deploy to Azure
azd up
```

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

3. **Node.js 18+ and npm**
   - Download from [nodejs.org](https://nodejs.org/)
   - Or use package managers: `winget install OpenJS.NodeJS`

4. **Python 3.11+**
   - Download from [python.org](https://python.org/)
   - Or use package managers: `winget install Python.Python.3.11`

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

### Option 1: Using Deployment Scripts (Recommended)

**For Windows (PowerShell):**
```powershell
# Navigate to the project directory
cd path/to/release_manager

# Run the deployment script
./deploy.ps1
```

**For Linux/macOS (Bash):**
```bash
# Navigate to the project directory
cd path/to/release_manager

# Make the script executable and run it
chmod +x deploy.sh
./deploy.sh
```

The PowerShell script will:
1. Check prerequisites and validate environment
2. Create `.env` file if it doesn't exist (prompting for edits)
3. Initialize Azure Developer CLI
4. Deploy infrastructure with proper BYOAI settings
5. Handle container image deployment with retry logic
6. Configure all services with appropriate settings

The Bash script provides equivalent functionality for Linux/macOS users with streamlined deployment process.

### Option 2: Manual Deployment Steps

#### Step 1: Initialize Azure Developer CLI

```bash
# Navigate to the project directory
cd path/to/release_manager

# Initialize azd (if not already initialized)
azd init
```

#### Step 2: Deploy Infrastructure and Application

```bash
# Deploy everything with a single command
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
```

### Step 3: Monitor Deployment

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

### Step 4: Verify Deployment

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

When using your own AI models (BYOAI mode), ensure your configuration is properly connected:

```bash
# Check configuration in Key Vault
az keyvault secret show --vault-name kv-<env-name> --name azure-ai-foundry-project-name

# Verify orchestrator configuration
az containerapp show --name orchestrator --resource-group rg-<env-name> --query configuration.ingress.targetPort
```

The application relies on your pre-configured AI models:
- Chat completion model (e.g., `gpt-4o`)
- Embeddings model (e.g., `text-embedding-ada-002`)

### 2. Configure External Integrations

#### JIRA Integration (Optional)

The solution uses a plugin for Jira Servers or an MCP Server with synthetic data in case a Jira server is not available. Configuration can be done via environment variables:

> ⚠️ **Warning:** Ensure `USE_JIRA_MCP_SERVER` is set to `true` if MCP Server use is desired. `JIRA_SERVER_ENDPOINT`,  `JIRA_SERVER_USERNAME` and `JIRA_SERVER_PASSWORD` are optional in that case and will be ignored.

1. **Configure in `.env` file:**
   ```bash
   USE_JIRA_MCP_SERVER=true
   JIRA_SERVER_ENDPOINT=https://your-org.atlassian.net
   JIRA_SERVER_USERNAME=your-email@domain.com
   JIRA_SERVER_PASSWORD=your-api-token
   ```

2. **Or update Key Vault after deployment:**
   ```bash
   # Set JIRA credentials in Key Vault
   az keyvault secret set --vault-name <keyvault-name> --name "jira-username" --value "your-email@domain.com"
   az keyvault secret set --vault-name <keyvault-name> --name "jira-password" --value "your-api-token"
   az keyvault secret set --vault-name <keyvault-name> --name "jira-endpoint" --value "https://your-org.atlassian.net"
   ```

#### Azure DevOps Integration (Optional)

The solution uses official Azure DevOps MCP Server if required settings are provided. It falls back to using an MCP Server with synthetic data if needed. Configuration can be done via environment variables:

> ⚠️ **Warning:** Ensure `USE_AZURE_DEVOPS_MCP_SERVER` is set to `true` if MCP Server use is desired. `AZURE_DEVOPS_ORG_NAME` and `AZURE_DEVOPS_EXT_PAT` are optional in that case and will be ignored.

1. **Create Personal Access Token:**
   - Go to Azure DevOps → User Settings → Personal Access Tokens
   - Create token with `Work Items (Read & Write)` and `Code (Read)` permissions

2. **Update Key Vault:**
   ```bash
   # Set Azure DevOps credentials
   az keyvault secret set --vault-name <keyvault-name> --name "azure-devops-org" --value "your-org-name"
   az keyvault secret set --vault-name <keyvault-name> --name "azure-devops-pat" --value "your-pat-token"
   ```

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

# Remove with confirmation
azd down --force
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