# Local macOS build

These commands were verified on Apple Silicon macOS on 2026-07-30. They keep development data separate from a real Anki profile.

## Prerequisites

```sh
brew install rustup ninja just mpv lame
export PATH="/opt/homebrew/opt/rustup/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
rustup toolchain install 1.92.0-aarch64-apple-darwin
git submodule update --init qt/installer/mac-template
```

Anki downloads its pinned Node, Python, protobuf, Qt, and other build dependencies on the first build.

## Build and launch

```sh
just build
just run --base /private/tmp/speedrun-anki-profile --lang en
```

The `--base` path is deliberate: it prevents an unfinished fork from opening or changing the user's normal Anki profile.

For a production-performance build:

```sh
RELEASE=1 just build
```

## Build a macOS installer

```sh
just installer
```

The verified Apple Silicon build produced
`out/installer/dist/anki-26.05-mac-apple.dmg`. The app in that image is
ad-hoc signed, so it is suitable for local proof on the build Mac but not for
distribution to other Macs. A distributable artifact still requires an Apple
Developer ID certificate and notarization.

The 2026-07-31 artifact is 213 MiB with SHA-256
`8d757377d5c8f4cf496831dcec5402a19b75f57528c662e57d4dff2470f8654f`.

## Test and benchmark

```sh
just test-rust
just test-py
just check
PYTHONPATH="$PWD/out/pylib" \
  ANKI_TEST_MODE=1 \
  "$PWD/out/pyenv/bin/python" \
  tools/benchmark_topic_mastery.py --cards 50000 --iterations 20
```

`just check` is the final upstream gate. The focused Rust and Python recipes are listed separately so failures remain easy to localize.

## Known boundary

This proves the desktop fork builds and runs locally. The generated DMG passed
image verification, deep code-signature verification, and a launch directly
from a read-only mounted image with `--base` pointing at a disposable path. It
does not prove installation or launch on a separate clean Mac, and the ad-hoc
signature is intentionally not distributable.

The Android emulator and bidirectional offline-sync proof are documented in
[SYNC_AND_MOBILE_PROOF.md](./SYNC_AND_MOBILE_PROOF.md). None of these commands
replace `/Applications/Anki.app` or open the normal Anki profile.
