# Build script for backlog-cli
# Generates source distribution and wheel packages

# Ensure we're in the project root
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

# Clean previous builds
$DistDir = Join-Path $ProjectRoot "dist"
if (Test-Path $DistDir) {
    Write-Host "Cleaning previous builds..." -ForegroundColor Cyan
    Remove-Item -Path $DistDir -Recurse -Force
}

# Build package
Write-Host "Building package..." -ForegroundColor Cyan
python -m build

Write-Host "`nBuild complete! Distribution files in ./dist/" -ForegroundColor Green
Get-ChildItem -Path $DistDir | ForEach-Object {
    Write-Host "- $($_.Name)" -ForegroundColor White
}

Write-Host "`nTo install locally for testing:" -ForegroundColor Cyan
Write-Host "pip install --force-reinstall $DistDir\*.whl" -ForegroundColor Yellow
