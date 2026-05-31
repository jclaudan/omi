#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Stop Omi OSS+ stack
.DESCRIPTION
    Stops all OSS+ services gracefully
    Use -Remove to also delete volumes and data
.EXAMPLE
    .\stop-ossp.ps1
    .\stop-ossp.ps1 -Remove
#>

param(
    [switch]$Remove = $false,
    [switch]$Help = $false
)

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Full
    exit 0
}

$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "[STOP] Stopping Omi OSS+ Stack..." -ForegroundColor Cyan

# Check if Docker is installed
try {
    docker --version > $null 2>&1
} catch {
    Write-Host "[ERROR] Docker not found" -ForegroundColor Red
    exit 1
}

# Stop services
if ($Remove) {
    Write-Host "[INFO] Removing containers and volumes..." -ForegroundColor Yellow
    Write-Host "[WARN] WARNING: This will delete all data!" -ForegroundColor Red

    $confirmation = Read-Host "Are you sure? Type 'yes' to confirm"
    if ($confirmation -ne "yes") {
        Write-Host "Cancelled" -ForegroundColor Yellow
        exit 0
    }

    docker compose -f "$scriptPath/docker-compose.yml" down -v
    Write-Host "[OK] Containers and volumes removed" -ForegroundColor Green
} else {
    Write-Host "[INFO] Stopping services..." -ForegroundColor Yellow
    docker compose -f "$scriptPath/docker-compose.yml" down
    Write-Host "[OK] Services stopped" -ForegroundColor Green
    Write-Host ""
    Write-Host "Tip: Use .\stop-ossp.ps1 -Remove to also delete volumes and data" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[OK] OSS+ Stack stopped" -ForegroundColor Green
