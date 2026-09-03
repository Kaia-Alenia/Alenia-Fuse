$ErrorActionPreference = "Stop"

Write-Host "Installing Alenia Porter for Windows via Go..." -ForegroundColor Cyan

# Check if Go is installed
if (-not (Get-Command "go" -ErrorAction SilentlyContinue)) {
    Write-Error "Go is not installed or not in PATH. Please install Go from https://golang.org/dl/ before proceeding."
}

Write-Host "Compiling and installing Alenia Porter from source..."
if (Test-Path ".\cmd\porter") {
    go install .\cmd\porter
} else {
    go install github.com/Kaia-Alenia/Alenia-Porter/cmd/porter@latest
}

$goBinPath = Join-Path $env:USERPROFILE "go\bin"

$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notmatch [regex]::Escape($goBinPath)) {
    Write-Host "Adding $goBinPath to user PATH..."
    [Environment]::SetEnvironmentVariable("PATH", "$userPath;$goBinPath", "User")
    Write-Host "You may need to restart your terminal for the PATH changes to take effect." -ForegroundColor Yellow
}

Write-Host "Alenia Porter installed successfully!" -ForegroundColor Green
Write-Host "You can now run 'porter' from the command line."
