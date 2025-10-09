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

@description('The Redis password')
@secure()
param redisPassword string

@description('The storage account name')
param storageAccountName string

@description('The Container Registry resource ID')
param containerRegistryId string

@description('The Container Registry login server')
param containerRegistryLoginServer string

@description('The AI Foundry endpoint')
param aiFoundryEndpoint string

@description('The Azure AI Model Deployment Name provided by the user')
param aiModelDeploymentName string = ''

@description('The Azure OpenAI endpoint provided by the user')
@secure()
param openaiEndpoint string = ''

@description('The Azure OpenAI Responses Deployment Name provided by the user')
@secure()
param openaiResponsesDeploymentName string = ''

@description('The Azure OpenAI Embedding Deployment Name provided by the user')
@secure()
param openaiEmbeddingDeploymentName string = ''

@description('The Application Insights Connection String')
@secure()
param applicationInsightsConnectionString string = ''

@description('Jira server endpoint')
@secure()
param jiraServerEndpoint string = ''

@description('Jira server username')
@secure()
param jiraServerUsername string = ''

@description('Jira server password')
@secure()
param jiraServerPassword string = ''

@description('Azure DevOps organization name')
@secure()
param azureDevOpsOrgName string = ''

@description('Azure DevOps PAT token')
@secure()
param azureDevOpsExtPat string = ''

@description('Storage account key')
@secure()
param storageAccountKey string = ''

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
      registries: [
        {
          server: containerRegistryLoginServer
          identity: 'system'
        }
      ]
      secrets: [
        {
          name: 'app-insights-connection-string'
          value: applicationInsightsConnectionString
        }
        {
          name: 'redis-password'
          value: redisPassword
        }
        {
          name: 'azure-openai-endpoint'
          value: openaiEndpoint
        }
        {
          name: 'azure-openai-responses-deployment-name'
          value: openaiResponsesDeploymentName
        }
        {
          name: 'azure-openai-embedding-deployment-name'
          value: openaiEmbeddingDeploymentName
        }
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
          name: 'storage-account-key'
          value: storageAccountKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'orchestrator'
          image: !empty(imageName) ? imageName : 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
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
              value: applicationInsightsConnectionString
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
              name: 'AZURE_AI_MODEL_DEPLOYMENT_NAME'
              value: aiModelDeploymentName
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: openaiEndpoint
            }
            {
              name: 'AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME'
              value: openaiResponsesDeploymentName
            }
            {
              name: 'AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME'
              value: openaiEmbeddingDeploymentName
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
              value: redisPassword
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
              value: jiraServerEndpoint
            }
            {
              name: 'JIRA-SERVER-USERNAME'
              value: jiraServerUsername
            }
            {
              name: 'JIRA-SERVER-PASSWORD'
              value: jiraServerPassword
            }
            {
              name: 'AZURE-DEVOPS-ORG-NAME'
              value: azureDevOpsOrgName
            }
            {
              name: 'AZURE-DEVOPS-EXT-PAT'
              value: azureDevOpsExtPat
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
output principalId string = orchestratorApp.identity.principalId
