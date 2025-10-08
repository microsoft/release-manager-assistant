@description('The name of the static web app')
param name string

@description('The location for the static web app')
param location string = resourceGroup().location

@description('The tags to apply to the static web app')
param tags object = {}

@description('The pricing tier of the static web app')
@allowed([
  'Free'
  'Standard'
])
param skuName string = 'Free'

@description('The tier of the static web app')
@allowed([
  'Free'
  'Standard'
])
param skuTier string = 'Free'

@description('The Session Manager URL for API calls')
param sessionManagerUrl string

resource staticWebApp 'Microsoft.Web/staticSites@2022-09-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: skuName
    tier: skuTier
  }
  properties: {
    repositoryUrl: ''
    branch: ''
    buildProperties: {
      appLocation: '/src/frontend/react-app'
      apiLocation: ''
      outputLocation: 'dist'
    }
  }
}

// Configure app settings for the static web app
resource staticWebAppSettings 'Microsoft.Web/staticSites/config@2022-09-01' = {
  name: 'appsettings'
  parent: staticWebApp
  properties: {
    VITE_SESSION_MANAGER_URL: sessionManagerUrl
  }
}

output name string = staticWebApp.name
output uri string = 'https://${staticWebApp.properties.defaultHostname}'
output id string = staticWebApp.id
output defaultHostname string = staticWebApp.properties.defaultHostname
