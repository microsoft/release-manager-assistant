# Post Provisioning Script for Release Manager
# Assigns Azure AI User role to Session Manager and Orchestrator managed identities

Write-Host "Starting post-provision role assignment..."

# Check if running in GitHub Actions and handle authentication
$isGitHubActions = $env:GITHUB_ACTIONS -eq "true"
if ($isGitHubActions) {
    Write-Host "Running in GitHub Actions - using federated identity authentication..." -ForegroundColor Cyan

    # Check if we have the required environment variables for federated identity
    if (-not $env:AZURE_CLIENT_ID -or -not $env:AZURE_TENANT_ID) {
        Write-Host "Missing required federated identity environment variables - skipping post-provision in validation mode" -ForegroundColor Yellow
        Write-Host "Post-provision script completed (GitHub Actions validation mode)" -ForegroundColor Green
        exit 0
    }

    # Login using federated identity (OIDC)
    try {
        Write-Host "Logging in with federated identity..."

        # Check if OIDC environment variables are available
        if ($env:ACTIONS_ID_TOKEN_REQUEST_URL -and $env:ACTIONS_ID_TOKEN_REQUEST_TOKEN) {
            # Get the OIDC token
            $tokenUri = "$env:ACTIONS_ID_TOKEN_REQUEST_URL&audience=api://AzureADTokenExchange"
            $tokenResponse = Invoke-RestMethod -Uri $tokenUri -Headers @{
                Authorization = "bearer $env:ACTIONS_ID_TOKEN_REQUEST_TOKEN"
            }
            $federatedToken = $tokenResponse.value

            # Login with the federated token
            az login --service-principal `
                --username $env:AZURE_CLIENT_ID `
                --tenant $env:AZURE_TENANT_ID `
                --federated-token $federatedToken `
                --output none
        } else {
            # Fallback: try using az login with default credentials (might be pre-authenticated by validation action)
            Write-Host "OIDC variables not available, checking if already authenticated..."
            $accountInfo = az account show 2>$null
            if (-not $accountInfo) {
                Write-Host "No existing authentication found, attempting default login..."
                az login --identity --output none 2>$null
            }
        }

        # Set the subscription
        if ($env:AZURE_SUBSCRIPTION_ID) {
            Write-Host "Setting subscription to $env:AZURE_SUBSCRIPTION_ID"
            az account set --subscription $env:AZURE_SUBSCRIPTION_ID
        }

        Write-Host "Azure authentication successful" -ForegroundColor Green
    }
    catch {
        Write-Host "Failed to authenticate with Azure using federated identity: $_" -ForegroundColor Yellow
        Write-Host "Skipping post-provision operations in validation mode" -ForegroundColor Yellow
        Write-Host "Post-provision script completed (GitHub Actions validation mode)" -ForegroundColor Green
        exit 0
    }
}

# Get resource group name from azd environment
$ResourceGroup = $(azd env get-values | Select-String "AZURE_RESOURCE_GROUP_NAME" | ForEach-Object { $_.ToString().Split('=')[1].Trim('"') })
if (-not $ResourceGroup) {
    Write-Error "AZURE_RESOURCE_GROUP_NAME is not set in the environment."
    exit 1
}

# Output all environment values for debugging
Write-Host "Checking all azd environment values..." -ForegroundColor Cyan
$allEnvValues = azd env get-values

# Try to get AI Foundry values from azd environment with better error handling
Write-Host "Attempting to extract AI Foundry values..." -ForegroundColor Cyan

# Helper function to extract environment variable values
function Get-AzdEnvironmentValue {
    param(
        [string]$VariableName,
        [string[]]$AllEnvValues
    )

    $match = $AllEnvValues | Select-String $VariableName
    if ($match) {
        Write-Host "Found match for $VariableName`: $match" -ForegroundColor Green
        try {
            $value = $match.ToString().Split('=')[1].Trim('"')
            Write-Host "Extracted value: $value" -ForegroundColor Green
            return $value
        } catch {
            Write-Host "Error parsing $VariableName value: $_" -ForegroundColor Red
            return $null
        }
    } else {
        Write-Host "$VariableName not found in environment" -ForegroundColor Yellow
        return $null
    }
}

# Extract AI Foundry configuration values
$AiFoundryResourceGroup = Get-AzdEnvironmentValue -VariableName "AZURE_AI_FOUNDRY_RESOURCE_GROUP" -AllEnvValues $allEnvValues
$AiFoundryResourceName = Get-AzdEnvironmentValue -VariableName "AZURE_AI_FOUNDRY_RESOURCE_NAME" -AllEnvValues $allEnvValues
$AiFoundryProjectName = Get-AzdEnvironmentValue -VariableName "AZURE_AI_FOUNDRY_PROJECT_NAME" -AllEnvValues $allEnvValues

