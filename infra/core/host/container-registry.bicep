@description('The name of the container registry')
param name string

@description('The location for the container registry')
param location string = resourceGroup().location

@description('The tags to apply to the container registry')
param tags object = {}

@description('The SKU of the container registry')
@allowed([
  'Basic'
  'Standard'
  'Premium'
])
param sku string = 'Basic'

@description('Whether admin user is enabled')
param adminUserEnabled bool = true

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: adminUserEnabled
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
  }
}

output name string = containerRegistry.name
output loginServer string = containerRegistry.properties.loginServer
output resourceId string = containerRegistry.id
output adminUsername string = adminUserEnabled ? containerRegistry.name : ''
@secure()
output adminPassword string = adminUserEnabled ? containerRegistry.listCredentials().passwords[0].value : ''
