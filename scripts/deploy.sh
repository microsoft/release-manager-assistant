#!/bin/bash

# Bash deployment script for Release Manager Assistant

#echo -e "${BLUE}📦 Provisioning Azure infrastructure...${RESET}"
azd provision --no-prompt

# Run post-provision script to ensure proper role assignments
echo -e "${BLUE}🔑 Running post-provision script to assign AI Foundry roles...${RESET}" on any error
set -e

# Define color codes for better readability
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
CYAN='\033[36m'
WHITE='\033[37m'
RESET='\033[0m'

echo -e "${GREEN}🚀 Deploying Release Manager Assistant to Azure...${RESET}"

# Check if azd is installed
if ! command -v azd &> /dev/null; then
    echo -e "${RED}❌ Azure Developer CLI (azd) is not installed. Please install it first.${RESET}"
    echo -e "${YELLOW}   Visit: https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd${RESET}"
    exit 1
fi

# Check if az CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI (az) is not installed. Please install it first.${RESET}"
    echo -e "${YELLOW}   Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli${RESET}"
    exit 1
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    echo -e "${RED}❌ Please log in to Azure first using 'az login'${RESET}"
    exit 1
fi

# Check if environment file exists
if [ ! -f ".env" ]; then
    echo -e "${BLUE}📝 Creating .env file from template...${RESET}"
    cp .env.template .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your Azure configuration and run this script again.${RESET}"
    exit 1
fi

# Load environment variables from .env file
set -o allexport
source .env
set +o allexport

# Validate required environment variables
if [ -z "$AZURE_ENV_NAME" ]; then
    echo -e "${RED}❌ AZURE_ENV_NAME is not set in .env file${RESET}"
    exit 1
fi

if [ -z "$AZURE_LOCATION" ]; then
    echo -e "${RED}❌ AZURE_LOCATION is not set in .env file${RESET}"
    exit 1
fi

if [ -z "$AZURE_SUBSCRIPTION_ID" ]; then
    echo -e "${RED}❌ AZURE_SUBSCRIPTION_ID is not set in .env file${RESET}"
    exit 1
fi

echo -e "${BLUE}🏗️  Initializing Azure Developer environment...${RESET}"
azd env new "$AZURE_ENV_NAME" --location "$AZURE_LOCATION" --subscription "$AZURE_SUBSCRIPTION_ID" || true

echo -e "\033[34m📦 Provisioning Azure infrastructure...\033[0m"
azd provision --no-prompt

# Run post-provision script to ensure proper role assignments
echo -e "\033[34m� Running post-provision script to assign AI Foundry roles...\033[0m"
chmod +x ./scripts/post-provision.sh
./scripts/post-provision.sh

# Define services and retry parameters
services=("orchestrator" "session-manager" "frontend")
max_retries=3
retry_delay_seconds=30

for service in "${services[@]}"; do
    for ((i=1; i<=max_retries; i++)); do
        echo -e "${BLUE}🔨 Deploying service '$service' (Attempt $i of $max_retries)...${RESET}"
        
        # Run the command and check its exit code
        if azd deploy "$service" --no-prompt; then
            echo -e "${GREEN}✅ Successfully deployed service '$service'.${RESET}"
            break # Success, exit retry loop
        else
            echo -e "${YELLOW}⚠️  Deployment of service '$service' failed on attempt $i.${RESET}"
            if [ $i -lt $max_retries ]; then
                echo "   Waiting for $retry_delay_seconds seconds before retrying..."
                sleep $retry_delay_seconds
            else
                echo -e "${RED}❌ Failed to deploy service '$service' after $max_retries attempts. Aborting.${RESET}"
                exit 1
            fi
        fi
    done
done

echo -e "${GREEN}✅ All services deployed successfully!${RESET}"
echo ""
echo -e "${CYAN}🔗 Your application URLs:${RESET}"
azd show --output table

echo ""
echo -e "${BLUE}📖 To view logs:${RESET}"
echo -e "${WHITE}   azd monitor --live${RESET}"
echo ""
echo -e "${BLUE}🧹 To cleanup resources:${RESET}"
echo -e "${WHITE}   azd down --force --purge${RESET}"
