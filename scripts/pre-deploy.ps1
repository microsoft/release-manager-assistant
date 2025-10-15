# Pre-Deploy Script for Release Manager Assistant
# Builds the frontend application

Write-Host "Building Frontend.." -ForegroundColor Green

# Get the Session Manager URL from azd environment with better error handling
$sessionManagerUrl = (azd env get-values | Select-String "SESSION_MANAGER_URL" | ForEach-Object { $_.ToString().Split('=')[1].Trim('"') })

# Validate the URL
if (-not $sessionManagerUrl) {
    Write-Error "SESSION_MANAGER_URL is not set in the environment."
    exit 1
}

# Ensure URL has protocol
if (-not ($sessionManagerUrl -match "^https?://")) {
    Write-Error "SESSION_MANAGER_URL must start with http:// or https://"
    exit 1
}

Write-Host "Session Manager URL: $sessionManagerUrl" -ForegroundColor Cyan

# Build the frontend with the environment variable
Set-Location "./src/frontend/react-app"
$env:VITE_SESSION_MANAGER_URL = $sessionManagerUrl

# Create a .env file to ensure Vite picks up the variable
Set-Content -Path ".env" -Value "VITE_SESSION_MANAGER_URL=$sessionManagerUrl"
Write-Host "Created .env file with VITE_SESSION_MANAGER_URL=$sessionManagerUrl" -ForegroundColor Cyan
npm install
npm run build

# Copy the build files to a deployment directory
if (!(Test-Path "../../../infra/frontend-build")) {
    New-Item -ItemType Directory -Force -Path "../../../infra/frontend-build"
}
Copy-Item -Path "./dist/*" -Destination "../../../infra/frontend-build/" -Recurse -Force

Write-Host "Frontend build completed successfully!" -ForegroundColor Green