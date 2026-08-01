# Why topic mastery belongs in Rust

## Decision

Speedrun implements a read-only `TopicMastery` RPC in Anki's shared Rust collection service. A caller supplies a hierarchical tag root such as `mcat` and a recall threshold. The response groups descendant tags such as `mcat::biology`, then returns:

- total cards;
- cards with and without FSRS memory state;
- average current FSRS retrievability for cards with evidence;
- cards at or above the mastery threshold; and
- mastered cards divided by all cards.

Zero in the protobuf threshold field selects the explicit default of 0.90. Other values must be finite and in `(0, 1]`.

## Why the engine is the right boundary

FSRS memory state, card timing, SQLite storage, tag semantics, undo, and sync are Anki engine concerns. Calculating recall in a desktop view would duplicate Anki's retrievability formula and make a phone client likely to disagree. The RPC instead uses the same `fsrs::current_retrievability` call, card decay fallback, and elapsed-time logic as Anki's existing retrievability graph.

The operation does not reschedule cards, alter desired retention, write revlogs, or create an undo entry. Exam priority can consume this read model later without contaminating the memory model it is trying to measure.

Missing evidence is not silently converted to zero recall. It is excluded from `average_recall`, counted in `cards_without_memory_state`, and remains in the mastery denominator. That lets a dashboard distinguish "observed weak recall" from "we do not know."

## Performance shape

The implementation uses one cached SQLite join over cards and note tags. It selects only the card fields needed to reconstruct FSRS retrievability and avoids Anki's general search temporary table. Notes may belong to multiple topics intentionally; duplicate topic spellings on one note are collapsed case-insensitively.

On an optimized Apple Silicon build with 50,000 generated cards across four MCAT topics and 100 cards carrying FSRS memory state, 20 warm queries produced:

- p50: 19.752 ms;
- p95: 20.215 ms; and
- worst case: 20.860 ms.

The exact result can vary by machine. Reproduce it with:

```sh
PYTHONPATH="$PWD/out/pylib" \
  ANKI_TEST_MODE=1 \
  "$PWD/out/pyenv/bin/python" \
  tools/benchmark_topic_mastery.py --cards 50000 --iterations 20
```

The same RPC was also benchmarked across AnkiDroid's real JNI boundary on an
Android 15 ARM64 Pixel 8 emulator. After three warmups, 20 measured calls over
50,000 tagged cards produced:

- median: 69.393 ms;
- p95: 91.849 ms; and
- worst case: 95.509 ms.

The Android instrumentation test has a hard `p95 < 100 ms` assertion. It lives
in the companion backend checkout at
`tmp/Anki-Android-Backend/rsdroid-instrumented/src/androidTest/java/net/ankiweb/rsdroid/BackendIntegrationTests.kt`.

## Tests and invariants

The three Rust unit tests prove:

1. descendant tags group correctly, one card may inform multiple topics, and unrelated/root-only tags do not count;
2. missing memory state remains visible and cannot inflate average recall or mastery; and
3. changing the threshold changes mastery while the card and undo status remain byte-for-byte/equality unchanged, followed by a clean collection database check.

The Python test creates an `mcat::biology` note and calls `Collection.topic_mastery()`, exercising generated protobuf bindings and the Rust bridge end to end.

An Android integration test creates a real tagged note and calls the same RPC
through `BackendFactory`, proving the generated Kotlin/protobuf/JNI path rather
than a Kotlin reimplementation.

## Upstream files touched

- `proto/anki/stats.proto`: request, response, topic result, and service method.
- `rslib/src/stats/mod.rs`: registers the Rust module.
- `rslib/src/stats/service.rs`: maps the service trait to the collection method.
- `rslib/src/stats/topic_mastery.rs`: validation, query, aggregation, FSRS calculation, and Rust tests.
- `rslib/src/stats/topic_mastery.sql`: minimal cached SQLite query.
- `pylib/anki/collection.py`: public Python convenience method.
- `pylib/tests/test_stats.py`: Python-to-Rust integration test.
- `tools/benchmark_topic_mastery.py`: deterministic 50,000-card benchmark harness.

No FSRS scheduling, review answering, sync, or undo implementation file is modified.
