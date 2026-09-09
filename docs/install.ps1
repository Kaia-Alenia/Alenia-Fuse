$ErrorActionPreference = "Stop"

if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    throw "Python 3.11+ is required."
}

python -m pip install alenia-fuse
Write-Host "Installation complete. Run: fuse --help" -ForegroundColor Green
