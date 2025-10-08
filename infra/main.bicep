targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('The image name for the session manager service')
param session_manager_image_name string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('The image name for the orchestrator service')
param orchestrator_image_name string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('JIRA server endpoint')
param jiraServerEndpoint string = ''

@secure()
@description('JIRA server username')
param jiraServerUsername string = ''

@secure()
@description('JIRA server password')
param jiraServerPassword string = ''

@description('Azure DevOps organization name')
param azureDevOpsOrgName string = ''

@secure()
@description('Azure DevOps PAT token')
param azureDevOpsExtPat string = ''

@secure()
@description('Redis password for all services')
param redisPassword string = ''

// BYOAI parameters - Bring Your Own AI resources
@description('Azure AI Foundry Resource ID - if provided, AI Foundry will not be deployed')
param azureAiFoundryResourceId string = ''

@description('Azure AI Foundry Resource Name - if provided, AI Foundry will not be deployed')
param azureAiFoundryResourceName string = ''

@description('Azure AI Foundry Project Name - if provided, AI Foundry will not be deployed')
param azureAiFoundryProjectName string = ''

@description('Azure AI Foundry Model Deployment Name - if provided, AI Foundry will not be deployed')
param azureAiModelDeploymentName string = ''

@description('Azure OpenAI Endpoint - if provided, AI Foundry OpenAI will not be deployed')
param azureOpenAIEndpoint string = ''

@description('Azure OpenAI Responses Deployment Name - if provided, AI Foundry OpenAI will not be deployed')
param azureOpenAIResponsesDeploymentName string = ''

@description('Azure OpenAI Embedding Deployment Name - if provided, AI Foundry OpenAI will not be deployed')
param azureOpenAIEmbeddingDeploymentName string = ''

@description('Azure Content Safety Resource Name - if provided, Content Safety service will not be deployed')
param azureContentSafetyResourceName string = ''

var actualRedisPassword = redisPassword != '' ? redisPassword : uniqueString(subscription().id, environmentName, 'redis-password')

// Determine if the user is bringing their own AI resources
var byoaiEnabled = !empty(azureAiFoundryResourceId) && !empty(azureAiFoundryResourceName) && !empty(azureOpenAIEndpoint) && !empty(azureOpenAIResponsesDeploymentName) && !empty(azureOpenAIEmbeddingDeploymentName)

// Determine if the user is bringing their own Content Safety service
var byoContentSafetyEnabled = !empty(azureContentSafetyResourceName)

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = {
  'azd-env-name': environmentName
}

// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

// Create Application Insights for monitoring
module monitoring './core/monitor/monitoring.bicep' = {
  name: 'monitoring'
  scope: rg
  params: {
    location: location
    tags: tags
    logAnalyticsName: '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    applicationInsightsName: '${abbrs.insightsComponents}${resourceToken}'
  }
}

// Create Key Vault for secrets management
module keyVault './core/security/keyvault.bicep' = {
  name: 'keyvault'
  scope: rg
  params: {
    location: location
    tags: tags
    name: '${abbrs.keyVaultVaults}${resourceToken}'
  }
}

// Create Storage Account for visualizations
module storage './core/storage/storage-account.bicep' = {
  name: 'storage'
  scope: rg
  params: {
    location: location
    tags: tags
    name: '${abbrs.storageStorageAccounts}${resourceToken}'
    // SFI Wave 1 compliant - no shared key access, but allow network access for Container Apps
    defaultAction: 'Allow'
    containers: [
      {
        name: 'visualizations'
        publicAccess: 'None'
      }
    ]
  }
}

// Create Content Safety service if not provided by user
module contentSafety './core/ai/contentsafety.bicep' = if (!byoContentSafetyEnabled) {
  name: 'contentsafety'
  scope: rg
  params: {
    location: location
    tags: tags
    name: '${abbrs.cognitiveServicesAccounts}${resourceToken}-content-safety'
  }
}

var azureContentSafetyResourceNameValue = byoContentSafetyEnabled ? azureContentSafetyResourceName : (!empty(contentSafety) ? contentSafety!.outputs.id : '')
var azureContentSafetyEndpoint = 'https://${azureContentSafetyResourceNameValue}.cognitiveservices.azure.com/'

