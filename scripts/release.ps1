param (
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [switch]$TestPyPI,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipTests
)

# Ensure we're in the project root
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

# Verify version format
if (-not ($Version -match "^\d+\.\d+\.\d+$")) {
    Write-Error "Version must be in format X.Y.Z"
    exit 1
}

# Run tests if not skipped
if (-not $SkipTests) {
    Write-Host "Running test suite..." -ForegroundColor Cyan
    pytest -m "not integration" --cov=backlog_cli --cov-report=term
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Tests failed! Fix issues before releasing."
        exit 1
    }
}

# Update version in pyproject.toml
$PyProjectPath = Join-Path $ProjectRoot "pyproject.toml"
$PyProject = Get-Content $PyProjectPath -Raw
$PyProject = $PyProject -replace 'version = "\d+\.\d+\.\d+"', "version = `"$Version`""
Set-Content -Path $PyProjectPath -Value $PyProject

# Clean previous builds
$DistDir = Join-Path $ProjectRoot "dist"
if (Test-Path $DistDir) {
    Write-Host "Cleaning previous builds..." -ForegroundColor Cyan
    Remove-Item -Path $DistDir -Recurse -Force
}

# Build package
Write-Host "Building package..." -ForegroundColor Cyan
python -m build

# Upload to TestPyPI or PyPI
if ($TestPyPI) {
    Write-Host "Uploading to TestPyPI..." -ForegroundColor Cyan
    python -m twine upload --repository testpypi dist/*
} else {
    Write-Host "Ready to upload to PyPI. Run the following command:" -ForegroundColor Green
    Write-Host "python -m twine upload dist/*" -ForegroundColor Yellow
}

# Create git tag
Write-Host "Creating git tag v$Version..." -ForegroundColor Cyan
git tag -a "v$Version" -m "Release v$Version"

Write-Host "`nRelease v$Version prepared!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Push the tag: git push origin v$Version" -ForegroundColor White
Write-Host "2. Create a GitHub release with the same tag" -ForegroundColor White
if (-not $TestPyPI) {
    Write-Host "3. Upload to PyPI with: python -m twine upload dist/*" -ForegroundColor White
}
