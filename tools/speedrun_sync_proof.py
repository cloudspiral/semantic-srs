# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Create and verify the disposable two-client Speedrun sync scenario."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from anki.collection import AddNoteRequest, Collection
from anki.decks import DeckId

ROOT_DECK = "Speedrun Sync Proof"
PHONE_DECK = f"{ROOT_DECK}::Phone Offline"
DESKTOP_DECK = f"{ROOT_DECK}::Desktop Offline"
CONFLICT_DECK = f"{ROOT_DECK}::Same Card Conflict"
TAG_ROOT = "mcat::syncproof"


def open_collection(path: Path) -> Collection:
    path.parent.mkdir(parents=True, exist_ok=True)
    return Collection(str(path))


def login(col: Collection, args: argparse.Namespace):
    return col.sync_login(args.username, args.password, args.endpoint)


def normal_sync(col: Collection, args: argparse.Namespace) -> dict[str, Any]:
    output = col.sync_collection(login(col, args), sync_media=False)
    if output.required != output.NO_CHANGES:
        raise RuntimeError(
            f"normal sync required an unexpected full action: {output.required}"
        )
    return {
        "host_number": output.host_number,
        "server_message": output.server_message,
        "required": "no_changes",
    }


def seed_and_upload(path: Path, args: argparse.Namespace) -> dict[str, Any]:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing collection: {path}")

    col = open_collection(path)
    notetype = col.models.by_name("Basic")
    assert notetype

    requests: list[AddNoteRequest] = []
    for deck_name, actor, count in (
        (PHONE_DECK, "phone", 10),
        (DESKTOP_DECK, "desktop", 10),
        (CONFLICT_DECK, "conflict", 1),
    ):
        deck_id = DeckId(col.decks.id(deck_name))
        for index in range(1, count + 1):
            note = col.new_note(notetype)
            note["Front"] = f"Speedrun sync proof - {actor} {index:02d}"
            note["Back"] = f"Deterministic answer for {actor} {index:02d}"
            note.add_tag(f"{TAG_ROOT}::{actor}")
            requests.append(AddNoteRequest(note=note, deck_id=deck_id))
    col.add_notes(requests)

    auth = login(col, args)
    output = col.sync_collection(auth, sync_media=False)
    if output.required == output.FULL_UPLOAD:
        col.full_upload_or_download(
            auth=auth,
            server_usn=output.server_media_usn,
            upload=True,
        )
        sync_kind = "full_upload"
    elif output.required == output.NO_CHANGES:
        sync_kind = "normal"
    else:
        raise RuntimeError(f"seed expected a full upload, got {output.required}")

    result = report(col)
    result["initial_sync"] = sync_kind
    col.close(downgrade=False)
    return result


def answer_deck(
    col: Collection, deck_name: str, ease: Literal[1, 2, 3, 4]
) -> list[int]:
    card_ids = sorted(col.find_cards(f'deck:"{deck_name}"'))
    if not card_ids:
        raise RuntimeError(f"no cards found in {deck_name}")
    for card_id in card_ids:
        card = col.get_card(card_id)
        card.start_timer()
        col.sched.answerCard(card, ease)
    return [int(card_id) for card_id in card_ids]


def review_desktop(path: Path, args: argparse.Namespace) -> dict[str, Any]:
    col = open_collection(path)
    desktop_ids = answer_deck(col, DESKTOP_DECK, ease=3)
    conflict_ids = answer_deck(col, CONFLICT_DECK, ease=2)
    result = report(col)
    result["reviewed_desktop_card_ids"] = desktop_ids
    result["reviewed_conflict_card_ids"] = conflict_ids
    col.close(downgrade=False)
    return result


def sync_existing(path: Path, args: argparse.Namespace) -> dict[str, Any]:
    col = open_collection(path)
    result = normal_sync(col, args)
    result["collection"] = report(col)
    col.close(downgrade=False)
    return result


