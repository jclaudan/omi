# Install and run Flutter APK in dev flavor on connected device
# Usage: .\run-apk-dev.ps1

$flutterPath = "$env:USERPROFILE\scoop\apps\flutter\current\bin\flutter.bat"

# Determine app directory (works whether script is in root or app folder)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Test-Path "$scriptDir\pubspec.yaml") {
    $appDir = $scriptDir
} else {
    $appDir = "$scriptDir\app"
}

$apkPath = "$appDir\build\app\outputs\flutter-apk\app-dev-release.apk"

Write-Host "📱 Checking for connected devices..." -ForegroundColor Cyan
& $flutterPath devices

Write-Host ""
if (-not (Test-Path $apkPath)) {
    Write-Host "❌ APK not found at $apkPath" -ForegroundColor Red
    Write-Host "💡 Run build-apk-dev.ps1 first to build the APK" -ForegroundColor Yellow
    exit 1
}

Write-Host "📦 Installing APK to device..." -ForegroundColor Cyan
adb install -r $apkPath

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ APK installed successfully!" -ForegroundColor Green
    Write-Host "🚀 Launching app..." -ForegroundColor Cyan
    adb shell am start -n com.friend.ios.dev/com.friend.ios.MainActivity
    Write-Host "✅ App launched!" -ForegroundColor Green
} else {
    Write-Host "❌ Installation failed" -ForegroundColor Red
    exit 1
}
