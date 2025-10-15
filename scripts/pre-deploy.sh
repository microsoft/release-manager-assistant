#!/bin/bash
# Pre-Deploy Script for Release Manager Assistant
# Builds the frontend application

# Define color codes for better readability
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
CYAN='\033[36m'
WHITE='\033[37m'
RESET='\033[0m'

set -e

echo -e "${GREEN}Building Frontend..${RESET}"

# Get the Session Manager URL from azd environment with better error handling
session_manager_url=$(azd env get-values | grep "SESSION_MANAGER_URL=" | cut -d'=' -f2 | tr -d '"')

# Validate the URL
if [ -z "$session_manager_url" ]; then
    echo -e "${RED}Error: SESSION_MANAGER_URL is not set in the environment.${RESET}"
    exit 1
fi

# Ensure URL has protocol
if [[ ! "$session_manager_url" =~ ^https?:// ]]; then
    echo -e "${RED}Error: SESSION_MANAGER_URL must start with http:// or https://${RESET}"
    exit 1
fi

echo -e "${CYAN}Session Manager URL: $session_manager_url${RESET}"

# Build the frontend with the environment variable
cd "./src/frontend/react-app"
export VITE_SESSION_MANAGER_URL="$session_manager_url"

# Create a .env file to ensure Vite picks up the variable
echo "VITE_SESSION_MANAGER_URL=$session_manager_url" > .env
echo -e "${CYAN}Created .env file with VITE_SESSION_MANAGER_URL=$session_manager_url${RESET}"
npm install
npm run build

# Copy the build files to a deployment directory
if [ ! -d "../../../infra/frontend-build" ]; then
    mkdir -p "../../../infra/frontend-build"
fi
cp -r ./dist/* "../../../infra/frontend-build/"

echo -e "${GREEN}Frontend build completed successfully!${RESET}"