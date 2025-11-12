@description('The name of the NAT gateway')
param name string

@description('The location for the NAT gateway')
param location string = resourceGroup().location

@description('The tags to apply to the NAT gateway')
param tags object = {}

@description('The name of the public IP address')
param publicIpName string

@description('Idle timeout in minutes for the NAT gateway')
param idleTimeoutInMinutes int = 4

resource publicIp 'Microsoft.Network/publicIPAddresses@2023-09-01' = {
  name: publicIpName
  location: location
  tags: tags
  sku: {
    name: 'Standard'
    tier: 'Regional'
  }
  properties: {
    publicIPAllocationMethod: 'Static'
    publicIPAddressVersion: 'IPv4'
  }
}

resource natGateway 'Microsoft.Network/natGateways@2023-09-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Standard'
  }
  properties: {
    publicIpAddresses: [
      {
        id: publicIp.id
      }
    ]
    idleTimeoutInMinutes: idleTimeoutInMinutes
  }
}

output natGatewayId string = natGateway.id
output natGatewayName string = natGateway.name
output publicIpId string = publicIp.id
output publicIpAddress string = publicIp.properties.ipAddress