# Complete workflow: Clean, Build, and Run dev APK
# Usage: .\build-and-run-dev.ps1

$flutterPath = "$env:USERPROFILE\scoop\apps\flutter\current\bin\flutter.bat"

# Determine app directory (works whether script is in root or app folder)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Test-Path "$scriptDir\pubspec.yaml") {
    $appDir = $scriptDir
} else {
    $appDir = "$scriptDir\app"
}

Set-Location $appDir

Write-Host "================================" -ForegroundColor Cyan
Write-Host "🚀 COMPLETE DEV APK BUILD & RUN" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Clean
Write-Host "[1/4] 🧹 Cleaning build..." -ForegroundColor Cyan
& $flutterPath clean
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Clean failed"; exit 1 }

# Step 2: Get dependencies
Write-Host "[2/4] 📦 Getting dependencies..." -ForegroundColor Cyan
& $flutterPath pub get
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Pub get failed"; exit 1 }

# Step 3: Build APK
Write-Host "[3/4] 🏗️  Building APK..." -ForegroundColor Cyan
& $flutterPath build apk --flavor dev
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Build failed"; exit 1 }

# Step 4: Install and run
Write-Host "[4/4] 📱 Installing and running..." -ForegroundColor Cyan
$apkPath = "$appDir\build\app\outputs\flutter-apk\app-dev-release.apk"

if (-not (Test-Path $apkPath)) {
    Write-Host "❌ APK not found" -ForegroundColor Red
    exit 1
}

adb install -r $apkPath
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Install failed"; exit 1 }

adb shell am start -n com.friend.ios.dev/com.friend.ios.MainActivity

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "✅ SUCCESS! App is running!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
