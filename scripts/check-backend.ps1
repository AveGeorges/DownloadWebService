# Backend local smoke checks (PowerShell)
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\..\backend"

if (-not (Test-Path .venv)) {
    python -m venv .venv
}

.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]" | Out-Null

Write-Host "==> ruff check"
ruff check src tests
Write-Host "==> ruff format --check"
ruff format --check src tests
Write-Host "==> pytest + coverage"
pytest -q

Write-Host "OK: backend checks passed"
