// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

use std::collections::BTreeMap;
use std::collections::HashSet;

use anki_proto::stats::TopicMastery;
use anki_proto::stats::TopicMasteryRequest;
use anki_proto::stats::TopicMasteryResponse;
use fsrs::FSRS5_DEFAULT_DECAY;
use rusqlite::params;

use crate::card::Card;
use crate::prelude::*;
use crate::storage::card::data::CardData;

const DEFAULT_MASTERY_THRESHOLD: f32 = 0.9;

#[derive(Default)]
struct TopicAccumulator {
    total_cards: u32,
    cards_with_memory_state: u32,
    mastered_cards: u32,
    recall_sum: f32,
}

impl Collection {
    /// Return FSRS-derived recall and mastery grouped by descendant tags.
    ///
    /// This is deliberately read-only: it reuses Anki's persisted memory state
    /// and retrievability formula without changing scheduling state or adding
    /// an undo entry. Cards without memory state remain visible as missing
    /// evidence.
    pub fn topic_mastery(&mut self, input: TopicMasteryRequest) -> Result<TopicMasteryResponse> {
        let tag_prefix = input.tag_prefix.trim().trim_end_matches("::");
        require!(!tag_prefix.is_empty(), "tag prefix must not be empty");

        let mastery_threshold = if input.mastery_threshold == 0.0 {
            DEFAULT_MASTERY_THRESHOLD
        } else {
            input.mastery_threshold
        };
        require!(
            mastery_threshold.is_finite() && mastery_threshold > 0.0 && mastery_threshold <= 1.0,
            "mastery threshold must be in (0, 1]"
        );

        let topic_prefix = format!("{tag_prefix}::");
        let topic_prefix_lower = topic_prefix.to_lowercase();
        let timing = self.timing_today()?;
        let mut accumulators: BTreeMap<String, TopicAccumulator> = BTreeMap::new();
        let mut total_tagged_cards = 0_u32;
        let mut cards_with_memory_state = 0_u32;

        // One joined query avoids materializing Anki's temporary search table
        // and fetching the same notes again, which matters on 50k-card decks.
        let descendant_pattern = format!("(?i).* {}::.*", regex::escape(tag_prefix));
        let mut statement = self
            .storage
            .db
            .prepare_cached(include_str!("topic_mastery.sql"))?;
        let rows = statement.query_and_then(params![descendant_pattern], |row| {
            let data: CardData = row.get(8)?;
            let card = Card {
                note_id: row.get(0)?,
                ctype: row.get(2)?,
                queue: row.get(3)?,
                due: row.get(4)?,
                interval: row.get(5)?,
                original_due: row.get(6)?,
                original_deck_id: row.get(7)?,
                memory_state: data.memory_state(),
                decay: data.decay,
                last_review_time: data.last_review_time,
                ..Default::default()
            };
            Ok::<_, rusqlite::Error>((row.get::<_, String>(1)?, card))
        })?;

        for row in rows {
            let (tags, card) = row?;
            let topics = crate::tags::split_tags(&tags)
                .filter(|tag| tag.to_lowercase().starts_with(&topic_prefix_lower));
            total_tagged_cards += 1;
            let retrievability = card.memory_state.map(|state| {
                let elapsed_seconds = card.seconds_since_last_review(&timing).unwrap_or_default();
                fsrs::current_retrievability(
                    state.into(),
                    elapsed_seconds as f32 / 86_400.0,
                    card.decay.unwrap_or(FSRS5_DEFAULT_DECAY),
                )
            });
            if retrievability.is_some() {
                cards_with_memory_state += 1;
            }

            // A note can intentionally contribute to multiple topic rollups.
            // Duplicate spellings on one note are collapsed case-insensitively.
            let mut seen_topics = HashSet::new();
            for topic in topics {
                let normalized = topic.to_lowercase();
                if !seen_topics.insert(normalized.clone()) {
                    continue;
                }
                let accumulator = accumulators.entry(normalized).or_default();
                accumulator.total_cards += 1;
                if let Some(recall) = retrievability {
                    accumulator.cards_with_memory_state += 1;
                    accumulator.recall_sum += recall;
                    if recall >= mastery_threshold {
                        accumulator.mastered_cards += 1;
                    }
                }
            }
        }

        let topics = accumulators
            .into_iter()
            .map(|(topic, accumulator)| {
                let cards_without_memory_state =
                    accumulator.total_cards - accumulator.cards_with_memory_state;
                TopicMastery {
                    topic,
                    total_cards: accumulator.total_cards,
                    cards_with_memory_state: accumulator.cards_with_memory_state,
                    cards_without_memory_state,
                    mastered_cards: accumulator.mastered_cards,
                    average_recall: if accumulator.cards_with_memory_state == 0 {
                        0.0
                    } else {
                        accumulator.recall_sum / accumulator.cards_with_memory_state as f32
                    },
                    mastery: if accumulator.total_cards == 0 {
                        0.0
                    } else {
                        accumulator.mastered_cards as f32 / accumulator.total_cards as f32
                    },
                }
            })
            .collect();

        Ok(TopicMasteryResponse {
            topics,
            total_tagged_cards,
            cards_with_memory_state,
            cards_without_memory_state: total_tagged_cards - cards_with_memory_state,
            mastery_threshold,
            tag_prefix: tag_prefix.to_lowercase(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::card::FsrsMemoryState;

    fn add_topic_card(
        col: &mut Collection,
        tags: &[&str],
        memory_state: Option<FsrsMemoryState>,
        days_since_review: i64,
    ) -> Result<CardId> {
        let mut note = NoteAdder::basic(col).fields(&["front", "back"]).note();
        note.tags = tags.iter().map(ToString::to_string).collect();
        col.add_note(&mut note, DeckId(1))?;
        let mut card = col.storage.all_cards_of_note(note.id)?.remove(0);
        card.memory_state = memory_state;
        card.last_review_time = memory_state
            .map(|_| TimestampSecs(TimestampSecs::now().0 - days_since_review * 86_400));
        col.storage.update_card(&card)?;
        Ok(card.id)
    }

    fn request(threshold: f32) -> TopicMasteryRequest {
        TopicMasteryRequest {
            tag_prefix: "mcat".into(),
            mastery_threshold: threshold,
        }
    }

    #[test]
    fn groups_descendant_tags_and_counts_unique_cards() -> Result<()> {
        let mut col = Collection::new();
        add_topic_card(
            &mut col,
            &["mcat::biology", "mcat::chemistry"],
            Some(FsrsMemoryState {
                stability: 100.0,
                difficulty: 5.0,
            }),
            0,
        )?;
        add_topic_card(&mut col, &["mcat::biology"], None, 0)?;
        add_topic_card(&mut col, &["mcat"], None, 0)?;
        add_topic_card(&mut col, &["other::biology"], None, 0)?;

        let output = col.topic_mastery(request(0.9))?;

        assert_eq!(output.total_tagged_cards, 2);
        assert_eq!(output.topics.len(), 2);
        assert_eq!(output.topics[0].topic, "mcat::biology");
        assert_eq!(output.topics[0].total_cards, 2);
        assert_eq!(output.topics[1].topic, "mcat::chemistry");
        assert_eq!(output.topics[1].total_cards, 1);
        Ok(())
    }

    #[test]
    fn exposes_missing_memory_state_without_inflating_average() -> Result<()> {
        let mut col = Collection::new();
        add_topic_card(
            &mut col,
            &["MCAT::Biology"],
            Some(FsrsMemoryState {
                stability: 100.0,
                difficulty: 5.0,
            }),
            0,
        )?;
        add_topic_card(&mut col, &["mcat::biology"], None, 0)?;

        let output = col.topic_mastery(request(0.9))?;
        let biology = &output.topics[0];

        assert_eq!(biology.cards_with_memory_state, 1);
        assert_eq!(biology.cards_without_memory_state, 1);
        assert!(biology.average_recall > 0.99);
        assert_eq!(biology.mastered_cards, 1);
        assert_eq!(biology.mastery, 0.5);
        Ok(())
    }

    #[test]
    fn threshold_changes_mastery_and_query_is_undo_neutral() -> Result<()> {
        let mut col = Collection::new();
        let card_id = add_topic_card(
            &mut col,
            &["mcat::physics"],
            Some(FsrsMemoryState {
                stability: 10.0,
                difficulty: 5.0,
            }),
            10,
        )?;
        let undo_before = col.undo_status();
        let card_before = col.storage.get_card(card_id)?.unwrap();

        let lower = col.topic_mastery(request(0.8))?;
        let higher = col.topic_mastery(request(0.95))?;

        assert_eq!(lower.topics[0].mastered_cards, 1);
        assert_eq!(higher.topics[0].mastered_cards, 0);
        assert_eq!(col.undo_status().last_step, undo_before.last_step);
        assert_eq!(col.undo_status().undo, undo_before.undo);
        assert_eq!(col.undo_status().redo, undo_before.redo);
        assert_eq!(col.storage.get_card(card_id)?.unwrap(), card_before);
        assert_eq!(col.check_database()?, Default::default());
        Ok(())
    }
}
