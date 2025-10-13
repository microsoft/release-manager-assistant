@description('The name of the MCP server container app')
param name string

@description('The location for the MCP server container app')
param location string = resourceGroup().location

@description('The tags to apply to the MCP server container app')
param tags object = {}

@description('The name of the container image')
param imageName string

@description('The resource ID of the Container Apps environment')
param containerAppsEnvironmentId string

@description('The Container Registry resource ID')
param containerRegistryId string

@description('The Container Registry login server')
param containerRegistryLoginServer string

@description('The Container Registry admin username')
param containerRegistryUsername string = ''

@description('The Container Registry admin password')
@secure()
param containerRegistryPassword string = ''

@description('The Application Insights Connection String')
@secure()
param applicationInsightsConnectionString string = ''

resource mcpServerApp 'Microsoft.App/containerApps@2023-05-01' = {
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
        external: false // Internal only - accessible by other container apps
        targetPort: 12321
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
          value: applicationInsightsConnectionString
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
          name: 'mcp-server'
          image: !empty(imageName) ? imageName : 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          resources: {
            cpu: json('1')
            memory: '2Gi'
          }
          env: [
            {
              name: 'MCP_TRANSPORT'
              value: 'http'
            }
            {
              name: 'MCP_HOST'
              value: '0.0.0.0'
            }
            {
              name: 'MCP_PORT'
              value: '12321'
            }
            {
              name: 'MCP_SERVER_NAME'
              value: 'ReleaseManagerMcpServer'
            }
            {
              name: 'MCP_DEBUG'
              value: 'false'
            }
            {
              name: 'APPLICATION_INSIGHTS_CONNECTION_STRING'
              value: applicationInsightsConnectionString
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '20'
              }
            }
          }
        ]
      }
    }
  }
}

resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(mcpServerApp.id, containerRegistryId, 'AcrPull')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull role definition ID
    principalId: mcpServerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

output mcpEndpoint string = 'http://${mcpServerApp.name}/mcp'
