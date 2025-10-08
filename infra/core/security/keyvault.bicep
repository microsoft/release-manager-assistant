@description('The name of the key vault')
param name string

@description('The location for the key vault')
param location string = resourceGroup().location

@description('The tags to apply to the key vault')
param tags object = {}

@description('The Azure Active Directory tenant ID that should be used for authenticating requests to the key vault')
param tenantId string = tenant().tenantId

@description('Specifies whether the key vault is a standard vault or a premium vault')
@allowed([
  'standard'
  'premium'
])
param skuName string = 'standard'

resource keyVault 'Microsoft.KeyVault/vaults@2022-07-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    tenantId: tenantId
    sku: {
      family: 'A'
      name: skuName
    }
    accessPolicies: []
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enableRbacAuthorization: true
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

output name string = keyVault.name
output uri string = keyVault.properties.vaultUri
output resourceId string = keyVault.id
