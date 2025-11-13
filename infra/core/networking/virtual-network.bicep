@description('The name of the virtual network')
param name string

@description('The location for the virtual network')
param location string = resourceGroup().location

@description('The tags to apply to the virtual network')
param tags object = {}

@description('The address space for the virtual network')
param addressSpace string = '10.0.0.0/16'

@description('The name of the subnet for Container Apps')
param subnetName string = 'container-apps-subnet'

@description('The address prefix for the Container Apps subnet')
param subnetAddressPrefix string = '10.0.0.0/23'

@description('The resource ID of the NAT gateway to attach to the subnet')
param natGatewayId string

resource virtualNetwork 'Microsoft.Network/virtualNetworks@2023-09-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [
        addressSpace
      ]
    }
    subnets: [
      {
        name: subnetName
        properties: {
          addressPrefix: subnetAddressPrefix
          natGateway: {
            id: natGatewayId
          }
          serviceEndpoints: []
          delegations: [
            {
              name: 'Microsoft.App.environments'
              properties: {
                serviceName: 'Microsoft.App/environments'
              }
              type: 'Microsoft.Network/virtualNetworks/subnets/delegations'
            }
          ]
        }
        type: 'Microsoft.Network/virtualNetworks/subnets'
      }
    ]
    virtualNetworkPeerings: []
    enableDdosProtection: false
  }
}

output vnetId string = virtualNetwork.id
output vnetName string = virtualNetwork.name
output subnetId string = virtualNetwork.properties.subnets[0].id
output subnetName string = subnetName