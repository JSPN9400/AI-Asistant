# Mobile Companion

This folder now contains a lightweight Android starter for a "lite APK" approach.

## Why This Approach

The mobile app should stay thin:

- no on-device AI models
- no heavy local processing
- uses the hosted web app and cloud API
- optional phone features like file upload and camera capture through Android WebView

This matches the low-spec product direction better than bundling a full mobile framework plus local AI runtime.

## Project Type

- Native Android
- Kotlin
- WebView shell

## What It Does

- loads the hosted workplace app URL
- supports file chooser from the phone
- allows future voice and camera capture integration
- keeps APK size small compared with a full embedded assistant runtime

## Before Building

Edit this value in:

- `app/build.gradle.kts`

Set:

```kotlin
buildConfigField("String", "WEB_APP_URL", "\"https://your-app.onrender.com/\"")
```

Replace it with your real hosted URL.

## Build In Android Studio

1. Open `frontend/mobile_companion` in Android Studio.
2. Let Gradle sync.
3. Update `WEB_APP_URL`.
4. Build debug APK:

```text
Build > Build Bundle(s) / APK(s) > Build APK(s)
```

## Output

Android Studio will generate:

- debug APK for testing
- release APK or AAB after signing setup

## Recommended Use

- Render hosts the backend and web app
- This APK acts as the mobile companion shell
- APK distribution can be done via GitHub Releases, Firebase App Distribution, or Play internal testing
