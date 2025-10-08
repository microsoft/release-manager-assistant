param (
    [Parameter(Mandatory=$true)][string]$Path
)

# check if virtual environment already exists
if (-Not (Test-Path -Path "$Path/.venv"))
{
  Write-Host ""
  Write-Host "Creating python virtual environment in directory $Path/.venv"
  $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
  if (-not $pythonCmd) {
    # fallback to python3 if python not found
    $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
  }
  Start-Process -FilePath ($pythonCmd).Source -ArgumentList "-m venv $Path/.venv" -Wait -NoNewWindow
  if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Failed to create python virtual environment in directory $Path/.venv"
    exit $LASTEXITCODE
  }
}

Write-Host "Installing keyring and artifacts-keyring packages"

  # Activate the virtual environment
  & "$Path/.venv/Scripts/Activate.ps1"

  # Install required packages
  pip install keyring artifacts-keyring
  pip install wheel setuptools