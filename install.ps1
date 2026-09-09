$ErrorActionPreference = "Stop"

Write-Host "Installing Alenia Fuse for Windows via Python..." -ForegroundColor Cyan

# Check if Python is installed
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH. Please install Python 3.11+ before proceeding."
}

Write-Host "Installing Alenia Fuse..."
python -m pip install -e .

Write-Host "Alenia Fuse installed successfully!" -ForegroundColor Green
Write-Host "You can now run 'fuse' from the command line."