// Create Azure AI Foundry with Release Manager Assistant project if not provided by user
module aiProject './core/ai/ai-project.bicep' = if (!byoaiEnabled) {
  name: 'aiproject'
  scope: rg
  params: {
    location: location
    tags: tags
    // Use dummy names and zero capacity if BYOAI is enabled
    name: !byoaiEnabled ? '${abbrs.cognitiveServicesAccounts}${resourceToken}-foundry' : ''
    projectName: !byoaiEnabled ? 'release-manager-assistant' : ''
    gpt4oCapacity: !byoaiEnabled ? 10 : 0
  }
}

// Azure AI Foundry Settings - either user provided or generated
var azureAiFoundryResourceNameValue = byoaiEnabled ? azureAiFoundryResourceName : (!empty(aiProject) ? aiProject.outputs.id : '')
var azureAiFoundryProjectNameValue = byoaiEnabled ? azureAiFoundryProjectName : (!empty(aiProject) ? aiProject.outputs.projectName : '')
var azureAiFoundryProjectEndpoint = 'https://${azureAiFoundryResourceNameValue}.services.ai.azure.com/api/projects/${azureAiFoundryProjectNameValue}'

// Azure OpenAI Settings - either user provided or generated
var azureOpenAIEndpointValue = byoaiEnabled ? azureOpenAIEndpoint : (!empty(aiProject) ? aiProject.outputs.openaiEndpoint : '')
var azureOpenAIResponsesDeploymentNameValue = byoaiEnabled ? azureOpenAIResponsesDeploymentName : (!empty(aiProject) ? aiProject.outputs.responseApiDeploymentName : '')
var azureOpenAIEmbeddingDeploymentNameValue = byoaiEnabled ? azureOpenAIEmbeddingDeploymentName : (!empty(aiProject) ? aiProject.outputs.embeddingDeploymentName : '')

// Create Container Registry for storing container images
module containerRegistry './core/host/container-registry.bicep' = {
  name: 'container-registry'
  scope: rg
  params: {
    name: 'cr${resourceToken}'
    location: location
    tags: tags
  }
}

// Create Container Apps Environment
module containerAppsEnvironment './core/host/container-apps-environment.bicep' = {
  name: 'container-apps-environment'
  scope: rg
  params: {
    name: '${abbrs.appManagedEnvironments}${resourceToken}'
    location: location
    tags: tags
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
  }
}

// Deploy Redis as a container app
module redis './app/redis.bicep' = {
  name: 'redis'
  scope: rg
  params: {
    name: '${abbrs.appContainerApps}redis-${resourceToken}'
    location: location
    tags: tags
    containerAppsEnvironmentId: containerAppsEnvironment.outputs.environmentId
    redisPassword: actualRedisPassword
  }
}

// Deploy Session Manager service
module sessionManager './app/session-manager.bicep' = {
  name: 'session-manager'
  scope: rg
  params: {
    name: '${abbrs.appContainerApps}session-manager-${resourceToken}'
    location: location
    tags: union(tags, { 'azd-service-name': 'session-manager' })
    imageName: session_manager_image_name
    containerAppsEnvironmentId: containerAppsEnvironment.outputs.environmentId
    containerRegistryId: containerRegistry.outputs.resourceId
    containerRegistryLoginServer: containerRegistry.outputs.loginServer
    containerRegistryUsername: containerRegistry.outputs.adminUsername
    containerRegistryPassword: containerRegistry.outputs.adminPassword
    keyVaultName: keyVault.outputs.name
    keyVaultUri: 'https://${keyVault.outputs.name}${environment().suffixes.keyvaultDns}/'
    redisHost: redis.outputs.hostName
    redisPort: redis.outputs.port
    contentSafetyEndpoint: azureContentSafetyEndpoint
    aiFoundryResourceId: byoaiEnabled ? azureAiFoundryResourceId : aiProject!.outputs.id
    aiFoundryEndpoint: azureAiFoundryProjectEndpoint
  }
  dependsOn: [
    secrets
  ]
}

