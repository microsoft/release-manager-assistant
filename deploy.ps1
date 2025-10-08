# PowerShell deployment script for Release Manager Assistant

# Exit Write-Host "🚀 Provisioning infrastructure, building images, and deploying services..." -ForegroundColor Blue
azd up --no-promptrorActionPreference = "Stop"

Write-Host "🚀 Deploying Release Manager Assistant to Azure..." -ForegroundColor Green

# Check if azd is installed
if (!(Get-Command "azd" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Azure Developer CLI (azd) is not installed. Please install it first." -ForegroundColor Red
    Write-Host "   Visit: https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd" -ForegroundColor Yellow
    exit 1
}

# Check if az CLI is installed
if (!(Get-Command "az" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Azure CLI (az) is not installed. Please install it first." -ForegroundColor Red
    Write-Host "   Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Yellow
    exit 1
}

# Check if logged in to Azure
try {
    az account show | Out-Null
} catch {
    Write-Host "❌ Please log in to Azure first using 'az login'" -ForegroundColor Red
    exit 1
}

# Check if environment file exists
if (!(Test-Path ".env")) {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Blue
    Copy-Item ".env.template" ".env"
    Write-Host "⚠️  Please edit .env file with your Azure configuration and run this script again." -ForegroundColor Yellow
    exit 1
}

# Load environment variables from .env file
Get-Content ".env" | ForEach-Object {
    if ($_ -match '^([^#][^=]*?)=(.*)$') {
        $key = $Matches[1].Trim()
        $value = $Matches[2].Trim()
        if ($value) {
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

# Validate required environment variables
if (-not $env:AZURE_ENV_NAME) {
    Write-Host "❌ AZURE_ENV_NAME is not set in .env file" -ForegroundColor Red
    exit 1
}

if (-not $env:AZURE_LOCATION) {
    Write-Host "❌ AZURE_LOCATION is not set in .env file" -ForegroundColor Red
    exit 1
}

if (-not $env:AZURE_SUBSCRIPTION_ID) {
    Write-Host "❌ AZURE_SUBSCRIPTION_ID is not set in .env file" -ForegroundColor Red
    exit 1
}

Write-Host "🏗️  Initializing Azure Developer environment..." -ForegroundColor Blue
try {
    azd env new $env:AZURE_ENV_NAME --location $env:AZURE_LOCATION --subscription $env:AZURE_SUBSCRIPTION_ID
} catch {
    # Environment might already exist
}

Write-Host "📦 Provisioning Azure infrastructure..." -ForegroundColor Blue
azd provision --no-prompt

Write-Host "� Getting ACR name from azd environment..." -ForegroundColor Blue
$acrName = $(azd env get-values | Select-String "AZURE_CONTAINER_REGISTRY_NAME" | ForEach-Object { $_.ToString().Split('=')[1].Trim('"') })
if ([string]::IsNullOrWhiteSpace($acrName)) {
    Write-Error "Failed to get ACR name from azd environment"
    exit 1
}

Write-Host "🐳 Building and pushing Docker images to ACR: $acrName..." -ForegroundColor Blue
$sessionManagerImage = "$($env:AZURE_ENV_NAME)-session-manager"
$orchestratorImage = "$($env:AZURE_ENV_NAME)-orchestrator"
./scripts/build-and-push-images.ps1 -AcrName $acrName -SessionManagerImageName $sessionManagerImage -OrchestratorImageName $orchestratorImage

Write-Host "🔨 Deploying applications with container images..." -ForegroundColor Blue
azd deploy --no-prompt

Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 Your application URLs:" -ForegroundColor Cyan
azd show --output table

Write-Host ""
Write-Host "📖 To view logs:" -ForegroundColor Blue
Write-Host "   azd monitor --live" -ForegroundColor White
Write-Host ""
Write-Host "🧹 To cleanup resources:" -ForegroundColor Blue
Write-Host "   azd down --force --purge" -ForegroundColor White
