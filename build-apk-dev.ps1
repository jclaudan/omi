# Build Flutter APK in dev flavor
# Usage: .\build-apk-dev.ps1

$flutterPath = "$env:USERPROFILE\scoop\apps\flutter\current\bin\flutter.bat"

# Determine app directory (works whether script is in root or app folder)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Test-Path "$scriptDir\pubspec.yaml") {
    $appDir = $scriptDir
} else {
    $appDir = "$scriptDir\app"
}

Set-Location $appDir

Write-Host "🧹 Cleaning build..." -ForegroundColor Cyan
& $flutterPath clean

Write-Host "📦 Building dev APK..." -ForegroundColor Cyan
& $flutterPath pub get

& $flutterPath build apk --flavor dev

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ APK build successful!" -ForegroundColor Green
    Write-Host "📍 Location: build/app/outputs/flutter-apk/app-dev-release.apk" -ForegroundColor Green
} else {
    Write-Host "❌ Build failed" -ForegroundColor Red
    exit 1
}
