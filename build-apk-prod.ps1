# Build Flutter APK in prod flavor (for store/production)
# Usage: .\build-apk-prod.ps1

$flutterPath = "$env:USERPROFILE\scoop\apps\flutter\current\bin\flutter.bat"

# Determine app directory (works whether script is in root or app folder)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Test-Path "$scriptDir\pubspec.yaml") {
    $appDir = $scriptDir
} else {
    $appDir = "$scriptDir\app"
}

Set-Location $appDir

Write-Host "⚠️  Building PRODUCTION APK" -ForegroundColor Yellow
Write-Host "This will create a release build for the Play Store" -ForegroundColor Yellow
Write-Host ""

Write-Host "🧹 Cleaning build..." -ForegroundColor Cyan
& $flutterPath clean

Write-Host "📦 Getting dependencies..." -ForegroundColor Cyan
& $flutterPath pub get

Write-Host "🏗️  Building production APK..." -ForegroundColor Cyan
& $flutterPath build apk --flavor prod -v

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Production APK build successful!" -ForegroundColor Green
    Write-Host "📍 Location: build/app/outputs/flutter-apk/app-prod-release.apk" -ForegroundColor Green
    Write-Host "⚠️  Remember to sign the APK before uploading to Play Store!" -ForegroundColor Yellow
} else {
    Write-Host "❌ Build failed" -ForegroundColor Red
    exit 1
}
