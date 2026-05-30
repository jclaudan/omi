# Omi OSS+ Android APK Build Status

**Date**: 2026-05-30  
**Branch**: `feat/use-only-opensource-alternative`  
**Status**: 🟡 In Progress - Build Environment Ready, Flutter Compatibility Issue Blocking

## Completed Work

### 1. ✅ Flutter Installation
- Flutter SDK 3.44.0 successfully installed via Scoop
- Dart SDK compatible
- Android toolchain configured (Android SDK 36.0.0)

### 2. ✅ Project Dependencies Resolved
- `flutter pub get` completed successfully
- Fixed whisper_flutter_new encoding issue:
  - Changed Git ref from `684fb437` to `af6b457c` (includes pubspec.yaml UTF-8 fix)
  - Eliminates "Unexpected character" error during dependency resolution
  
### 3. ✅ Flutter Code Generation
- `dart run build_runner build` completed (131 seconds)
  - Generated 14 output files
  - 100+ .g.dart files regenerated
  - Asset and font generation successful
  
- `flutter gen-l10n` completed
  - Generated localizations for 49 languages

### 4. ✅ Build Configuration
- Keystore configured: `android/key.properties` copied
- Firebase dev config installed: `lib/firebase_options_dev.dart`
- Google services JSON configured: `android/app/src/dev/google-services.json`

### 5. ✅ Code Fixes
- Fixed missing import in `lib/pages/onboarding/oss_plus/step_test.dart`
  - Added: `import 'package:omi/backend/preferences.dart';`
  - Resolved SharedPreferencesUtil compilation error

## Current Blocker: Flutter/font_awesome_flutter Compatibility

### Problem
Flutter 3.44.0 made `IconData` class final (breaking change).
The project's `font_awesome_flutter` dependency (v10.8.0 - v10.12.0) attempts to extend this final class, causing compilation errors:

```
Error: The class 'IconData' can't be extended outside of its library because it's a final class.
```

### Why This Happened
- Project specifies Flutter 3.35.3 as requirement (see `app/setup.sh`)
- Scoop package manager only provides Flutter 3.44.0
- font_awesome_flutter hasn't been updated to support Flutter 3.44.0

### Solution Options (in order of preference)

**Option 1: Use Flutter 3.35.3 (Recommended)**
```bash
# Manual installation from official Flutter channels
flutter version management --switch 3.35.3
```
- Requires downloading Flutter from https://flutter.dev/docs/development/tools/sdk/releases
- Would be compatible with existing font_awesome_flutter

**Option 2: Use Compatible Fork**
```yaml
font_awesome_flutter:
  git:
    url: https://github.com/fluttercommunity/font_awesome_flutter.git
    ref: master
```
- ✅ Resolves the final class issue  
- ❌ Requires fixing type mismatch (FaIconData vs IconData) across multiple files
- ~15 type correction errors in pages/settings and other UI files

**Option 3: Downgrade to Older Flutter**
- Would require Scoop or manual setup of Flutter 3.24 or earlier
- Not recommended - misaligned with project goals

## To Complete APK Build

### Immediate Next Steps
1. Install Flutter 3.35.3:
   ```bash
   # Option A: Manual installation
   curl -L https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.35.3-stable.zip -o flutter_3.35.3.zip
   unzip flutter_3.35.3.zip
   set PATH=path/to/flutter_3.35.3/bin:%PATH%
   
   # Option B: Using FVM (Flutter Version Manager)
   fvm install 3.35.3
   fvm use 3.35.3
   ```

2. Verify Flutter downgrade:
   ```bash
   flutter doctor
   flutter --version  # Should show 3.35.3
   ```

3. Clean and rebuild:
   ```bash
   flutter clean
   flutter pub get
   dart run build_runner build --delete-conflicting-outputs
   flutter gen-l10n
   ```

4. Build APK:
   ```bash
   flutter build apk --flavor dev
   # APK output: app/build/app/outputs/flutter-apk/app-dev-release.apk
   ```

### Alternative: Fix type mismatch with master branch
If Flutter version management is problematic, use fluttercommunity's fork and fix ~15 type mismatches:
- Replace `IconData` with `FaIconData` or add type converters
- Update `FaIcon` usage to expect `FaIconData`
- ~2-3 hours estimated effort

## Environment Setup Summary

| Component | Status | Version |
|-----------|--------|---------|
| Flutter | ✅ Installed | 3.44.0 (3.35.3 needed) |
| Dart | ✅ Working | 3.5.3 |
| Android SDK | ✅ Ready | API 36 |
| Android Gradle Plugin | ✅ Present | 8.10.1 |
| Java/JDK | ✅ Available | 17.0.x |
| Kotlin | ✅ Present | 2.1.0 |

## OSS+ APK Features (When Built)
When successfully built, the APK will include:
- ✅ Mode selector (Cloud/OSS+) on first launch
- ✅ OSS+ configuration wizard
- ✅ Supabase authentication routing
- ✅ Backend service health checks (via step_test.dart)
- ✅ All database/vector/storage backends routed for OSS+
- ✅ Encrypted messaging with AES-256-GCM
- ✅ Full localization (49 languages)

## Git Commit
Changes committed to `feat/use-only-opensource-alternative`:
```
9075c54b3 fix(app): resolve whisper_flutter_new encoding and step_test imports
```

## Next Session Recommendations
1. Priority: Resolve Flutter version issue (prefer Flutter 3.35.3 installation)
2. Once Flutter is correct, run `flutter build apk --flavor dev` to generate the APK
3. Test APK on Android device/emulator with OSS+ backend services running
4. Update Android dependencies if needed (AGP 8.11.1+ and Kotlin 2.2.20+ preferred per warnings)
