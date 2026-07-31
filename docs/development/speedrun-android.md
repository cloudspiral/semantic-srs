# Speedrun Android development

This branch is a local Android companion prototype for the Speedrun project. It
reuses Anki's Rust scheduling engine and adds a native dashboard to AnkiDroid's
Statistics screen. The dashboard calls the Rust `topic_mastery` RPC through the
Android backend rather than reimplementing topic aggregation in Kotlin.

## Local checkout layout

The verified setup uses these sibling repositories:

```text
tmp/
├── Anki-Android/          # this repository, branch speedrun-mobile
└── Anki-Android-Backend/  # branch speedrun-backend
    └── anki/              # pinned Anki core, branch speedrun-topic-mastery
```

`Anki-Android-Backend/anki` contains the same read-only topic-mastery Rust
implementation used by the desktop prototype, ported onto the Anki revision
pinned by the Android backend.

## Prerequisites

The verified macOS setup uses Android Studio's bundled JBR, Android SDK 36,
build tools 35 and 36, NDK 29.0.14206865, and an ARM64 Android 15 emulator.
The AVD is named `Speedrun_Pixel_8_API_35`.

Start the emulator with Android Studio's Device Manager or:

```sh
$ANDROID_HOME/emulator/emulator -avd Speedrun_Pixel_8_API_35
```

## Build the Rust Android backend

From `tmp/Anki-Android-Backend`:

```sh
env \
  JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" \
  ANDROID_HOME="$HOME/Library/Android/sdk" \
  ANDROID_SDK_ROOT="$HOME/Library/Android/sdk" \
  ANDROID_NDK_HOME="$HOME/Library/Android/sdk/ndk/29.0.14206865" \
  YARN_RC_FILENAME=.yarnrc-android.yml \
  PATH="$HOME/.cargo/bin:/opt/homebrew/opt/rustup/bin:/opt/homebrew/bin:$HOME/Library/Android/sdk/cmdline-tools/latest/bin:$HOME/Library/Android/sdk/platform-tools:/usr/bin:/bin" \
  ./build.sh
```

The build emits `rsdroid/build/outputs/aar/rsdroid-release.aar`, including an
ARM64 `librsdroid.so`. The build explicitly uses the protobuf compiler bundled
by the pinned Anki checkout so generated Java stays compatible with the
backend's protobuf runtime.

## Build and install AnkiDroid

Set `local.properties` in this repository:

```properties
sdk.dir=/Users/matt/Library/Android/sdk
local_backend=true
```

Then build and install the ARM64 Play debug APK:

```sh
env \
  JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" \
  ANDROID_HOME="$HOME/Library/Android/sdk" \
  ANDROID_SDK_ROOT="$HOME/Library/Android/sdk" \
  ./gradlew :AnkiDroid:assemblePlayDebug

$ANDROID_HOME/platform-tools/adb install -r \
  AnkiDroid/build/outputs/apk/play/debug/AnkiDroid-play-arm64-v8a-debug.apk
```

Open AnkiDroid, complete the disposable local onboarding if needed, open the
navigation drawer, and choose **Statistics**. The `Speedrun · MCAT` card appears
above the existing Anki statistics view.

## Current evidence boundary

Verified locally on the ARM64 emulator:

- the Android APK packages and loads the locally built Rust backend;
- Kotlin calls the generated `topicMastery("mcat", 0.9f)` API;
- the dashboard renders Rust-computed tag, FSRS-memory-state, and topic counts;
- zero data and missing memory state abstain instead of presenting a false
  recall estimate;
- performance and readiness remain separate from memory and visibly abstain.

This prototype does not yet implement the full product claim. It still needs
real account sync/reconciliation tests, the held-back exam performance model,
the official-content coverage map, readiness estimation, confidence intervals,
and physical-device validation. Those claims must remain unavailable until the
required evidence exists.
