$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\.."
docker compose down
Write-Host "OK: stack stopped"