// Deploy Orchestrator service
module orchestrator './app/orchestrator.bicep' = {
  name: 'orchestrator'
  scope: rg
  params: {
    name: '${abbrs.appContainerApps}orchestrator-${resourceToken}'
    location: location
    tags: union(tags, { 'azd-service-name': 'orchestrator' })
    imageName: orchestrator_image_name
    containerAppsEnvironmentId: containerAppsEnvironment.outputs.environmentId
    containerRegistryId: containerRegistry.outputs.resourceId
    containerRegistryLoginServer: containerRegistry.outputs.loginServer
    containerRegistryUsername: containerRegistry.outputs.adminUsername
    containerRegistryPassword: containerRegistry.outputs.adminPassword
    keyVaultName: keyVault.outputs.name
    keyVaultUri: 'https://${keyVault.outputs.name}${environment().suffixes.keyvaultDns}/'
    redisHost: redis.outputs.hostName
    redisPort: redis.outputs.port
    storageAccountName: storage.outputs.name
    aiFoundryEndpoint: azureAiFoundryProjectEndpoint
    aiFoundryResourceId: byoaiEnabled ? azureAiFoundryResourceId : aiProject!.outputs.id
    aiModelDeploymentName: azureOpenAIResponsesDeploymentNameValue
    openaiEndpoint: azureOpenAIEndpointValue
    openaiResponsesDeploymentName: azureOpenAIResponsesDeploymentNameValue
    openaiEmbeddingDeploymentName: azureOpenAIEmbeddingDeploymentNameValue
  }
  dependsOn: [
    sessionManager
    secrets
  ]
}

// Deploy Static Web App for frontend
module staticWebApp './app/frontend.bicep' = {
  name: 'frontend'
  scope: rg
  params: {
    name: '${abbrs.webStaticSites}${resourceToken}'
    location: location
    tags: union(tags, { 'azd-service-name': 'frontend' })
    sessionManagerUrl: sessionManager.outputs.uri
  }
  dependsOn: [
    orchestrator
  ]
}

// Store secrets in Key Vault
module secrets './core/security/keyvault-secrets.bicep' = {
  name: 'secrets'
  scope: rg
  params: {
    keyVaultName: keyVault.outputs.name
    secrets: [
      {
        name: 'jira-server-endpoint'
        value: jiraServerEndpoint
      }
      {
        name: 'jira-server-username'
        value: jiraServerUsername
      }
      {
        name: 'jira-server-password'
        value: jiraServerPassword
      }
      {
        name: 'azure-devops-org-name'
        value: azureDevOpsOrgName
      }
      {
        name: 'azure-devops-ext-pat'
        value: azureDevOpsExtPat
      }
      {
        name: 'redis-password'
        value: actualRedisPassword
      }
      {
        name: 'storage-account-key'
        value: storage.outputs.primaryKey
      }
      {
        name: 'azure-ai-project-endpoint'
        value: azureAiFoundryProjectEndpoint
      }
      {
        name: 'azure-openai-endpoint'
        value: azureOpenAIEndpointValue
      }
      {
        name: 'azure-openai-responses-deployment-name'
        value: azureOpenAIResponsesDeploymentNameValue
      }
      {
        name: 'azure-openai-embedding-deployment-name'
        value: azureOpenAIEmbeddingDeploymentNameValue
      }
      {
        name: 'app-insights-connection-string'
        value: monitoring.outputs.applicationInsightsConnectionString
      }
    ]
  }
}

// Outputs
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP_NAME string = rg.name

output AZURE_KEY_VAULT_NAME string = keyVault.outputs.name
output AZURE_KEY_VAULT_URI string = keyVault.outputs.uri

output AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING string = monitoring.outputs.applicationInsightsConnectionString

output REDIS_HOSTNAME string = redis.outputs.hostName
output REDIS_PORT string = string(redis.outputs.port)

output AZURE_STORAGE_ACCOUNT_NAME string = storage.outputs.name

output AZURE_CONTENT_SAFETY_ENDPOINT string = azureContentSafetyEndpoint
output AZURE_AI_PROJECT_ENDPOINT string = azureAiFoundryProjectEndpoint
output AZURE_OPENAI_ENDPOINT string = azureOpenAIEndpointValue
output AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME string = azureOpenAIResponsesDeploymentNameValue
output AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME string = azureOpenAIEmbeddingDeploymentNameValue

output SESSION_MANAGER_URL string = sessionManager.outputs.uri
output ORCHESTRATOR_URL string = orchestrator.outputs.uri
output FRONTEND_URL string = staticWebApp.outputs.uri

output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.outputs.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = containerRegistry.outputs.name
