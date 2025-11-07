@description('The location for the Network Security Perimeter resource.')
param location string = resourceGroup().location

@description('The name of the Network Security Perimeter Resource.')
param nspName string = 'releaseManagerAssistantNsp'

@description('The name of the default NSP profile.')
param profileName string = 'releaseManagerAssistantNspProfile'

@description('The resource ID of the Key Vault to associate with the NSP.')
param keyVaultResourceId string

@description('The resource ID of the Storage Account to associate with the NSP.')
param storageAccountResourceId string

resource networkSecurityPerimeter 'Microsoft.Network/networkSecurityPerimeters@2023-07-01-preview' = {
    name: nspName
    location: location
    properties: {}
}

resource profile 'Microsoft.Network/networkSecurityPerimeters/profiles@2023-07-01-preview' = {
    parent: networkSecurityPerimeter
    name: profileName
    location: location
    properties: {}
}

// Network Security Perimeter associated with Key Vault
resource keyVaultAssociation 'Microsoft.Network/networkSecurityPerimeters/resourceAssociations@2023-07-01-preview' = {
    parent: networkSecurityPerimeter
    name: 'keyvault-association'
    location: location
    properties: {
        privateLinkResource: {
            id: keyVaultResourceId
        }
        profile: {
            id: profile.id
        }
        accessMode: 'Learning'
    }
}

// Network Security Perimeter associated with Storage Account
resource storageAccountAssociation 'Microsoft.Network/networkSecurityPerimeters/resourceAssociations@2023-07-01-preview' = {
    parent: networkSecurityPerimeter
    name: 'storage-association'
    location: location
    properties: {
        privateLinkResource: {
            id: storageAccountResourceId
        }
        profile: {
            id: profile.id
        }
        accessMode: 'Learning'
    }
}

@description('The Network Security Perimeter resource name.')
output nspName string = networkSecurityPerimeter.name

@description('The Network Security Perimeter profile resource Id.')
output profileId string = profile.id
