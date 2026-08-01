# Speedrun - MCAT

Speedrun is an experimental desktop-and-phone MCAT study system built on Anki. Its core product claim is that strong flashcard recall can coexist with weak transfer to unfamiliar passages, so memory, question performance, and score readiness must be modeled and shown separately.

Current verified state:

- the upstream Anki desktop app builds and runs on macOS;
- a read-only Rust/protobuf/Python topic-mastery query reports FSRS recall by `mcat::...` tag without changing scheduling state;
- 3 Rust tests and 1 Python call-through test cover grouping, missing memory evidence, threshold behavior, and undo neutrality;
- optimized desktop and on-device Android 50,000-card benchmarks both meet the interactive dashboard budget;
- the desktop Statistics page and AnkiDroid Statistics drawer show the same Rust-backed evidence while memory, performance, and readiness abstain independently;
- a real two-client offline sync retained 22 unique review events across 21 cards, including two conflicting reviews of one card, and stayed idempotent after repeat sync and 20 mid-answer force-close/relaunch cycles on each app;
- an Apple Silicon DMG and Android debug APK build successfully without replacing the user's installed Anki or normal profile; and
- readiness remains abstained because no held-back outcome dataset supports a score estimate yet.

See the [Brainlift](./docs/BRAINLIFT.md), [local build guide](./docs/LOCAL_BUILD.md), [sync and mobile proof](./docs/SYNC_AND_MOBILE_PROOF.md), and [Rust implementation note](./docs/RUST_TOPIC_MASTERY.md).

## Anki upstream

[![Build Status](https://github.com/ankitects/anki/actions/workflows/ci.yml/badge.svg)](https://github.com/ankitects/anki/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/docs-dev--docs.ankiweb.net-blue)](https://dev-docs.ankiweb.net)

This fork contains the source code for the computer version of
[Anki](https://apps.ankiweb.net).

## About

Anki is a spaced repetition program. Please see the [website](https://apps.ankiweb.net) to learn more.

## Getting Started

### Contributing

Want to contribute to Anki? Check out the [Contribution Guidelines](./docs/contributing.md).

For more information on building and developing, please see [Development](./docs/development.md).

#### Contributors

The following people have contributed to Anki: [CONTRIBUTORS](./CONTRIBUTORS)

### Anki Betas

If you'd like to try development builds of Anki but don't feel comfortable
building the code, please see [Anki betas](https://betas.ankiweb.net/).

## License

Anki's license: [LICENSE](./LICENSE)
