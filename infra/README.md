# Release Manager Assistant

- **Key Vault** - Secure storage for secrets and configuration
- **Storage Account** - Storage for visualizations and data
- **Application Insights** - Monitoring and telemetry
- **Log Analytics Workspace** - Centralized logging
- **Content Safety** - Azure AI Content Safety service
- **AI Foundry** - Azure AI Foundry account with Release Manager Assistant project and pre-deployed models (GPT-4o, text-embedding-3-large) - Azure Deployment

This document describes how to deploy the Release Manager Assistant to Azure using the Azure Developer CLI (azd).

## Architecture Overview

The Release Manager Assistant consists of three main components:

1. **Frontend** - React.js application deployed as an Azure Static Web App
2. **Session Manager** - Python/Quart service for WebSocket communication, deployed as a Container App
3. **Orchestrator** - Python/aiohttp service for agent orchestration, deployed as a Container App

### Azure Resources

The deployment creates the following Azure resources:

- **Resource Group** - Contains all resources
- **Container Apps Environment** - Hosts the backend services and Redis
- **Container Apps** - Session Manager, Orchestrator, and Redis services
- **Static Web App** - Frontend application
- **Redis Container** - Message queuing between services (containerized)
- **Key Vault** - Secure storage for secrets and configuration
- **Storage Account** - Storage for visualizations and data
- **Application Insights** - Monitoring and telemetry
- **Log Analytics Workspace** - Centralized logging
- **Content Safety** - Azure AI Content Safety service
- **Azure AI Foundry** - Azure AI Foundry project for model access

## Prerequisites

