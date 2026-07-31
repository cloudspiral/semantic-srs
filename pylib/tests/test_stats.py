# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os
import tempfile

import pytest

from anki.collection import CardStats
from tests.shared import getEmptyCol


def test_stats():
    col = getEmptyCol()
    note = col.newNote()
    note["Front"] = "foo"
    col.addNote(note)
    c = note.cards()[0]
    # card stats
    card_stats = col.card_stats_data(c.id)
    assert card_stats.note_id == note.id
    c = col.sched.getCard()
    col.sched.answerCard(c, 3)
    col.sched.answerCard(c, 2)
    card_stats = col.card_stats_data(c.id)
    assert len(card_stats.revlog) == 2


def test_graphs_empty():
    col = getEmptyCol()
    assert col.stats().report()


def test_graphs():
    dir = tempfile.gettempdir()
    col = getEmptyCol()
    g = col.stats()
    rep = g.report()
    with open(os.path.join(dir, "test.html"), "w", encoding="UTF-8") as note:
        note.write(rep)
    return


def test_topic_mastery_calls_rust_backend():
    col = getEmptyCol()
    note = col.newNote()
    note["Front"] = "mitochondrion"
    note.add_tag("mcat::biology")
    col.addNote(note)

    output = col.topic_mastery("mcat")

    assert output.tag_prefix == "mcat"
    assert output.mastery_threshold == pytest.approx(0.9)
    assert output.total_tagged_cards == 1
    assert output.cards_with_memory_state == 0
    assert output.cards_without_memory_state == 1
    assert len(output.topics) == 1
    assert output.topics[0].topic == "mcat::biology"
    assert output.topics[0].mastery == 0
