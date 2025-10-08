@description('The name of the Container Apps environment')
param name string

@description('The location for the Container Apps environment')
param location string = resourceGroup().location

@description('The tags to apply to the Container Apps environment')
param tags object = {}

@description('The resource ID of the Log Analytics workspace')
param logAnalyticsWorkspaceId string

@description('Whether to enable zone redundancy')
param zoneRedundant bool = false

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: reference(logAnalyticsWorkspaceId, '2021-12-01-preview').customerId
        sharedKey: listKeys(logAnalyticsWorkspaceId, '2021-12-01-preview').primarySharedKey
      }
    }
    zoneRedundant: zoneRedundant
  }
}

output environmentId string = containerAppsEnvironment.id
output name string = containerAppsEnvironment.name
output domain string = containerAppsEnvironment.properties.defaultDomain
