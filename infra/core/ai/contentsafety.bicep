@description('The name of the Content Safety service')
param name string

@description('The location for the Content Safety service')
param location string = resourceGroup().location

@description('The tags to apply to the Content Safety service')
param tags object = {}

@description('The pricing tier of the Content Safety service')
@allowed([
  'F0'
  'S0'
])
param skuName string = 'F0'

resource contentSafety 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: name
  location: location
  tags: tags
  kind: 'ContentSafety'
  properties: {
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
  }
  sku: {
    name: skuName
  }
}

output name string = contentSafety.name
output endpoint string = contentSafety.properties.endpoint
output id string = contentSafety.id
@secure()
output primaryKey string = contentSafety.listKeys().key1
@secure()
output secondaryKey string = contentSafety.listKeys().key2
