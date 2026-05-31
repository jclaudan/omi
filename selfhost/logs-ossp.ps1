#!/usr/bin/env pwsh
<#
.SYNOPSIS
    View Omi OSS+ service logs
.DESCRIPTION
    Shows logs from all OSS+ services or a specific service
.PARAMETER Service
    Service name to show logs for (supabase, qdrant, minio, faster-whisper, ollama, redis)
.PARAMETER Lines
    Number of lines to show (default: 100)
.PARAMETER Follow
    Follow log output (like 'tail -f')
.EXAMPLE
    .\logs-ossp.ps1
    .\logs-ossp.ps1 -Service supabase
    .\logs-ossp.ps1 -Service ollama -Follow
    .\logs-ossp.ps1 -Lines 50
#>

param(
    [string]$Service = "",
    [int]$Lines = 100,
    [switch]$Follow = $false,
    [switch]$Help = $false
)

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Full
    exit 0
}

$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if Docker is installed
try {
    docker --version > $null 2>&1
} catch {
    Write-Host "[ERROR] Docker not found" -ForegroundColor Red
    exit 1
}

# List of services
$services = @(
    "omi-supabase",
    "omi-qdrant",
    "omi-minio",
    "omi-faster-whisper",
    "omi-ollama",
    "omi-redis"
)

# Build command
$cmd = @("docker", "compose", "-f", "$scriptPath/docker-compose.yml", "logs")

if ($Service) {
    # Validate service name
    $validService = $services | Where-Object { $_ -like "*$Service*" } | Select-Object -First 1
    if (-not $validService) {
        Write-Host "[ERROR] Unknown service: $Service" -ForegroundColor Red
        Write-Host "Available services:" -ForegroundColor Yellow
        $services | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
        exit 1
    }
    Write-Host "[INFO] Logs for $validService" -ForegroundColor Cyan
    $cmd += $validService
} else {
    Write-Host "[INFO] Logs for all services (press Ctrl+C to exit)" -ForegroundColor Cyan
}

# Add options
if ($Follow) {
    $cmd += "-f"
} else {
    $cmd += "--tail=$Lines"
}

# Add timestamp
$cmd += "-t"

# Execute
& $cmd[0] $cmd[1..($cmd.Length - 1)]
