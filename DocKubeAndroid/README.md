# DocKube Mobile

The phone companion to the DocKube desktop app. It is a **reference**, not a
tool: it holds every command from the desktop app and the whole Learning Centre,
so you can look things up and copy commands to your clipboard. It deliberately
does not try to run Docker or Kubernetes. All of that content ships inside the
APK, so it works with no network at all.

The one exception is the **Update** button, which checks GitHub for a newer
build. That is the app's only internet access, and it runs only when you tap
the button.

## Install

Copy the APK to the phone and tap it. You will be asked to allow installs from
that file manager the first time.

The APK is debug-signed, which is fine for sideloading. For Play Store you would
replace `signingConfig` in `app/build.gradle.kts` with a real keystore.

## Build

    build_apk.bat            debug APK
    build_apk.bat release    release APK

Output lands in `app\build\outputs\apk\`.

Requires `JAVA_HOME=C:\JDK 17`, the SDK at `C:\Android\Sdk` and Gradle at
`C:\Android\gradle`. Android Studio is not needed.

## Keeping the content in sync with the desktop app

The command list is not typed in by hand. `export_android_content.py` in the
parent folder builds the real desktop app, swaps its panel builders for
recorders, selects all 20 categories, and writes out whatever buttons the
desktop app would have drawn:

    cd ..
    python export_android_content.py
    copy android_content.json DocKubeAndroid\app\src\main\assets\android_content.json
    cd DocKubeAndroid
    build_apk.bat

`test_android_content.py` checks the result and fails if the packaged copy is
stale, so a mismatch cannot ship unnoticed.

## Layout

    app/src/main/assets/android_content.json   all content, generated
    app/src/main/java/com/dockeybe/mobile/
        MainActivity.kt          entry point, loads content off the main thread
        data/Models.kt           content model
        data/ContentRepository.kt JSON parsing
        ui/HomeScreen.kt         categories
        ui/CategoryScreen.kt     commands, tap to copy or share
        ui/SearchScreen.kt       search across every command
        ui/LearningScreen.kt     chapter list and the HTML reader
        ui/Theme.kt              DocKube's dark palette

## Why chapters are a WebView

The Learning Centre is full of comparison tables. Rendered as Compose text they
collapse into unreadable walls on a narrow screen, so the chapters are the same
HTML the desktop app shows, styled to match. JavaScript is disabled and the
WebView is barred from file and content access.