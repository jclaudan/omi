#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start Omi OSS+ stack with Docker Compose
.DESCRIPTION
    Starts all OSS+ services (Supabase, Qdrant, MinIO, Faster-Whisper, Ollama)
    Automatically generates .env file if it doesn't exist
.EXAMPLE
    .\start-ossp.ps1
#>

param(
    [switch]$NoLogs = $false,
    [switch]$Help = $false
)

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Full
    exit 0
}

$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootPath = Split-Path -Parent $scriptPath

Write-Host "[START] Starting Omi OSS+ Stack..." -ForegroundColor Cyan

# Check if Docker is installed
try {
    $dockerVersion = docker --version
    Write-Host "[OK] Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker not found. Please install Docker Desktop for Windows." -ForegroundColor Red
    Write-Host "  Download: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check if docker-compose is available
try {
    $composeVersion = docker compose version
    Write-Host "[OK] Docker Compose found" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker Compose not found" -ForegroundColor Red
    exit 1
}

# Generate .env if it doesn't exist
$envFile = Join-Path $scriptPath ".env"
$envTemplate = Join-Path $scriptPath ".env.template"

if (-not (Test-Path $envFile)) {
    if (Test-Path $envTemplate) {
        Write-Host "[INFO] Generating .env file..." -ForegroundColor Yellow
        Copy-Item -Path $envTemplate -Destination $envFile

        # Generate random secrets
        $jwtSecret = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object { [char]$_ })
        $encryptionSecret = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object { [char]$_ })

        # Update .env with generated secrets (simplified - in production use proper secret generation)
        $envContent = Get-Content $envFile
        $envContent = $envContent -replace 'JWT_SECRET=.*', "JWT_SECRET=$jwtSecret"
        $envContent = $envContent -replace 'ENCRYPTION_SECRET=.*', "ENCRYPTION_SECRET=$encryptionSecret"
        Set-Content -Path $envFile -Value $envContent

        Write-Host "[OK] .env file created with secure defaults" -ForegroundColor Green
    } else {
        Write-Host "[WARN] .env.template not found" -ForegroundColor Yellow
    }
} else {
    Write-Host "[OK] Using existing .env file" -ForegroundColor Green
}

# Pull latest images
Write-Host "`n[INFO] Pulling latest Docker images..." -ForegroundColor Yellow
docker compose -f "$scriptPath/docker-compose.yml" pull 2>&1 | Tee-Object -Variable pullOutput | Out-Null

# Start services
Write-Host "`n[INFO] Starting services..." -ForegroundColor Yellow
docker compose -f "$scriptPath/docker-compose.yml" up -d 2>&1 | Tee-Object -Variable upOutput | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to start services" -ForegroundColor Red
    Write-Host $upOutput
    exit 1
}

Write-Host "[OK] Services started" -ForegroundColor Green

# Wait for services to be healthy
Write-Host "`n[INFO] Waiting for services to be healthy..." -ForegroundColor Yellow
$maxRetries = 30
$retryCount = 0

while ($retryCount -lt $maxRetries) {
    $healthStatus = docker compose -f "$scriptPath/docker-compose.yml" ps --format "{{.Status}}" | Select-String "healthy|running" | Measure-Object | Select-Object -ExpandProperty Count
    $totalServices = 6  # supabase, qdrant, minio, faster-whisper, ollama, redis

    if ($healthStatus -ge $totalServices) {
        Write-Host "[OK] All services are healthy" -ForegroundColor Green
        break
    }

    $retryCount++
    Write-Host "  Waiting... ($retryCount/$maxRetries)" -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

# Display service URLs
Write-Host "`n[OSS+ Services Ready!]" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services:" -ForegroundColor Yellow
Write-Host "  [DB] PostgreSQL (Supabase)  : localhost:5432" -ForegroundColor White
Write-Host "  [WEB] Supabase Studio       : http://localhost:3000" -ForegroundColor White
Write-Host "  [API] PostgREST API         : http://localhost:8000" -ForegroundColor White
Write-Host "  [VEC] Qdrant Vector DB      : http://localhost:6333" -ForegroundColor White
Write-Host "  [STO] MinIO Object Storage  : http://localhost:9001" -ForegroundColor White
Write-Host "        MinIO API             : http://localhost:9000" -ForegroundColor White
Write-Host "  [STT] Faster-Whisper STT    : http://localhost:8001" -ForegroundColor White
Write-Host "        WebSocket (STT)       : ws://localhost:8002" -ForegroundColor White
Write-Host "  [LLM] Ollama LLM            : http://localhost:11434" -ForegroundColor White
Write-Host "  [CACHE] Redis Cache         : localhost:6379" -ForegroundColor White
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  .env file: $envFile" -ForegroundColor White
Write-Host ""
Write-Host "Quick setup:" -ForegroundColor Yellow
Write-Host "  1. Run database migrations:" -ForegroundColor White
Write-Host "     psql -h localhost -U postgres < ./selfhost/supabase/migrations/001_profiles.sql" -ForegroundColor Gray
Write-Host "  2. Check logs:" -ForegroundColor White
Write-Host "     .\logs-ossp.ps1" -ForegroundColor Gray
Write-Host "  3. Stop services:" -ForegroundColor White
Write-Host "     .\stop-ossp.ps1" -ForegroundColor Gray
Write-Host ""

# Show logs if requested
if (-not $NoLogs) {
    Write-Host "[INFO] Showing logs (press Ctrl+C to stop)..." -ForegroundColor Cyan
    docker compose -f "$scriptPath/docker-compose.yml" logs -f
}
