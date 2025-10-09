# Release Manager Assistant - Azure Deployment Guide

This guide walks you through deploying the Release Manager Assistant to Azure using Azure Developer CLI (azd).

## 🚀 Quick Start

### Option 1: Using deploy.ps1 Script (Recommended)

The easiest way to deploy the Release Manager Assistant is to use the included PowerShell deployment script:

```powershell
# Clone and navigate to the project
cd release_manager

# Run the deployment script
./deploy.ps1
```

This script handles the entire deployment process including:
- Environment setup and validation
- Azure infrastructure provisioning
- Building and pushing container images
- Deploying all services with automatic retries for resilience
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
   AZURE_AI_FOUNDRY_RESOURCE_NAME=your-ai-resource-name
   AZURE_AI_FOUNDRY_PROJECT_NAME=your-project-name
   AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4o
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=gpt-4o
   AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=text-embedding-ada-002
   AZURE_CONTENT_SAFETY_RESOURCE_NAME=your-content-safety-resource
   
   # Optional - External integrations
   JIRA_SERVER_ENDPOINT=https://your-org.atlassian.net
   JIRA_SERVER_USERNAME=your-email@domain.com
   JIRA_SERVER_PASSWORD=your-api-token
   
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
# Check if Container Apps is available
az provider show --namespace Microsoft.App --query "registrationState"

# Check if Azure AI services are available
az cognitiveservices account list-skus --location eastus2
```

## 🚀 Deployment Steps

### Option 1: Using deploy.ps1 Script (Recommended)

```powershell
# Navigate to the project directory
cd path/to/release_manager

# Run the deployment script
./deploy.ps1
```

This script will:
1. Check prerequisites and validate environment
2. Create `.env` file if it doesn't exist (prompting for edits)
3. Initialize Azure Developer CLI
4. Deploy infrastructure with proper BYOAI settings
5. Handle container image deployment with retry logic
6. Configure all services with appropriate settings

### Option 2: Manual Deployment Steps

#### Step 1: Initialize Azure Developer CLI

```bash
# Navigate to the project directory
cd path/to/release_manager

# Initialize azd (if not already initialized)
azd init

# The project already has azure.yaml, so this will detect it automatically
```

#### Step 2: Deploy Infrastructure and Application

```bash
# Deploy everything with a single command
azd up

# This command will:
# 1. Build the frontend application
# 2. Provision Azure infrastructure
# 3. Deploy all services
# 4. Configure networking and security
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
   - Container Apps deployment
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
- **URL**: `https://<random-name>.azurestaticapps.net`
- **Purpose**: React-based user interface

### API Endpoints
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

1. **[Optional] Get JIRA API Token:**
   - Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
   - Create API token
   - Use your email as username, token as password

2. **Update Key Vault:**
   ```bash
   # Set JIRA credentials in Key Vault
   az keyvault secret set --vault-name <keyvault-name> --name "jira-username" --value "your-email@domain.com"
   az keyvault secret set --vault-name <keyvault-name> --name "jira-password" --value "your-api-token"
   az keyvault secret set --vault-name <keyvault-name> --name "jira-endpoint" --value "https://your-org.atlassian.net"
   ```

#### Azure DevOps Integration (Optional)

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

- **Session Manager**: `https://<session-manager-url>/health`
- **Orchestrator**: `https://<orchestrator-url>/health`
- **Frontend**: Automatically monitored by Static Web Apps

## 🔄 Managing Your Deployment

### Update Application

```bash
# Update using deploy.ps1 (recommended for reliability)
./deploy.ps1

# Or update with azd commands
azd deploy

# Update only specific service
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

## 💰 Cost Optimization

### Typical Monthly Costs (East US 2)

- **Container Apps**: $20-50/month (depends on usage)
- **Azure AI**: $10-100/month (depends on API calls)
- **Static Web Apps**: $0-10/month (free tier available)
- **Storage Account**: $1-5/month
- **Key Vault**: $0-5/month
- **Application Insights**: $0-20/month

### Cost Reduction Tips

1. **Use free tiers** where available
2. **Scale Container Apps to zero** during non-business hours
3. **Monitor AI API usage** and set budgets
4. **Use cheaper regions** if latency allows

## 🔐 Security Best Practices

1. **Key Vault**: All secrets stored securely
2. **Managed Identity**: No hardcoded credentials
3. **Network Security**: Container Apps use internal networking
4. **HTTPS**: All endpoints use SSL/TLS
5. **Content Safety**: Built-in content filtering

## 📞 Support

- **Azure Developer CLI**: [GitHub Issues](https://github.com/Azure/azure-dev/issues)
- **Azure Documentation**: [docs.microsoft.com](https://docs.microsoft.com/azure)
- **Container Apps**: [Container Apps Documentation](https://docs.microsoft.com/azure/container-apps)

---

## Quick Reference Commands

```powershell
# Full deployment (recommended)
./deploy.ps1

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