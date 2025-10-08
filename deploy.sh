#!/bin/bash

# Exit on any error
set -e

echo "🚀 Deploying Release Manager Assistant to Azure..."

# Check if azd is installed
if ! command -v azd &> /dev/null; then
    echo "❌ Azure Developer CLI (azd) is not installed. Please install it first."
    echo "   Visit: https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd"
    exit 1
fi

# Check if az CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI (az) is not installed. Please install it first."
    echo "   Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    echo "❌ Please log in to Azure first using 'az login'"
    exit 1
fi

# Check if environment file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.template .env
    echo "⚠️  Please edit .env file with your Azure configuration and run this script again."
    exit 1
fi

# Source environment variables
export $(cat .env | grep -v '^#' | xargs)

# Validate required environment variables
if [ -z "$AZURE_ENV_NAME" ]; then
    echo "❌ AZURE_ENV_NAME is not set in .env file"
    exit 1
fi

if [ -z "$AZURE_LOCATION" ]; then
    echo "❌ AZURE_LOCATION is not set in .env file"
    exit 1
fi

if [ -z "$AZURE_SUBSCRIPTION_ID" ]; then
    echo "❌ AZURE_SUBSCRIPTION_ID is not set in .env file"
    exit 1
fi

echo "🏗️  Initializing Azure Developer environment..."
azd env new $AZURE_ENV_NAME --location $AZURE_LOCATION --subscription $AZURE_SUBSCRIPTION_ID || true

echo "📦 Provisioning Azure infrastructure..."
azd provision --no-prompt

echo "🔨 Building and deploying applications..."
azd deploy --no-prompt

echo "✅ Deployment completed successfully!"
echo ""
echo "🔗 Your application URLs:"
azd show --output table

echo ""
echo "📖 To view logs:"
echo "   azd monitor --live"
echo ""
echo "🧹 To cleanup resources:"
echo "   azd down --force --purge"
