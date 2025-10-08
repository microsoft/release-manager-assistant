@description('The name of the orchestrator container app')
param name string

@description('The location for the orchestrator container app')
param location string = resourceGroup().location

@description('The tags to apply to the orchestrator container app')
param tags object = {}

@description('The name of the container image')
param imageName string

@description('The resource ID of the Container Apps environment')
param containerAppsEnvironmentId string

@description('The KeyVault Name')
param keyVaultName string

@description('The KeyVault URI')
param keyVaultUri string

@description('The Redis host name')
param redisHost string

@description('The Redis port')
param redisPort int

@description('The storage account name')
param storageAccountName string

@description('The Container Registry resource ID')
param containerRegistryId string

@description('The Container Registry login server')
param containerRegistryLoginServer string

@description('The Container Registry admin username')
param containerRegistryUsername string = ''

@description('The Container Registry admin password')
@secure()
param containerRegistryPassword string = ''

@description('The AI Foundry endpoint')
param aiFoundryEndpoint string

@description('The resource ID of the AI Foundry account')
param aiFoundryResourceId string

@description('The Azure AI Model Deployment Name provided by the user')
param aiModelDeploymentName string = ''

@description('The Azure OpenAI endpoint provided by the user')
param openaiEndpoint string = ''

@description('The Azure OpenAI Responses Deployment Name provided by the user')
param openaiResponsesDeploymentName string = ''

@description('The Azure OpenAI Embedding Deployment Name provided by the user')
param openaiEmbeddingDeploymentName string = ''

resource orchestratorApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    environmentId: containerAppsEnvironmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 5002
      }
      registries: !empty(containerRegistryUsername) && !empty(containerRegistryPassword) ? [
        {
          server: containerRegistryLoginServer
          username: containerRegistryUsername
          passwordSecretRef: 'registry-password'
        }
      ] : [
        {
          server: containerRegistryLoginServer
          identity: 'system'
        }
      ]
      secrets: [
        {
          name: 'app-insights-connection-string'
          keyVaultUrl: '${keyVaultUri}secrets/app-insights-connection-string'
          identity: 'system'
        }
        {
          name: 'redis-password'
          keyVaultUrl: '${keyVaultUri}secrets/redis-password'
          identity: 'system'
        }
        {
          name: 'registry-password'
          value: containerRegistryPassword
        }
        {
          name: 'azure-openai-endpoint'
          keyVaultUrl: '${keyVaultUri}secrets/azure-openai-endpoint'
          identity: 'system'
        }
        {
          name: 'azure-openai-responses-deployment-name'
          keyVaultUrl: '${keyVaultUri}secrets/azure-openai-responses-deployment-name'
          identity: 'system'
        }
        {
          name: 'azure-openai-embedding-deployment-name'
          keyVaultUrl: '${keyVaultUri}secrets/azure-openai-embedding-deployment-name'
          identity: 'system'
        }
        {
          name: 'jira-server-endpoint'
          keyVaultUrl: '${keyVaultUri}secrets/jira-server-endpoint'
          identity: 'system'
        }
        {
          name: 'jira-server-username'
          keyVaultUrl: '${keyVaultUri}secrets/jira-server-username'
          identity: 'system'
        }
        {
          name: 'jira-server-password'
          keyVaultUrl: '${keyVaultUri}secrets/jira-server-password'
          identity: 'system'
        }
        {
          name: 'azure-devops-org-name'
          keyVaultUrl: '${keyVaultUri}secrets/azure-devops-org-name'
          identity: 'system'
        }
        {
          name: 'azure-devops-ext-pat'
          keyVaultUrl: '${keyVaultUri}secrets/azure-devops-ext-pat'
          identity: 'system'
        }
        {
          name: 'storage-account-key'
          keyVaultUrl: '${keyVaultUri}secrets/storage-account-key'
          identity: 'system'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'orchestrator'
          image: imageName
          resources: {
            cpu: json('2')
            memory: '4Gi'
          }
          env: [
            {
              name: 'KEYVAULT-URI'
              value: keyVaultUri
            }
            {
              name: 'APPLICATION-INSIGHTS-CNX-STR'
              secretRef: 'app-insights-connection-string'
            }
            {
              name: 'SERVICE-HOST'
              value: '0.0.0.0'
            }
            {
              name: 'SERVICE-PORT'
              value: '5002'
            }
            {
              name: 'AZURE-AI-PROJECT-ENDPOINT'
              value: aiFoundryEndpoint
            }
            {
              name: 'AZURE-AI-MODEL-DEPLOYMENT-NAME'
              value: aiModelDeploymentName
              secretRef: 'azure-openai-responses-deployment-name'
            }
            {
              name: 'AZURE-OPENAI-ENDPOINT'
              value: openaiEndpoint
              secretRef: 'azure-openai-endpoint'
            }
            {
              name: 'AZURE-OPENAI-RESPONSES-DEPLOYMENT-NAME'
              value: openaiResponsesDeploymentName
              secretRef: 'azure-openai-responses-deployment-name'
            }
            {
              name: 'AZURE-OPENAI-EMBEDDING-DEPLOYMENT-NAME'
              value: openaiEmbeddingDeploymentName
              secretRef: 'azure-openai-embedding-deployment-name'
            }
            {
              name: 'REDIS-HOST'
              value: redisHost
            }
            {
              name: 'REDIS-PORT'
              value: string(redisPort)
            }
            {
              name: 'REDIS-PASSWORD'
              secretRef: 'redis-password'
            }
            {
              name: 'REDIS-TASK-QUEUE-CHANNEL'
              value: 'request_task_queue'
            }
            {
              name: 'REDIS-MESSAGE-QUEUE-CHANNEL'
              value: 'response_message_queue'
            }
            {
              name: 'STORAGE-ACCOUNT-NAME'
              value: storageAccountName
            }
            {
              name: 'VISUALIZATION-DATA-CONTAINER'
              value: 'visualizations'
            }
            {
              name: 'JIRA-SERVER-ENDPOINT'
              secretRef: 'jira-server-endpoint'
            }
            {
              name: 'JIRA-SERVER-USERNAME'
              secretRef: 'jira-server-username'
            }
            {
              name: 'JIRA-SERVER-PASSWORD'
              secretRef: 'jira-server-password'
            }
            {
              name: 'AZURE-DEVOPS-ORG-NAME'
              secretRef: 'azure-devops-org-name'
            }
            {
              name: 'AZURE-DEVOPS-EXT-PAT'
              secretRef: 'azure-devops-ext-pat'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

// Role assignment for Key Vault access
resource keyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(orchestratorApp.id, keyVaultName, 'Key Vault Secrets User')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: orchestratorApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Role assignment for Storage Blob Data Contributor
resource storageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(orchestratorApp.id, storageAccountName, 'Storage Blob Data Contributor')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Blob Data Contributor
    principalId: orchestratorApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Role assignment for AI Foundry User access
resource aiFoundryUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(orchestratorApp.id, aiFoundryResourceId, 'Azure AI User')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '53ca6127-db72-4b80-b1b0-d745d6d5456d') // Azure AI User
    principalId: orchestratorApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(orchestratorApp.id, containerRegistryId, 'AcrPull') // Unique name for the role assignment
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull role definition ID
    principalId: orchestratorApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

output name string = orchestratorApp.name
output uri string = 'https://${orchestratorApp.properties.configuration.ingress.fqdn}'
output id string = orchestratorApp.id