1. **Azure CLI** - [Install Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
2. **Azure Developer CLI** - [Install azd](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd)
3. **Docker** - [Install Docker](https://docs.docker.com/get-docker/) (for container builds)
4. **Node.js** - [Install Node.js](https://nodejs.org/) (version 18 or higher)

## Quick Start

### 1. Clone and Navigate to the Project

```bash
cd d:\agent_templates\src\release_manager
```

### 2. Login to Azure

```bash
az login
```

### 3. Configure Environment

Copy the environment template and fill in your values:

```bash
# Windows
copy .env.template .env

# Linux/Mac
cp .env.template .env
```

Edit the `.env` file and provide the following required values:

```env
# Required
AZURE_ENV_NAME=my-release-manager-dev
AZURE_LOCATION=eastus2
AZURE_SUBSCRIPTION_ID=your-subscription-id

# Optional integrations
JIRA_SERVER_ENDPOINT=https://your-company.atlassian.net
JIRA_SERVER_USERNAME=your-jira-username
JIRA_SERVER_PASSWORD=your-jira-password

AZURE_DEVOPS_ORG_NAME=your-devops-org
AZURE_DEVOPS_EXT_PAT=your-devops-pat-token
```

### 4. Deploy

Run the deployment script:

```bash
# Windows
.\deploy.ps1

# Linux/Mac
./deploy.sh
```

Or use azd commands directly:

```bash
# Initialize the environment
azd env new my-release-manager-dev

# Provision and deploy
azd up
```

## Manual Deployment Steps

If you prefer to deploy manually or understand the process better:

### 1. Initialize Environment

```bash
azd env new <environment-name> --location <location> --subscription <subscription-id>
```

### 2. Set Environment Variables

```bash
azd env set AZURE_OPENAI_ENDPOINT "https://your-openai-resource.openai.azure.com/"
azd env set AZURE_OPENAI_API_KEY "your-api-key"
# ... set other variables as needed
```

### 3. Provision Infrastructure

```bash
azd provision
```

### 4. Deploy Applications

```bash
azd deploy
```

## Local Development

For local development with Docker Compose:

### 1. Start Services

```bash
docker-compose up -d
```

This starts:

- Redis on port 6379
- Session Manager on port 5000
- Orchestrator on port 5002
- Frontend on port 3000

### 2. Access the Application

- Frontend: http://localhost:3000
- Session Manager API: http://localhost:5000
- Orchestrator API: http://localhost:5002
- Redis: localhost:6379

### 3. Stop Services

```bash
docker-compose down
```

## Configuration

### Environment Variables

The application uses the following environment variables:

#### Session Manager

- `KEYVAULT-URI` - Azure Key Vault URI
- `APPLICATION-INSIGHTS-CNX-STR` - Application Insights connection string
- `AZURE-CONTENT-SAFETY-SERVICE` - Content Safety service endpoint
- `REDIS-HOST` - Redis hostname
- `REDIS-PORT` - Redis port (default: 6379)
- `REDIS-PASSWORD` - Redis password
- `FOUNDRY-PROJECT-ENDPOINT` - AI Project endpoint

#### Orchestrator

- `KEYVAULT_URI` - Azure Key Vault URI
- `APPLICATION_INSIGHTS_CNX_STR` - Application Insights connection string
- `AZURE_AI_PROJECT_ENDPOINT` - AI Project endpoint
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint
- `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` - Chat model deployment
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME` - Embedding model deployment
- `REDIS-HOST` - Redis hostname
- `REDIS-PORT` - Redis port
- `STORAGE_ACCOUNT_NAME` - Storage account name
- `JIRA_SERVER_ENDPOINT` - JIRA server URL (optional)
- `AZURE_DEVOPS_ORG_NAME` - Azure DevOps organization (optional)

#### Frontend

- `VITE_SESSION_MANAGER_URL` - Session Manager service URL

### Key Vault Secrets

The following secrets are automatically stored in Key Vault:

- `azure-openai-api-key` - Azure OpenAI API key
- `jira-server-username` - JIRA username (if configured)
- `jira-server-password` - JIRA password (if configured)
- `azure-devops-ext-pat` - Azure DevOps PAT (if configured)
- `redis-password` - Redis password
- `storage-account-key` - Storage account access key

## Monitoring and Logging

### Application Insights

All services are configured to send telemetry to Application Insights:

- **Session Manager** - WebSocket connections, request metrics
- **Orchestrator** - Agent execution metrics, AI model usage
- **Frontend** - Client-side errors and performance metrics

### Log Analytics

All container logs are sent to Log Analytics workspace for centralized logging.

### Monitoring Dashboard

Access monitoring through:

```bash
azd monitor
```

Or visit the Application Insights dashboard in the Azure portal.

## Scaling

### Container Apps Scaling

Both backend services are configured with auto-scaling:

- **Session Manager**: 1-10 replicas based on HTTP requests
- **Orchestrator**: 1-5 replicas based on HTTP requests

### Redis Container Scaling

The Redis container runs as a Container App with persistent storage. For production workloads:

- Monitor memory usage and adjust container resource limits
- Consider Redis clustering for high availability (requires custom Redis configuration)
- Use persistent volumes for data durability across container restarts

### Storage Account

The storage account uses Standard_LRS by default. For production, consider:

- Standard_GRS for geo-redundancy
- Premium_LRS for high performance

## Security

### Network Security

- All services use HTTPS/TLS encryption
- Container Apps are accessible only through the managed environment
- Redis cache is accessible only within the virtual network

### Identity and Access

- Container Apps use system-assigned managed identities
- Key Vault access is granted through RBAC
- Storage account access uses managed identity

### Content Safety

Azure AI Content Safety service is integrated to:

- Filter inappropriate text content
- Scan images for inappropriate content
- Configurable through environment variables

## Troubleshooting

### Common Issues

1. **Deployment fails with authentication error**
   - Ensure you're logged in: `az login`
   - Check subscription access: `az account show`

2. **Container Apps fail to start**
   - Check container logs in Azure portal
   - Verify environment variables are set correctly
   - Ensure Key Vault permissions are configured

3. **Frontend can't connect to backend**
   - Check CORS configuration
   - Verify Session Manager URL in frontend environment

4. **Redis connection errors**
   - Check Redis container is running in Container Apps environment
   - Verify Redis container app logs for startup issues
   - Ensure Redis password matches between services
   - Check internal network connectivity within Container Apps environment

### Getting Help

1. **View application logs**:

   ```bash
   azd monitor --live
   ```

2. **Check deployment status**:

   ```bash
   azd show
   ```

3. **View resource details**:

   ```bash
   az resource list --resource-group rg-<environment-name>
   ```

## Cleanup

To remove all Azure resources:

```bash
azd down --force --purge
```

This will delete:

- The resource group and all resources
- The azd environment configuration

## Cost Optimization

### Development Environment

For development environments, consider:

- Using Free tier for Static Web Apps
- Basic tier for Redis Cache (C0)
- Minimal Container Apps resources (0.5 CPU, 1 GB RAM)
- Standard_LRS storage account

### Production Environment

For production environments, consider:

- Standard tier for Static Web Apps
- Standard tier for Redis Cache (C1 or higher)
- Appropriate Container Apps resources based on load
- Geo-redundant storage account
- Premium Key Vault for hardware security modules

## Next Steps

1. **Custom Domain**: Configure custom domains for the Static Web App
2. **CI/CD Pipeline**: Set up GitHub Actions or Azure DevOps pipelines
3. **Monitoring Alerts**: Configure alerts for critical metrics
4. **Backup Strategy**: Implement backup for Redis and storage data
5. **Performance Testing**: Load test the application with realistic workloads
