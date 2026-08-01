# Android and two-client sync proof

## What is implemented

The companion AnkiDroid checkout in `tmp/Anki-Android` exposes a Speedrun
dashboard under **Navigation drawer > Statistics**. Its backend package in
`tmp/Anki-Android-Backend` includes the forked Anki Rust engine, so Android
calls `TopicMastery` through generated protobuf and JNI bindings. It does not
reimplement the mastery calculation in Kotlin.

The desktop Statistics page contains the corresponding dashboard. Both clients
keep three claims separate:

- memory evidence comes from tagged cards, FSRS state, and actual graded
  reviews;
- performance requires held-back exam-style questions; and
- readiness additionally requires official-topic coverage and validated
  performance.

Until those requirements are met, the UI says **Abstain** and shows no numeric
range or confidence. The current give-up rule requires at least 200 graded
reviews, 50% official-topic coverage, and a passing held-back evaluation.

## Verified Android path

The debug app was built, installed, and exercised on a standard Android Studio
AVD:

- Pixel 8 hardware profile;
- Android 15 / API 35;
- ARM64; and
- package `com.ichi2.anki.debug`.

This is the standard Mac development route for an Android-capable app. It
proves the APK, Android UI, JNI boundary, collection engine, and sync behavior
in an Android runtime. It is not a physical-device battery, camera, or vendor
compatibility test.

The ARM64 debug artifact is
`tmp/Anki-Android/AnkiDroid/build/outputs/apk/play/debug/AnkiDroid-play-arm64-v8a-debug.apk`.
The 2026-07-31 build is 107 MiB with SHA-256
`a7ba351974b687b8aa3f7af200fbb14167b57ac6ea6c53e18a8a40093ede116f`.

The 50,000-card instrumentation benchmark measured 20 post-warmup calls to the
Rust topic-mastery RPC. It passed its hard 100 ms p95 budget with median 69.393
ms, p95 91.849 ms, and worst 95.509 ms.

## Offline merge scenario

`tools/speedrun_sync_proof.py` creates and validates a disposable fixture. The
test used a local Anki sync server and two independent clients: the Android
emulator and a desktop collection opened only by the Python/Rust library.

The scenario was:

1. seed and upload 21 cards;
2. disconnect Android and review 10 phone cards once with Good;
3. review the shared conflict card on Android with Easy;
4. while Android remains disconnected, review 10 different desktop cards once
   with Good and the same conflict card with Hard;
5. sync desktop, reconnect and sync Android, then sync desktop again; and
6. repeat both syncs and run a collection integrity check.

The strict verifier observed:

- 21 cards and exactly 22 unique review-log rows;
- each phone-only and desktop-only card reviewed exactly once;
- two immutable review events retained for the conflict card, in Easy-then-Hard
  order;
- the later desktop Hard change winning the mutable card scheduling state;
- no event duplication after another Android/desktop sync; and
- a successful collection database integrity rebuild/check.

Android was then force-stopped and relaunched in the middle of an answer screen
20 times. A final Android/desktop sync and the same strict verifier still
reported 21 cards, 22 unique events, the same conflict result, and a clean
database.

The desktop fork was separately driven through its real Qt webviews. On each of
20 cycles the harness opened the deck, started the reviewer, confirmed the
answer plus Again/Hard/Good/Easy controls were visible, and sent an
unconditional process kill before grading. After the twentieth kill, the same
strict collection verifier reported the original 21 cards and 22 review events
with no duplicates or loss, the same conflict state, and a successful database
integrity rebuild/check.

Representative machine-generated JSON and screenshots are intentionally kept
outside Git under `tmp/sync-proof/evidence/`. The final verifier outputs are
`05-final-verification.json`, `06-repeat-sync.json`, and
`08-post-crash-verification.json`. The desktop run adds
`09-desktop-crash-cycles.jsonl` with one pre-kill UI-state record per cycle and
`10-desktop-post-crash-verification.json` with the final integrity result.

## Re-running the collection verifier

Use the fork's isolated Python environment and a disposable collection:

```sh
PYTHONPATH="$PWD/out/pylib" \
  ANKI_TEST_MODE=1 \
  "$PWD/out/pyenv/bin/python" \
  tools/speedrun_sync_proof.py verify \
  --collection tmp/sync-proof/desktop/collection.anki2 \
  --output tmp/sync-proof/evidence/verification.json
```

The seed, offline desktop review, sync, report, and verify actions are all
available through the script's first positional argument. Credentials and the
server endpoint are disposable command-line inputs; no real AnkiWeb account or
normal user profile is required.

## Remaining boundary

The Android path is emulator-verified, not physical-device verified. The DMG is
ad-hoc signed and verified only on the build Mac. A real MCAT performance or
readiness score remains intentionally impossible until the official-topic
taxonomy, held-back question set, scoring model, and leakage-resistant
evaluation protocol are supplied and validated.
