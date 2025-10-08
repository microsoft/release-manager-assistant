@description('The name of the key vault')
param keyVaultName string

@description('Array of secrets to store in the key vault')
param secrets array = []

resource keyVault 'Microsoft.KeyVault/vaults@2022-07-01' existing = {
  name: keyVaultName
}

resource keyVaultSecrets 'Microsoft.KeyVault/vaults/secrets@2022-07-01' = [for secret in secrets: {
  name: secret.name
  parent: keyVault
  properties: {
    value: secret.value
  }
}]

output secretUris array = [for (secret, i) in secrets: keyVaultSecrets[i].properties.secretUri]