def report(col: Collection) -> dict[str, Any]:
    cards: list[dict[str, Any]] = []
    for card_id in sorted(col.find_cards(f'deck:"{ROOT_DECK}"')):
        card = col.get_card(card_id)
        note = card.note()
        deck_name = col.decks.name(card.did)
        cards.append(
            {
                "card_id": int(card.id),
                "front": note["Front"],
                "deck": deck_name,
                "reps": card.reps,
                "queue": card.queue,
                "type": card.type,
                "interval": card.ivl,
            }
        )

    revlogs = [
        {
            "id": row[0],
            "card_id": row[1],
            "ease": row[2],
            "interval": row[3],
            "last_interval": row[4],
            "type": row[5],
        }
        for row in col.db.all(
            "select id, cid, ease, ivl, lastIvl, type from revlog order by id"
        )
    ]
    mastery = col.topic_mastery("mcat")
    return {
        "card_count": len(cards),
        "review_count": len(revlogs),
        "review_counts_by_card": dict(
            sorted(Counter(row["card_id"] for row in revlogs).items())
        ),
        "cards": cards,
        "revlogs": revlogs,
        "topic_mastery": {
            "total_tagged_cards": mastery.total_tagged_cards,
            "cards_with_memory_state": mastery.cards_with_memory_state,
            "cards_without_memory_state": mastery.cards_without_memory_state,
            "topics": [topic.topic for topic in mastery.topics],
        },
    }


def verify(path: Path) -> dict[str, Any]:
    col = open_collection(path)
    result = report(col)
    expected_cards = 21
    expected_reviews = 22
    phone_cards = [card for card in result["cards"] if card["deck"] == PHONE_DECK]
    desktop_cards = [card for card in result["cards"] if card["deck"] == DESKTOP_DECK]
    conflict_cards = [card for card in result["cards"] if card["deck"] == CONFLICT_DECK]

    assert result["card_count"] == expected_cards, result
    assert result["review_count"] == expected_reviews, result
    assert len(phone_cards) == 10 and all(card["reps"] == 1 for card in phone_cards)
    assert len(desktop_cards) == 10 and all(card["reps"] == 1 for card in desktop_cards)
    assert len(conflict_cards) == 1
    conflict_id = conflict_cards[0]["card_id"]
    assert result["review_counts_by_card"][conflict_id] == 2
    assert len({row["id"] for row in result["revlogs"]}) == expected_reviews

    phone_ids = {card["card_id"] for card in phone_cards}
    desktop_ids = {card["card_id"] for card in desktop_cards}
    phone_reviews = [row for row in result["revlogs"] if row["card_id"] in phone_ids]
    desktop_reviews = [
        row for row in result["revlogs"] if row["card_id"] in desktop_ids
    ]
    conflict_reviews = [
        row for row in result["revlogs"] if row["card_id"] == conflict_id
    ]
    assert len(phone_reviews) == 10 and all(row["ease"] == 3 for row in phone_reviews)
    assert len(desktop_reviews) == 10 and all(
        row["ease"] == 3 for row in desktop_reviews
    )
    assert [row["ease"] for row in conflict_reviews] == [4, 2]
    assert conflict_cards[0]["reps"] == 1
    assert conflict_cards[0]["queue"] == 1
    assert conflict_cards[0]["interval"] == 0

    integrity_message, integrity_ok = col.fix_integrity()
    assert integrity_ok, integrity_message
    result["integrity_ok"] = integrity_ok
    result["integrity_message"] = integrity_message
    result["conflict_rule_observed"] = (
        "Both immutable review-log events are retained exactly once. The phone's "
        "earlier Easy event remains in revlog, while the newer desktop Hard update "
        "wins the mutable card scheduling state (reps=1, queue=1, interval=0)."
    )
    col.close(downgrade=False)
    return result


def write_result(result: dict[str, Any], output: Path | None) -> None:
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(f"{rendered}\n", encoding="utf-8")
    print(rendered)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=("seed-upload", "review-desktop", "sync", "report", "verify"),
    )
    parser.add_argument("--collection", required=True, type=Path)
    parser.add_argument("--endpoint", default="http://127.0.0.1:18080/")
    parser.add_argument("--username", default="speedrun")
    parser.add_argument("--password", default="local-proof-only")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.action == "seed-upload":
        result = seed_and_upload(args.collection, args)
    elif args.action == "review-desktop":
        result = review_desktop(args.collection, args)
    elif args.action == "sync":
        result = sync_existing(args.collection, args)
    elif args.action == "report":
        col = open_collection(args.collection)
        result = report(col)
        col.close(downgrade=False)
    else:
        result = verify(args.collection)
    write_result(result, args.output)


if __name__ == "__main__":
    main()
