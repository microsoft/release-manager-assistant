@description('The name of the storage account')
param name string

@description('The location for the storage account')
param location string = resourceGroup().location

@description('The tags to apply to the storage account')
param tags object = {}

@description('The type of the storage account')
@allowed([
  'Standard_LRS'
  'Standard_GRS'
  'Standard_RAGRS'
  'Standard_ZRS'
  'Premium_LRS'
  'Premium_ZRS'
  'Standard_GZRS'
  'Standard_RAGZRS'
])
param skuName string = 'Standard_LRS'

@description('The kind of storage account')
@allowed([
  'Storage'
  'StorageV2'
  'BlobStorage'
  'FileStorage'
  'BlockBlobStorage'
])
param kind string = 'StorageV2'

@description('The access tier for the storage account')
@allowed([
  'Hot'
  'Cool'
])
param accessTier string = 'Hot'

@description('Whether to allow public blob access')
param allowBlobPublicAccess bool = false

@description('Whether to allow shared key access')
param allowSharedKeyAccess bool = false

@description('The default action for network access')
@allowed([
  'Allow'
  'Deny'
])
param defaultAction string = 'Deny'

@description('Whether to allow cross tenant replication')
param allowCrossTenantReplication bool = false

@description('Whether to require infrastructure encryption')
param requireInfrastructureEncryption bool = true

@description('Array of containers to create')
param containers array = []

resource storageAccount 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: skuName
  }
  kind: kind
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    accessTier: accessTier
    allowBlobPublicAccess: allowBlobPublicAccess
    allowSharedKeyAccess: allowSharedKeyAccess
    allowCrossTenantReplication: allowCrossTenantReplication
    networkAcls: {
      defaultAction: defaultAction
    }
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    encryption: {
      services: {
        blob: {
          enabled: true
          keyType: 'Account'
        }
        file: {
          enabled: true
          keyType: 'Account'
        }
      }
      keySource: 'Microsoft.Storage'
      requireInfrastructureEncryption: requireInfrastructureEncryption
    }
  }

  resource blobService 'blobServices@2022-09-01' = if (length(containers) > 0) {
    name: 'default'
  }
}

resource storageContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2022-09-01' = [for container in containers: {
  name: container.name
  parent: storageAccount::blobService
  properties: {
    publicAccess: container.?publicAccess ?? 'None'
  }
}]

output name string = storageAccount.name
output resourceId string = storageAccount.id
output primaryEndpoints object = storageAccount.properties.primaryEndpoints
@secure()
output primaryKey string = storageAccount.listKeys().keys[0].value
@secure()
output secondaryKey string = storageAccount.listKeys().keys[1].value

@secure()
output connectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
