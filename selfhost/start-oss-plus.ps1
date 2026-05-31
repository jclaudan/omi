# Start OSS+ Stack with or without Cloudflare Tunnel
# Usage: .\start-oss-plus.ps1 [local|tunnel]

param(
    [string]$mode = "local"
)

$selfhostDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $selfhostDir

Write-Host "================================" -ForegroundColor Cyan
Write-Host "[*] OSS+ Self-Hosted Stack" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env.selfhosted exists
if (-not (Test-Path ".env.selfhosted")) {
    Write-Host "[!] .env.selfhosted file not found!" -ForegroundColor Red
    Write-Host "[*] Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env.selfhosted"
    Write-Host "[+] Created .env.selfhosted - please edit it with your settings" -ForegroundColor Green
    Write-Host ""
    Write-Host "Edit .env.selfhosted and run again:" -ForegroundColor Cyan
    Write-Host "  notepad .env.selfhosted" -ForegroundColor Gray
    exit 1
}

Write-Host "[*] Starting services in mode: $mode" -ForegroundColor Cyan
Write-Host ""

if ($mode -eq "tunnel") {
    # With Cloudflare Tunnel
    Write-Host "[*] Starting with Cloudflare Tunnel..." -ForegroundColor Yellow
    Write-Host "[!] This may take 30-60 seconds to establish connection" -ForegroundColor Yellow
    Write-Host ""

    $token = (Get-Content .env.selfhosted | Select-String "CLOUDFLARE_TUNNEL_TOKEN=" | ForEach-Object { $_ -replace "CLOUDFLARE_TUNNEL_TOKEN=", "" }).ToString().Trim()

    if ([string]::IsNullOrEmpty($token)) {
        Write-Host "[!] CLOUDFLARE_TUNNEL_TOKEN not set in .env.selfhosted!" -ForegroundColor Red
        Write-Host "[*] Add your token to .env.selfhosted and try again" -ForegroundColor Yellow
        exit 1
    }

    docker compose --profile tunnel up -d

    Write-Host ""
    Write-Host "[+] Services starting..." -ForegroundColor Green
    Write-Host ""
    Write-Host "[*] Tunnel Status:" -ForegroundColor Cyan
    Write-Host "  Run: docker logs omi-cloudflare-tunnel" -ForegroundColor Gray
    Write-Host ""
    Write-Host "[*] Services:" -ForegroundColor Cyan
    Write-Host "  - PostgREST API: http://localhost:8000" -ForegroundColor Gray
    Write-Host "  - MinIO Console: http://localhost:9001" -ForegroundColor Gray
    Write-Host "  - Qdrant: http://localhost:6333" -ForegroundColor Gray
    Write-Host "  - Ollama: http://localhost:11434" -ForegroundColor Gray
    Write-Host "  - Redis: localhost:6379" -ForegroundColor Gray

} else {
    # Local IP only (default)
    Write-Host "[*] Starting with Local IP access only" -ForegroundColor Yellow
    Write-Host ""

    docker compose up -d

    Write-Host ""
    Write-Host "[+] All services started!" -ForegroundColor Green
    Write-Host ""

    # Get local IP
    $localIP = (Get-NetIPAddress -AddressFamily IPv4 -PrefixOrigin Dhcp, Manual | Select-Object -First 1).IPAddress

    Write-Host "[*] Access Points:" -ForegroundColor Cyan
    Write-Host "  - API (local): http://localhost:8000" -ForegroundColor Gray
    Write-Host "  - API (network): http://$localIP`:8000" -ForegroundColor Gray
    Write-Host "  - MinIO Console: http://localhost:9001" -ForegroundColor Gray
    Write-Host "  - Qdrant: http://localhost:6333" -ForegroundColor Gray
    Write-Host "  - Ollama: http://localhost:11434" -ForegroundColor Gray
    Write-Host "  - Redis: localhost:6379" -ForegroundColor Gray
    Write-Host ""
    Write-Host "[*] Use $localIP`:8000 for API_BASE_URL in Flutter app" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[*] View logs:" -ForegroundColor Cyan
Write-Host "  docker compose logs -f postgrest" -ForegroundColor Gray
Write-Host ""
Write-Host "[*] Stop services:" -ForegroundColor Cyan
Write-Host "  docker compose down" -ForegroundColor Gray
Write-Host ""
