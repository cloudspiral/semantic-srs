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

This proves the desktop fork builds and runs locally. It does not prove a clean-machine installer, phone build, or bidirectional phone sync. Those remain separate acceptance tests.
