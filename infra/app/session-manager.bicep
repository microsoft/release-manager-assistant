@description('The name of the session manager container app')
param name string

@description('The location for the session manager container app')
param location string = resourceGroup().location

@description('The tags to apply to the session manager container app')
param tags object = {}

@description('The name of the container image')
param imageName string

@description('The resource ID of the Container Apps environment')
param containerAppsEnvironmentId string

@description('The name of the Key Vault')
param keyVaultName string

@description('The KeyVault URI')
param keyVaultUri string

@description('The Redis host name')
param redisHost string

@description('The Redis port')
param redisPort int

@description('The Content Safety endpoint')
param contentSafetyEndpoint string

@description('The AI Foundry endpoint')
param aiFoundryEndpoint string

@description('The resource ID of the AI Foundry account')
param aiFoundryResourceId string

@description('The Container Registry resource ID')
param containerRegistryId string

@description('The Container Registry login server')
param containerRegistryLoginServer string

@description('The Container Registry admin username')
param containerRegistryUsername string = ''

@description('The Container Registry admin password')
@secure()
param containerRegistryPassword string = ''

resource sessionManagerApp 'Microsoft.App/containerApps@2023-05-01' = {
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
        targetPort: 5000
        transport: 'http'
        allowInsecure: false
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
          name: 'redis-password'
          keyVaultUrl: '${keyVaultUri}secrets/redis-password'
          identity: 'system'
        }
        {
          name: 'app-insights-connection-string'
          keyVaultUrl: '${keyVaultUri}secrets/app-insights-connection-string'
          identity: 'system'
        }
        {
          name: 'registry-password'
          value: containerRegistryPassword
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'session-manager'
          image: !empty(imageName) ? imageName : 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
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
              value: '5000'
            }
            {
              name: 'AZURE-CONTENT-SAFETY-SERVICE'
              value: contentSafetyEndpoint
            }
            {
              name: 'IMAGE-CONTENT-SAFETY-CHECK-ENABLED'
              value: 'true'
            }
            {
              name: 'TEXT-CONTENT-SAFETY-CHECK-ENABLED'
              value: 'true'
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
              name: 'AZURE-AI-PROJECT-ENDPOINT'
              value: aiFoundryEndpoint
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
              name: 'SESSION-MAX-RESPONSE-TIMEOUT-IN-SECONDS'
              value: '300'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '100'
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
  name: guid(sessionManagerApp.id, keyVaultName, 'Key Vault Secrets User')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: sessionManagerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Role assignment for Container Registry access (AcrPull)
resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(sessionManagerApp.id, containerRegistryId, 'AcrPull')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
    principalId: sessionManagerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Role assignment for AI Foundry access (Azure AI User)
resource aiFoundryRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(sessionManagerApp.id, aiFoundryResourceId, 'Azure AI User')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '53ca6127-db72-4b80-b1b0-d745d6d5456d') // Azure AI User
    principalId: sessionManagerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

output name string = sessionManagerApp.name
output uri string = 'https://${sessionManagerApp.properties.configuration.ingress.fqdn}'
output id string = sessionManagerApp.id
