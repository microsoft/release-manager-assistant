@description('The name of the Redis container app')
param name string

@description('The location for the Redis container app')
param location string = resourceGroup().location

@description('The tags to apply to the Redis container app')
param tags object = {}

@description('The resource ID of the Container Apps environment')
param containerAppsEnvironmentId string

@description('Redis password')
@secure()
param redisPassword string

resource redisApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    environmentId: containerAppsEnvironmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: false
        targetPort: 6379
        transport: 'tcp'
      }
      secrets: [
        {
          name: 'redis-password'
          value: redisPassword
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'redis'
          image: 'redis:7-alpine'
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          args: [
            'redis-server'
            '--requirepass'
            redisPassword
            '--appendonly'
            'yes'
            '--bind'
            '0.0.0.0'
            '--loglevel'
            'notice'
          ]
          volumeMounts: [
            {
              volumeName: 'redis-data'
              mountPath: '/data'
            }
          ]
        }
      ]
      volumes: [
        {
          name: 'redis-data'
          storageType: 'EmptyDir'
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1  // Redis should run as single instance
      }
    }
  }
}

output hostName string = redisApp.name
output endpoint string = redisApp.properties.configuration.ingress.fqdn
output port int = 6379

@secure()
output password string = redisPassword
