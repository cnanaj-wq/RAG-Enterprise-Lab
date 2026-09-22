$ErrorActionPreference = "Stop"
Write-Host "RAG Enterprise Lab - Phase 0 bootstrap"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ".env created from .env.example"
}

if (-not (Test-Path ".venv")) {
    py -3.12 -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"

Write-Host "Bootstrap complete."
Write-Host "Docling was NOT installed locally."
Write-Host "Run: .\.venv\Scripts\python.exe -m pytest"
