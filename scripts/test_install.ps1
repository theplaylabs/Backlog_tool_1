# Test installation script for backlog-cli
# Creates a temporary virtual environment and installs the package

param (
    [Parameter(Mandatory=$false)]
    [string]$WheelPath
)

# Determine wheel path if not provided
if (-not $WheelPath) {
    $DistDir = Join-Path (Split-Path -Parent $PSScriptRoot) "dist"
    $WheelFiles = Get-ChildItem -Path $DistDir -Filter "*.whl"
    if ($WheelFiles.Count -eq 0) {
        Write-Error "No wheel files found in dist directory. Run build.ps1 first."
        exit 1
    }
    $WheelPath = $WheelFiles[0].FullName
}

# Create temp directory
$TempDir = Join-Path $env:TEMP "bckl_test_$(Get-Random)"
New-Item -ItemType Directory -Path $TempDir | Out-Null

try {
    # Create virtual environment
    Write-Host "Creating test environment in $TempDir..." -ForegroundColor Cyan
    python -m venv "$TempDir\venv"
    
    # Activate virtual environment
    & "$TempDir\venv\Scripts\Activate.ps1"
    
    # Install the wheel
    Write-Host "Installing $WheelPath..." -ForegroundColor Cyan
    pip install $WheelPath
    
    # Test the command
    Write-Host "Testing bckl command..." -ForegroundColor Cyan
    bckl --version
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nSuccess! Package installed and basic command works." -ForegroundColor Green
    } else {
        Write-Host "`nError: Command failed with exit code $LASTEXITCODE" -ForegroundColor Red
    }
    
    # Deactivate the virtual environment
    deactivate
} 
catch {
    Write-Error "Error: $_"
} 
finally {
    # Clean up
    Write-Host "Cleaning up test environment..." -ForegroundColor Cyan
    Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}
