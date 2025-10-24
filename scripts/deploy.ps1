# PowerShell deployment script for Release Manager Assistant

# Set strict error handling
$ErrorActionPreference = "Stop"

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

# Run post-provision script to ensure proper role assignments
Write-Host "🔑 Running post-provision script to assign AI Foundry roles..." -ForegroundColor Blue
& "$PSScriptRoot\scripts\post-provision.ps1"

$services = @("orchestrator", "session-manager", "frontend")
$maxRetries = 3
$retryDelaySeconds = 30

foreach ($service in $services) {
    for ($i = 1; $i -le $maxRetries; $i++) {
        Write-Host "🔨 Deploying service '$service' (Attempt $i of $maxRetries)..." -ForegroundColor Blue
        
        # Run the command and check its exit code
        azd deploy $service --no-prompt
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Successfully deployed service '$service'." -ForegroundColor Green
            break # Success, exit retry loop
        }

        Write-Warning "⚠️  Deployment of service '$service' failed on attempt $i."
        if ($i -lt $maxRetries) {
            Write-Host "   Waiting for $retryDelaySeconds seconds before retrying..."
            Start-Sleep -Seconds $retryDelaySeconds
        } else {
            Write-Error "❌ Failed to deploy service '$service' after $maxRetries attempts. Aborting."
            exit 1
        }
    }
}

Write-Host "✅ All services deployed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 Your application URLs:" -ForegroundColor Cyan
azd show --output table

Write-Host ""
Write-Host "📖 To view logs:" -ForegroundColor Blue
Write-Host "   azd monitor --live" -ForegroundColor White
Write-Host ""
Write-Host "🧹 To cleanup resources:" -ForegroundColor Blue
Write-Host "   azd down --force --purge" -ForegroundColor White
