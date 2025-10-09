@description('The name of the AI Foundry account')
param name string

@description('The location for the AI Foundry account')
param location string = resourceGroup().location

@description('The tags to apply to the AI Foundry account')
param tags object = {}

@description('The name of the AI project under the foundry')
param projectName string = '${name}-project'

@description('GPT-4o model deployment capacity')
param gpt4oCapacity int = 10

@description('Flag to determine if the user is bringing their own AI resources.')
param byoaiEnabled bool = false

/*
  An AI Foundry resource is a variant of a CognitiveServices/account resource type
*/
resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = if (!byoaiEnabled) {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  properties: {
    // Required to work in AI Foundry
    allowProjectManagement: true

    // Defines developer API endpoint subdomain
    customSubDomainName: name

    // Use managed identity authentication
    disableLocalAuth: true

    // Required for resource provisioning
    publicNetworkAccess: 'Enabled'
  }
}

/*
  Developer APIs are exposed via a project, which groups in- and outputs that relate to one use case, including files.
  Create the Release Manager Assistant project right away so development teams can directly get started.
  Projects may be granted individual RBAC permissions and identities on top of what account provides.
*/
resource releaseManagerProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = if (!byoaiEnabled) {
  name: projectName
  parent: aiFoundry
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: 'Release Manager Template'
    description: 'AI project for the Release Manager Template application'
  }
}

/*
  Deploy GPT-4o model to use in playground, agents and other tools.
  This ensures the model is available as soon as the resource is created.
*/
resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = if (!byoaiEnabled) {
  parent: aiFoundry
  name: 'gpt-4o'
  sku: {
    capacity: gpt4oCapacity
    name: 'GlobalStandard'
  }
  properties: {
    model: {
      name: 'gpt-4o'
      format: 'OpenAI'
      version: '2024-08-06'
    }
  }
}

/*
  Deploy text embedding model for RAG scenarios
*/
resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = if (!byoaiEnabled) {
  parent: aiFoundry
  name: 'text-embedding-3-large'
  sku: {
    capacity: 10
    name: 'Standard'
  }
  properties: {
    model: {
      name: 'text-embedding-3-large'
      format: 'OpenAI'
      version: '1'
    }
  }
}

output name string = aiFoundry.name
output endpoint string = aiFoundry.properties.endpoint
output id string = aiFoundry.id
output principalId string = aiFoundry.identity.principalId
output projectName string = releaseManagerProject.name
output projectId string = releaseManagerProject.id
output projectPrincipalId string = releaseManagerProject.identity.principalId
output gpt4oDeploymentName string = !byoaiEnabled ? gpt4oDeployment.name : ''
output embeddingDeploymentName string = !byoaiEnabled ? embeddingDeployment.name : ''
output responseApiDeploymentName string = !byoaiEnabled ? gpt4oDeployment.name : ''

@description('Required. API endpoint for the AI project.')
output projectEndpoint string = 'https://${name}.services.ai.azure.com/api/projects/${projectName}'
@description('Required. API endpoint for OpenAI.')
output openaiEndpoint string = 'https://${name}.openai.azure.com/'
