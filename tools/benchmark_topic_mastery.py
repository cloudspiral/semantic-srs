# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Build a temporary tagged collection and time the topic-mastery RPC."""

from __future__ import annotations

import argparse
import json
import statistics
import tempfile
import time
from pathlib import Path

from anki.collection import AddNoteRequest, Collection
from anki.decks import DeckId


def benchmark(card_count: int, iterations: int) -> dict[str, object]:
    from anki.cards import FSRSMemoryState

    with tempfile.TemporaryDirectory(prefix="anki-topic-mastery-") as temp_dir:
        collection_path = Path(temp_dir) / "benchmark.anki2"
        col = Collection(str(collection_path))
        notetype = col.models.by_name("Basic")
        assert notetype

        requests: list[AddNoteRequest] = []
        topics = ("biology", "chemistry", "physics", "psychology")
        for index in range(card_count):
            note = col.new_note(notetype)
            note["Front"] = f"benchmark prompt {index}"
            note["Back"] = f"benchmark answer {index}"
            note.add_tag(f"mcat::{topics[index % len(topics)]}")
            requests.append(AddNoteRequest(note=note, deck_id=DeckId(1)))

        load_started = time.perf_counter()
        col.add_notes(requests)
        load_seconds = time.perf_counter() - load_started

        # Exercise the retrievability path as well as missing-evidence handling.
        card_ids = col.find_cards("tag:mcat")
        evidence_cards = [col.get_card(card_id) for card_id in card_ids[:100]]
        reviewed_at = int(time.time())
        for card in evidence_cards:
            card.memory_state = FSRSMemoryState(stability=100.0, difficulty=5.0)
            card.last_review_time = reviewed_at
        col.update_cards(evidence_cards, skip_undo_entry=True)

        col.topic_mastery("mcat")  # warm caches
        timings_ms: list[float] = []
        response = None
        for _ in range(iterations):
            started = time.perf_counter()
            response = col.topic_mastery("mcat")
            timings_ms.append((time.perf_counter() - started) * 1_000)
        assert response
        assert response.total_tagged_cards == card_count
        assert len(response.topics) == len(topics)
        col.close(downgrade=False)

    return {
        "card_count": card_count,
        "topics": len(topics),
        "cards_with_memory_state": response.cards_with_memory_state,
        "load_seconds": round(load_seconds, 3),
        "iterations": iterations,
        "query_ms": [round(timing, 3) for timing in timings_ms],
        "p50_query_ms": round(statistics.median(timings_ms), 3),
        "p95_query_ms": round(
            statistics.quantiles(timings_ms, n=100, method="inclusive")[94], 3
        ),
        "worst_query_ms": round(max(timings_ms), 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=int, default=50_000)
    parser.add_argument("--iterations", type=int, default=5)
    args = parser.parse_args()
    print(json.dumps(benchmark(args.cards, args.iterations), indent=2))


if __name__ == "__main__":
    main()
