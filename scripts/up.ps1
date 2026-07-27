$ErrorActionPreference = "Stop"

Set-Location "$PSScriptRoot\.."

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example — set EXTERNAL_API_BASE_URL and X_CANDIDATE_ID"
}

Write-Host "==> docker compose up --build -d"
docker compose up --build -d

Write-Host "==> waiting for /ready"
$deadline = (Get-Date).AddMinutes(3)
do {
    Start-Sleep -Seconds 3
    try {
        $ready = curl.exe -fsS http://localhost:8080/ready 2>$null
        if ($LASTEXITCODE -eq 0 -and $ready -match '"status"\s*:\s*"ready"') {
            Write-Host $ready
            Write-Host "OK: stack is ready"
            Write-Host "UI:      http://localhost:8080"
            Write-Host "Swagger: http://localhost:8080/docs"
            Write-Host "RabbitMQ: http://localhost:15672 (dws / dws_secret)"
            exit 0
        }
    } catch {
        # keep waiting
    }
} while ((Get-Date) -lt $deadline)

Write-Host "ERROR: stack did not become ready in time"
docker compose ps
docker compose logs api --tail=50
exit 1
