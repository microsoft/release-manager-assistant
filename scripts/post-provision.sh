#!/bin/bash

# Post Provisioning Script for Release Manager
# Assigns Azure AI User role to Session Manager and Orchestrator managed identities

# Define color codes for better readability
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
CYAN='\033[36m'
WHITE='\033[37m'
RESET='\033[0m'

echo "Starting post-provision role assignment..."

# Check if running in GitHub Actions and handle authentication
IS_GITHUB_ACTIONS="${GITHUB_ACTIONS:-false}"
if [ "$IS_GITHUB_ACTIONS" = "true" ]; then
    echo -e "${CYAN}Running in GitHub Actions - using federated identity authentication...${RESET}"

    # Check if we have the required environment variables for federated identity
    if [ -z "$AZURE_CLIENT_ID" ] || [ -z "$AZURE_TENANT_ID" ]; then
        echo -e "${YELLOW}Missing required federated identity environment variables - skipping post-provision in validation mode${RESET}"
        echo -e "${GREEN}Post-provision script completed (GitHub Actions validation mode)${RESET}"
        exit 0
    fi

    # Login using federated identity (OIDC)
    {
        echo "Logging in with federated identity..."

        # Check if OIDC environment variables are available
        if [ -n "$ACTIONS_ID_TOKEN_REQUEST_URL" ] && [ -n "$ACTIONS_ID_TOKEN_REQUEST_TOKEN" ]; then
            # Get the OIDC token
            token_uri="${ACTIONS_ID_TOKEN_REQUEST_URL}&audience=api://AzureADTokenExchange"
            federated_token=$(curl -s -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" "$token_uri" | jq -r '.value')

            # Login with the federated token
            az login --service-principal \
                --username "$AZURE_CLIENT_ID" \
                --tenant "$AZURE_TENANT_ID" \
                --federated-token "$federated_token" \
                --output none
        else
            # Fallback: try using az login with default credentials (might be pre-authenticated by validation action)
            echo "OIDC variables not available, checking if already authenticated..."
            if ! az account show >/dev/null 2>&1; then
                echo "No existing authentication found, attempting default login..."
                az login --identity --output none 2>/dev/null || true
            fi
        fi

        # Set the subscription
        if [ -n "$AZURE_SUBSCRIPTION_ID" ]; then
            echo "Setting subscription to $AZURE_SUBSCRIPTION_ID"
            az account set --subscription "$AZURE_SUBSCRIPTION_ID"
        fi

        echo -e "${GREEN}Azure authentication successful${RESET}"
    } || {
        echo -e "${YELLOW}Failed to authenticate with Azure using federated identity: $?${RESET}"
        echo -e "${YELLOW}Skipping post-provision operations in validation mode${RESET}"
        echo -e "${GREEN}Post-provision script completed (GitHub Actions validation mode)${RESET}"
        exit 0
    }
else
    # Running locally - check if user is logged in to Azure
    echo -e "${CYAN}Running locally - checking Azure authentication...${RESET}"

    if ! az account show >/dev/null 2>&1; then
        echo -e "${YELLOW}No Azure authentication found. Please run 'az login' manually and try again.${RESET}"
        exit 1
    fi

    # Display current account info
    account_info=$(az account show 2>/dev/null)
    if [ -n "$account_info" ]; then
        user_name=$(echo "$account_info" | jq -r '.user.name // .user.type')
        subscription_name=$(echo "$account_info" | jq -r '.name')
        subscription_id=$(echo "$account_info" | jq -r '.id')
        echo -e "${GREEN}Authenticated as: $user_name${RESET}"
        echo -e "${GREEN}Using subscription: $subscription_name ($subscription_id)${RESET}"
    else
        echo "Error: Failed to retrieve Azure account information." >&2
        exit 1
    fi
fi

# Get resource group name from azd environment
RESOURCE_GROUP=$(azd env get-values | grep "AZURE_RESOURCE_GROUP_NAME" | cut -d'=' -f2 | tr -d '"')
if [ -z "$RESOURCE_GROUP" ]; then
    echo "Error: AZURE_RESOURCE_GROUP_NAME is not set in the environment." >&2
    exit 1
fi

# Output all environment values for debugging
echo -e "${CYAN}Checking all azd environment values...${RESET}"
all_env_values=$(azd env get-values)
echo "$all_env_values" | while IFS='=' read -r key value; do
    if [ -n "$key" ] && [ -n "$value" ]; then
        printf "%-40s = %s\n" "$key" "$(echo "$value" | tr -d '"')"
    fi
done

# Helper function to extract environment variable values
get_azd_environment_value() {
    local variable_name="$1"
    local all_env_values="$2"

    local match=$(echo "$all_env_values" | grep "$variable_name")
    if [ -n "$match" ]; then
        local value=$(echo "$match" | cut -d'=' -f2 | tr -d '"')
        echo "$value"
    else
        return 1
    fi
}

# Try to get AI Foundry values from azd environment with better error handling
echo -e "${CYAN}Attempting to extract AI Foundry values...${RESET}"

# Extract AI Foundry configuration values
AI_FOUNDRY_RESOURCE_GROUP=$(get_azd_environment_value "AZURE_AI_FOUNDRY_RESOURCE_GROUP" "$all_env_values")
AI_FOUNDRY_RESOURCE_NAME=$(get_azd_environment_value "AZURE_AI_FOUNDRY_RESOURCE_NAME" "$all_env_values")
AI_FOUNDRY_PROJECT_NAME=$(get_azd_environment_value "AZURE_AI_FOUNDRY_PROJECT_NAME" "$all_env_values")

# Get container apps from the resource group for later role assignments
echo "Getting container apps from resource group $RESOURCE_GROUP..."
{
    container_apps=$(az containerapp list --resource-group "$RESOURCE_GROUP" --query "[].{name:name, id:id}" -o json)

    if [ -z "$container_apps" ] || [ "$container_apps" = "[]" ]; then
        if [ "$IS_GITHUB_ACTIONS" = "true" ]; then
            echo -e "${YELLOW}No container apps found in resource group $RESOURCE_GROUP (validation mode - this is expected)${RESET}"
            echo -e "${GREEN}Post-provision script completed (GitHub Actions validation mode)${RESET}"
            exit 0
        else
            echo "Error: No container apps found in resource group $RESOURCE_GROUP." >&2
            exit 1
        fi
    fi
} || {
    if [ "$IS_GITHUB_ACTIONS" = "true" ]; then
        echo -e "${YELLOW}Container app listing failed in validation mode - this is expected: $?${RESET}"
        echo -e "${GREEN}Post-provision script completed (GitHub Actions validation mode)${RESET}"
        exit 0
    else
        echo "Error: Failed to list container apps: $?" >&2
        exit 1
    fi
}

# Check if values are available, provide guidance if not
ai_foundry_configured=true
if [ -z "$AI_FOUNDRY_RESOURCE_GROUP" ] || [ -z "$AI_FOUNDRY_RESOURCE_NAME" ]; then
    echo -e "${YELLOW}AI Foundry resource information not found in environment.${RESET}"
    echo -e "${YELLOW}To configure AI Foundry integration, set these environment variables:${RESET}"
    echo -e "${CYAN}  azd env set AZURE_AI_FOUNDRY_RESOURCE_GROUP <your-resource-group>${RESET}"
    echo -e "${CYAN}  azd env set AZURE_AI_FOUNDRY_RESOURCE_NAME <your-resource-name>${RESET}"
    echo -e "${CYAN}  azd env set AZURE_AI_FOUNDRY_PROJECT_NAME <your-project-name>${RESET}"

    echo -e "${CYAN}Alternatively, set these variables in your .env file and re-run azd up${RESET}"
    ai_foundry_configured=false
fi

echo "Resource Group: $RESOURCE_GROUP"

# Only proceed with AI Foundry operations if the variables are configured
if [ "$ai_foundry_configured" = "true" ]; then
    echo "AI Foundry Resource Group: $AI_FOUNDRY_RESOURCE_GROUP"
    echo "AI Foundry Resource Name: $AI_FOUNDRY_RESOURCE_NAME"
    echo "AI Foundry Project Name: $AI_FOUNDRY_PROJECT_NAME"

    # Get the Azure AI resource ID
    echo -e "${CYAN}Getting Azure AI resource ID...${RESET}"
    ai_foundry_resource_id=$(az cognitiveservices account show --name "$AI_FOUNDRY_RESOURCE_NAME" --resource-group "$AI_FOUNDRY_RESOURCE_GROUP" --query "id" -o tsv)
    if [ -z "$ai_foundry_resource_id" ]; then
        echo "Error: Failed to find AI Foundry resource with name $AI_FOUNDRY_RESOURCE_NAME in resource group $AI_FOUNDRY_RESOURCE_GROUP." >&2
        exit 1
    fi

    echo "AI Foundry Resource ID: $ai_foundry_resource_id"
else
    echo -e "${YELLOW}Skipping AI Foundry role assignments as AI Foundry is not configured.${RESET}"
    exit 0
fi

# Azure AI User role definition ID
azure_ai_user_role_definition_id="53ca6127-db72-4b80-b1b0-d745d6d5456d"

# Process each container app for AI Foundry role assignments
echo "$container_apps" | jq -r '.[] | @base64' | while IFS= read -r app_data; do
    app=$(echo "$app_data" | base64 --decode)
    app_name=$(echo "$app" | jq -r '.name')

    # Check if this is the session manager or orchestrator
    if [[ "$app_name" == *"session-manager"* ]] || [[ "$app_name" == *"orchestrator"* ]]; then
        echo "Processing container app: $app_name"

        # Get the principal ID of the managed identity
        principal_id=$(az containerapp show --name "$app_name" --resource-group "$RESOURCE_GROUP" --query "identity.principalId" -o tsv)
        if [ -z "$principal_id" ]; then
            echo "Warning: Container app $app_name does not have a managed identity."
            continue
        fi

        echo "Container App: $app_name, Principal ID: $principal_id"

        # Assign the Azure AI User role
        echo "Assigning Azure AI User role to $app_name..."
        if az role assignment create \
            --assignee-object-id "$principal_id" \
            --role "$azure_ai_user_role_definition_id" \
            --scope "$ai_foundry_resource_id" \
            --assignee-principal-type "ServicePrincipal"; then
            echo -e "${GREEN}Role assignment created successfully for $app_name${RESET}"
        else
            echo "Error: Failed to create role assignment for $app_name" >&2
        fi
    fi
done

echo -e "${GREEN}Post-provision role assignment completed.${RESET}"
