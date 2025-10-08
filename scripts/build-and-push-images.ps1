#!/usr/bin/env pwsh

# Script to build and push Docker images to ACR

param(
    [Parameter(Mandatory=$true)][string]$AcrName,
    [Parameter(Mandatory=$false)][string]$SessionManagerImageName = "session-manager:latest",
    [Parameter(Mandatory=$false)][string]$OrchestratorImageName = "orchestrator:latest"
)

Write-Host "Building and pushing Docker images to ACR: $AcrName"

# Set ACR login server
$loginServer = "$AcrName.azurecr.io"

# Log in to ACR
Write-Host "Logging in to ACR..."
az acr login --name $AcrName

# Build and push Session Manager image
Write-Host "Building Session Manager image..."
$sessionManagerImageTag = "$loginServer/$SessionManagerImageName"
docker build -f ./src/backend/services/session_manager/Dockerfile -t $sessionManagerImageTag ./src/backend
Write-Host "Pushing Session Manager image to ACR..."
docker push $sessionManagerImageTag

# Build and push Orchestrator image
Write-Host "Building Orchestrator image..."
$orchestratorImageTag = "$loginServer/$OrchestratorImageName"
docker build -f ./src/backend/services/orchestrator/Dockerfile -t $orchestratorImageTag ./src/backend
Write-Host "Pushing Orchestrator image to ACR..."
docker push $orchestratorImageTag

Write-Host "Images successfully built and pushed to ACR."
Write-Host "Session Manager: $sessionManagerImageTag"
Write-Host "Orchestrator: $orchestratorImageTag"

# Update the .env file with the full image paths
$envFile = "./.env"
$envContent = Get-Content $envFile -Raw

$envContent = $envContent -replace "SESSION_MANAGER_IMAGE_NAME=.*", "SESSION_MANAGER_IMAGE_NAME=$sessionManagerImageTag"
$envContent = $envContent -replace "ORCHESTRATOR_IMAGE_NAME=.*", "ORCHESTRATOR_IMAGE_NAME=$orchestratorImageTag"

Set-Content -Path $envFile -Value $envContent

Write-Host ".env file updated with full image paths."