# Get container apps from the resource group for later role assignments
Write-Host "Getting container apps from resource group $ResourceGroup..."
try {
    $containerApps = az containerapp list --resource-group $ResourceGroup --query "[].{name:name, id:id}" -o json | ConvertFrom-Json

    if (-not $containerApps -or $containerApps.Count -eq 0) {
        if ($isGitHubActions) {
            Write-Host "No container apps found in resource group $ResourceGroup (validation mode - this is expected)" -ForegroundColor Yellow
            Write-Host "Post-provision script completed (GitHub Actions validation mode)" -ForegroundColor Green
            exit 0
        } else {
            Write-Error "No container apps found in resource group $ResourceGroup."
            exit 1
        }
    }
}
catch {
    if ($isGitHubActions) {
        Write-Host "Container app listing failed in validation mode - this is expected: $_" -ForegroundColor Yellow
        Write-Host "Post-provision script completed (GitHub Actions validation mode)" -ForegroundColor Green
        exit 0
    } else {
        Write-Error "Failed to list container apps: $_"
        exit 1
    }
}

# Check if values are available, provide guidance if not
$aiFoundryConfigured = $true
if (-not $AiFoundryResourceGroup -or -not $AiFoundryResourceName) {
    Write-Host "AI Foundry resource information not found in environment." -ForegroundColor Yellow
    Write-Host "To configure AI Foundry integration, set these environment variables:" -ForegroundColor Yellow
    Write-Host "  azd env set AZURE_AI_FOUNDRY_RESOURCE_GROUP <your-resource-group>" -ForegroundColor Cyan
    Write-Host "  azd env set AZURE_AI_FOUNDRY_RESOURCE_NAME <your-resource-name>" -ForegroundColor Cyan
    Write-Host "  azd env set AZURE_AI_FOUNDRY_PROJECT_NAME <your-project-name>" -ForegroundColor Cyan

    Write-Host "Alternatively, set these variables in your .env file and re-run azd up" -ForegroundColor Cyan
    $aiFoundryConfigured = $false
}

Write-Host "Resource Group: $ResourceGroup"

# Only proceed with AI Foundry operations if the variables are configured
if ($aiFoundryConfigured) {
    Write-Host "AI Foundry Resource Group: $AiFoundryResourceGroup"
    Write-Host "AI Foundry Resource Name: $AiFoundryResourceName"
    Write-Host "AI Foundry Project Name: $AiFoundryProjectName"

    # Get the Azure AI resource ID
    Write-Host "Getting Azure AI resource ID..." -ForegroundColor Cyan
    $aiFoundryResourceId = az cognitiveservices account show --name $AiFoundryResourceName --resource-group $AiFoundryResourceGroup --query "id" -o tsv
    if (-not $aiFoundryResourceId) {
        Write-Error "Failed to find AI Foundry resource with name $AiFoundryResourceName in resource group $AiFoundryResourceGroup."
        exit 1
    }

    Write-Host "AI Foundry Resource ID: $aiFoundryResourceId"
} else {
    Write-Host "Skipping AI Foundry role assignments as AI Foundry is not configured." -ForegroundColor Yellow
    exit 0
}

# Azure AI User role definition ID
$azureAiUserRoleDefinitionId = "53ca6127-db72-4b80-b1b0-d745d6d5456d"

# Process each container app for AI Foundry role assignments
foreach ($app in $containerApps) {
    # Check if this is the session manager or orchestrator
    if ($app.name -like "*session-manager*" -or $app.name -like "*orchestrator*") {
        Write-Host "Processing container app: $($app.name)"

        # Get the principal ID of the managed identity
        $principalId = az containerapp show --name $app.name --resource-group $ResourceGroup --query "identity.principalId" -o tsv
        if (-not $principalId) {
            Write-Warning "Container app $($app.name) does not have a managed identity."
            continue
        }

        Write-Host "Container App: $($app.name), Principal ID: $principalId"

        # Assign the Azure AI User role
        Write-Host "Assigning Azure AI User role to $($app.name)..."
        az role assignment create `
            --assignee-object-id $principalId `
            --role $azureAiUserRoleDefinitionId `
            --scope $aiFoundryResourceId `
            --assignee-principal-type "ServicePrincipal"

        if ($LASTEXITCODE -eq 0) {
            Write-Host "Role assignment created successfully for $($app.name)" -ForegroundColor Green
        } else {
            Write-Error "Failed to create role assignment for $($app.name)"
        }
    }
}

Write-Host "Post-provision role assignment completed." -ForegroundColor Green