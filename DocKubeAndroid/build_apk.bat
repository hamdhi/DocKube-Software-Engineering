@echo off
REM Builds the DocKube Android APK.
REM   The release APK is published to the 'android-latest' GitHub release,
REM   not copied to the desktop app's dist folder.
REM
REM Everything is installed locally, so Android Studio is not needed:
REM   C:\Android\Sdk     - platform android-36, build-tools 36.0.0
REM   C:\Android\gradle  - Gradle 8.14.3
REM
REM Usage:
REM   build_apk.bat            debug APK
REM   build_apk.bat release    release APK
REM   (published to the android-latest GitHub release)
REMsetlocal

set "JAVA_HOME=C:\JDK 17"
set "ANDROID_HOME=C:\Android\Sdk"
set "ANDROID_SDK_ROOT=C:\Android\Sdk"
set "GRADLE=C:\Android\gradle\dist\gradle-8.14.3\bin\gradle.bat"

cd /d "%~dp0"

if "%1"=="release" (
    echo Building the release APK...
    "%GRADLE%" --no-daemon assembleRelease
) else (
    echo Building the debug APK...
    "%GRADLE%" --no-daemon assembleDebug
)

if errorlevel 1 (
    echo.
    echo BUILD FAILED
    exit /b 1
)

echo.
echo APKs produced:
dir /b "app\build\outputs\apk\*\*.apk"
echo.
echo Install on the phone over USB:
echo     C:\Android\Sdk\platform-tools\adb install -r app\build\outputs\apk\debug\app-debug.apk
endlocal
