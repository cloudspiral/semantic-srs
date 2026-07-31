# Speedrun Brainlift v1

Status: v1, written before the Anki source was added to this workspace\
Exam: MCAT\
Spike: Why MCAT students can maintain strong flashcard recall while remaining unable to transfer that knowledge to unfamiliar passages\
Research cutoff: 2026-07-30

## 1. Purpose and boundaries

Speedrun is an Anki-based desktop study app with a phone companion. It separates three questions that study products often collapse:

1. **Memory:** What is the probability that the learner can recall a studied fact now?
2. **Performance:** What is the probability that the learner can apply relevant knowledge to a held-back, reworded, exam-style question?
3. **Readiness:** What MCAT score range is supported by held-back performance, timing, and official-outline coverage?

The product exists to expose the transfer gap between remembering a card and solving a novel problem. It will preserve Anki's FSRS scheduling semantics. Its thesis feature will use a Rust-native topic-mastery query to identify high-weight topics where recall is strong but transfer performance is weak, then recommend exam-style practice rather than more of the same cards.

Out of scope for v1:

- diagnosing a learner or guaranteeing an MCAT score;
- replacing official AAMC practice exams;
- changing FSRS intervals to force product-specific priorities;
- grading free-form medical advice;
- generating or scoring when provenance is missing;
- claiming hands-on observations of paid tools until a real account session has been completed;
- using AI as a dependency for reviewing, syncing, or calculating the three scores.

## 2. Why MCAT

The MCAT has an unusually useful split for this thesis: a large factual base makes spaced retrieval valuable, while passage-based questions require selection and application of knowledge under time pressure. The official total scale is 472-528, with four section scores of 118-132. Unlike a pass/fail exam, it provides a real scale on which uncertainty can be expressed as a range. Unlike an almost purely reasoning-based exam, it gives Anki's memory engine a legitimate job without pretending that memory is readiness.

The score model will abstain until both conditions hold:

- at least 200 graded reviews; and
- at least 50% of the official outline topics have evidence.

Even above that floor, readiness requires held-back exam-style responses. Card reviews alone can produce memory and coverage estimates, but never a projected MCAT score.

## 3. DOK 1 - source ledger

These are the load-bearing sources, not an exhaustive bibliography.

### S1. Wozniak, _Optimization of Learning_ and the SM-2 lineage

- Primary/source-of-record: https://www.super-memory.com/english/ol/sm2.htm
- System lineage: https://www.super-memory.com/english/ol.htm
- Evidence used: spaced repetition treats review timing as an optimization problem informed by response history. SM-2 made a practical scheduler out of per-item repetition state and a learner-supplied quality grade.
- What this project takes: review history is event data, scheduling state belongs in the shared engine, and a scheduler should be inspectable.
- What it rejects: a scheduling heuristic is not evidence of far transfer or exam readiness.

### S2. Ye, Su, and Cao (2022), _A Stochastic Shortest Path Algorithm for Optimizing Spaced Repetition Scheduling_

- DOI: https://doi.org/10.1145/3534678.3539081
- Reproduction repository: https://github.com/maimemo/SSP-MMC
- Evidence used: the DHP memory model and scheduling objective were fit/evaluated on large-scale time-series review behavior; the paper reports optimization of memorization cost.
- What this project takes: recall probability can be modeled and evaluated on held-out review events, and the evaluation should report a proper scoring rule.
- What it rejects: an optimized recall schedule is not automatically an optimized exam-preparation schedule.

### S3. FSRS and Anki's implementation decisions

- FSRS technical lineage: https://github.com/open-spaced-repetition/fsrs4anki
- FSRS Rust implementation used by Anki: https://github.com/open-spaced-repetition/fsrs-rs
- Anki FSRS behavior and constraints: https://docs.ankiweb.net/deck-options.html#fsrs
- Anki source: https://github.com/ankitects/anki
- Anki development/build decisions: https://github.com/ankitects/anki/blob/main/docs/development.md
- Evidence used: FSRS estimates retrievability and schedules toward desired retention; Anki keeps scheduling, storage, undo, sync, and cross-client contracts in its shared backend.
- What this project takes: preserve FSRS intervals and undo semantics; expose mastery through Anki's protobuf/Rust/Python boundary so desktop and phone use one definition.
- What it rejects: desired retention is not a readiness percentage, and a JavaScript or Swift reimplementation would create a second engine.

### S4. Roediger and Karpicke (2006), _Test-Enhanced Learning_

- DOI: https://doi.org/10.1111/j.1467-9280.2006.01693.x
- Primary article copy: https://is.muni.cz/el/phil/jaro2013/PSB_443/um/39045645/3_5.3._Test_enhanced_learning.pdf
- Evidence used: retrieval practice improved delayed retention relative to repeated study even when repeated study looked better on the immediate test.
- What this project takes: performance during study and durable learning can point in different directions; delayed, held-back outcomes matter.
- What it rejects: the result does not show that recalling the original wording transfers to a novel MCAT passage.

### S5. Kornell and Bjork (2008), _Learning Concepts and Categories: Is Spacing the Enemy of Induction?_

- DOI/record: https://pubmed.ncbi.nlm.nih.gov/18578849/
- Evidence used: interleaving category exemplars improved later classification even though learners commonly preferred blocking.
- What this project takes: discriminating among confusable topics may require mixed examples and novel classification, not another same-form retrieval.
- What it rejects: a category-learning result is not permission to interleave every learner and topic from the first exposure.

### S6. Sweller (1988), _Cognitive Load During Problem Solving: Effects on Learning_

- DOI: https://doi.org/10.1207/s15516709cog1202_4
- Evidence used: conventional means-ends problem solving can consume capacity needed for schema acquisition, and prior knowledge changes what instruction is useful.
- What this project takes: transfer practice should be gated by prerequisite memory and should not send a novice straight into maximal passage complexity.
- What it rejects: "harder is better" as a universal design rule.

### S7. Bjork and Bjork, desirable difficulties

- Source: https://bjorklab.psych.ucla.edu/wp-content/uploads/sites/13/2016/07/RBjork_inpress.pdf
- Evidence used: conditions that slow apparent acquisition can support retention and transfer; spacing, testing, variation, and interleaving are candidate difficulties.
- What this project takes: a temporary drop in practice accuracy can be compatible with better transfer.
- What it rejects: difficulty by itself is not desirable; the effect must be measured on delayed, novel items.

### S8. AAMC, exam structure, outline, and score reporting

- Official scale: https://students-residents.aamc.org/mcat-scores/mcat-exam-score-scale
- Official preparation and outline entry point: https://students-residents.aamc.org/prepare-mcat-exam/prepare-mcat-exam
- 2026 official prep updates: https://students-residents.aamc.org/prepare-mcat-exam/aamc-mcat-official-prep-updates
- Score-report confidence bands: https://www.aamc.org/services/mcat-admissions-officers/resources/score-report
- Evidence used: the real score scale is 472-528; the outline defines coverage; official score reports use confidence bands; official full-length practice is the closest available criterion.
- What this project takes: topic IDs and weights must come from the official outline, and projected scores must be ranges calibrated against held-back question performance.
- What it rejects: converting a flashcard percentage directly into a scaled score.

### S9. Current product behavior, public evidence only

- AAMC Official Prep: https://students-residents.aamc.org/prepare-mcat-exam/prepare-mcat-exam
- Blueprint practice exams/QBank: https://blueprintprep.com/mcat/practice-exams
- Blueprint analytics documentation: https://help.blueprintprep.com/en/articles/9757728-mcat-lsat-account-analytics
- UWorld MCAT: https://gradschool.uworld.com/mcat/
- UWorld QBank: https://gradschool.uworld.com/mcat/question-bank/
- UWorld flashcards: https://gradschool.uworld.com/mcat/flashcards/

Publicly observed on 2026-07-30: all three expose exam-style practice; Blueprint documents score-over-time, timing, answer-change, and metadata analytics; UWorld publicly distinguishes QBank performance from full-length score prediction and provides spaced-repetition flashcards plus topic analytics; AAMC provides official practice and the official outline. These are vendor-authored public claims and documentation, not independent validation.

## 4. DOK 2 - synthesis

### Memory systems optimize a narrow target well

SuperMemo, FSRS, and Anki form a coherent lineage: represent review history, estimate memory state, and choose the next interval. FSRS improves that narrow bridge by turning history into an explicit retrievability estimate that can be evaluated. That is valuable precisely because it is narrow. A recall probability means "likely to retrieve this memory under a similar cue," not "likely to select and use it inside a novel passage."

### Exam tools measure performance but usually fragment the loop

AAMC practice is closest to the criterion but is scarce and is not a daily memory engine. Blueprint and UWorld connect question banks, explanations, topic analytics, and study recommendations. UWorld also connects QBank content to spaced-repetition flashcards. Public documentation shows strong DOK 2/3 instruments, but does not establish a transparent, per-topic statistical bridge from card-level recall to held-back transfer, nor a visible abstention rule for readiness.

### Difficulty is conditional

Retrieval practice and interleaving can improve delayed outcomes while making practice feel worse. Cognitive-load evidence supplies the boundary: a challenge becomes undesirable when prerequisites are missing or the task consumes capacity without building a useful schema. The product therefore should not maximize difficulty. It should escalate cue distance only where the memory prerequisite is credible, then measure whether transfer improves.

### Calibration is a product behavior

The honest UI is not a single "readiness" ring. It is three estimates with ranges, coverage, sample size, last-updated time, reasons, and an explicit rule for refusing to score. Model quality is not established by an attractive point estimate; it is established by held-back calibration and error.

## 5. DOK 3 - contradictions and assumptions

### Contradiction A: fluent practice versus durable/transferable learning

Repeated exposure and blocked practice can produce rapid gains and confidence, while delayed retrieval or interleaving can look worse during training. Products naturally optimize visible session progress because it is immediate and motivating. The scientific criterion is delayed performance on unseen forms. The build must keep both numbers so the interface cannot silently substitute one for the other.

### Contradiction B: interleaving as benefit versus overload

Interleaving helps learners notice discriminating features, but novice problem solving can overload working memory. Therefore topic-aware mixing must be gated: first establish minimum recall evidence, then introduce nearby confusable topics and reworded items. A null or negative result for novices would not refute interleaving everywhere; it would refute this project's trigger policy.

### Contradiction C: personalized memory versus population score mapping

FSRS can personalize memory from an individual's review log. MCAT score mapping will initially depend on a much thinner sample and population assumptions. Combining them into one "AI readiness" number would launder the weakest link through the strongest. The product must show the models separately and let readiness abstain even when memory is well calibrated.

### Assumptions the build will test

1. A topic-level transfer gap is stable enough to guide the next activity.
2. FSRS retrievability aggregated by official topic is a useful memory feature.
3. Timing, difficulty, and coverage add predictive information beyond topic memory alone.
4. A mastery query over 50,000 cards can remain comfortably inside the dashboard budget.
5. The same protobuf contract can serve desktop Python and a phone client without duplicating scoring logic.

### What the public teardown exposed

| Tool               | DOK actually measured in public workflow                         | Progress number publicly documented                                          | What it implies                                                                   | Unknown / hands-on check required                                                                                                   |
| ------------------ | ---------------------------------------------------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| AAMC Official Prep | DOK 2/3 through official-style questions and full lengths        | Correctness and official scaled practice score                               | Closest evidence of present exam performance                                      | Whether the hub exposes explicit abstention, calibration history, or a single next-study recommendation                             |
| Blueprint          | DOK 2/3 through diagnostic, QBank, section and full-length exams | Scores over time, accuracy, timing, answer changes, topic/reasoning metadata | Analytics and targeting are described as indicating what raises score             | Exact score uncertainty UI, cold-start behavior, question rewording, and whether recommendations expose missing data                |
| UWorld             | DOK 1 flashcards plus DOK 2/3 QBank/full lengths                 | Flashcard performance, QBank analytics, topic gaps, full-length results      | Vendor explicitly says QBank is diagnostic and full lengths predict scores better | Whether memory and question performance are joined at the same concept level, and whether score prediction shows a calibrated range |

Teardown limitation: no paid or authenticated session was available during v1. The table records public interfaces, documentation, and product claims only. Before submission, run a scripted hands-on session in each tool and replace unknowns with screenshots and timestamps. Do not convert marketing claims into observed behavior.

## 6. DOK 4 - Spiky POVs

### POV 1 - the thesis under test

**Consensus says:** once recall is high, the learner should keep the spaced-repetition queue moving and add general question-bank volume.

**I think:** for MCAT learners with credible topic recall, the binding constraint is often _discriminative transfer_, and the next activity should be chosen by the largest exam-weighted gap between recall and held-back reworded-question performance. More cards from the same cue are often negative-value work at that point.

**Evidence:** retrieval and interleaving research separates practice fluency from delayed classification; MCAT passages require selecting knowledge under a changed cue; current tools publicly report memory or question performance, but the transparent gap is not their primary object.

**What would prove me wrong:** with equal study time and the same held-back questions, the transfer-gap queue fails to improve held-back passage accuracy over both (a) the same app with ordinary due ordering and (b) unmodified Anki. Primary metric set in advance: difference in held-back passage accuracy; secondary metrics: calibration error and time per correct answer. Report a 95% interval and accept a null result.

### POV 2 - readiness should be allowed to disappear

**Consensus says:** a study dashboard should always show a progress or readiness number so the learner knows where they stand.

**I think:** the most useful readiness state early in MCAT preparation is "insufficient evidence," because always-on scores reward content volume and turn missing coverage into false precision. Abstention is a feature, not an empty state.

**Evidence:** AAMC itself reports confidence bands; memory calibration and score mapping are different models; official-outline coverage can be measured directly.

**What would prove me wrong:** learners shown a strict abstention state abandon the product or make worse study choices than learners shown a clearly labeled, very-wide prior range, with no compensating improvement in calibration or trust.

### POV 3 - exam priority must not rewrite memory

**Consensus says:** if a topic matters more for the exam, schedule its cards sooner by changing intervals.

**I think:** exam priority belongs in queue selection and next-action guidance, not inside FSRS state transitions. Changing intervals mixes "likely to forget" with "important on the exam," makes recall calibration harder to interpret, and risks breaking undo/sync semantics.

**Evidence:** Anki/FSRS define a coherent memory contract; the official outline supplies a separate exam-weight signal; the two can be combined at query time without corrupting either.

**What would prove me wrong:** an interval-modifying topic scheduler preserves held-back recall calibration and undo/sync invariants while producing better transfer per minute than query-time prioritization.

## 7. AI consensus check

Model: OpenAI Codex, GPT-5 family\
Date: 2026-07-30\
Rule: the model was asked for objections, not approval. The evidence pass supplied sources without debating the response.

### Pass one - POV cold

**Prompt**

> Evaluate this claim as a skeptical learning-science and assessment expert. Do not help me sell it. Name the strongest objections and what evidence is missing: "For MCAT learners with strong flashcard recall, the binding constraint is discriminative transfer. The next study activity should be selected by the exam-weighted gap between recall and held-back reworded-question performance, not by doing more due cards."

**Response**

1. "Strong flashcard recall" may be a selection effect: advanced learners could both recall and transfer better without the queue causing either.
2. The claim jumps from a population story to an individual intervention without defining a threshold or showing the gap is stable.
3. Reworded questions may still be near copies and measure cue variation rather than MCAT passage reasoning.
4. Topic weights do not equal expected score gain; topics interact, and the MCAT samples skills as well as content.
5. Diverting time from due cards could damage retention, so any transfer gain must be measured jointly with memory cost.
6. Equal item counts are not equal study time, and a harder queue may change motivation or dropout.
7. The intervention needs an ordinary-Anki baseline and an ablation; otherwise a better question bank could explain the result.
8. A one-week sample cannot support a broad plateau claim or a calibrated MCAT score.

Cold result: useful pushback. The original claim was too broad about "MCAT learners" and did not protect the memory objective.

### Pass two - evidence supplied

**Prompt**

> Re-evaluate only in light of these sources and constraints. State exactly what changed, what did not, and the narrowest defensible claim.
>
> - Roediger & Karpicke (2006): delayed retention can favor retrieval practice even when repeated study looks better immediately.
> - Kornell & Bjork (2008): interleaving improved later category classification despite learner intuitions favoring blocking.
> - Sweller (1988): problem-solving load can impair schema acquisition for novices.
> - FSRS/Anki: retrievability is a memory estimate with preserved scheduling and undo semantics.
> - AAMC: the exam uses a 472-528 scale, an official content outline, passage reasoning, and confidence bands.
> - Design constraints: do not change FSRS intervals; gate transfer practice on prerequisite memory; use unseen passage-style items; compare feature-on, feature-off, and unmodified Anki under equal time; evaluate both recall and transfer; never score below the data floor.

**Response**

The sources move the claim from an unsupported replacement of spaced repetition to a plausible, falsifiable _routing policy after a memory prerequisite is met_. Kornell and Bjork support testing discrimination under varied exemplars; Roediger and Karpicke support using delayed outcomes rather than practice fluency; Sweller justifies the prerequisite gate; FSRS provides a separable memory estimate.

They do not establish that an exam-weighted transfer gap is the optimal policy, that the gap will be stable per learner, or that it maps to MCAT score gain. The defensible claim is:

> Among learners/topics that pass a predeclared recall-evidence gate, routing a fixed study-time budget toward official-topic-weighted, held-back transfer weaknesses may improve novel passage accuracy without harming calibrated recall; a three-arm test can reject that claim.

What moved: the objection that the idea necessarily competes with or corrupts the memory scheduler.\
What survived: causal identification, measurement leakage, stability, topic-weight validity, sample-size, and score-mapping objections.

### Load-bearing update

The AI check narrowed POV 1. The build will:

- keep FSRS state untouched;
- expose a Rust-native topic mastery read model;
- gate transfer recommendations;
- track equal study time, not equal item count;
- evaluate memory cost and transfer benefit together;
- keep readiness unavailable until held-back performance and coverage floors are met.

## 8. Traceability table

| POV                                | Forced build                                                                                                    | Real code target                                                                                                   | Predeclared number                                                                                                                                 | Failure condition                                                                                                   |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Transfer, not more same-cue review | Per-topic mastery query plus transfer-gap queue; thesis feature flag for ablation                               | Anki Rust collection service, new protobuf request/response, generated Python binding, desktop next-action service | Held-back passage accuracy difference with 95% interval; memory Brier score must not worsen beyond 0.02                                            | Feature-on does not beat feature-off and unmodified Anki under equal time, or harms recall calibration beyond limit |
| Readiness may disappear            | Three separate score cards with ranges, coverage, reasons, timestamps, sample counts, and enforced give-up rule | Shared scoring module and desktop/phone view state                                                                 | Abstain below 200 reviews or 50% official-topic coverage; readiness additionally requires at least 50 held-back questions across all four sections | Any UI path emits a projected score below the floor, or hides missing-section coverage                              |
| Priority must not rewrite memory   | Read-only mastery RPC and query-time ordering; unchanged FSRS scheduling/undo                                   | Rust query code and tests proving collection remains unchanged                                                     | Query p95 under 100 ms on 50,000 cards; collection checksum unchanged; undo behavior unchanged                                                     | Query mutates collection/scheduling state, misses the latency target, or desktop and phone disagree                 |

Features with no row are scope creep.

## 9. Test plan written before implementation

### Three-arm thesis test

1. Full app: transfer-gap routing on.
2. Same app: transfer-gap routing off; ordinary due ordering plus matched practice inventory.
3. Plain upstream Anki.

Use the same learners where possible, the same unseen questions, and identical study-time budgets. Set assignment and analysis before viewing outcomes. The primary outcome is held-back passage accuracy. Report a 95% interval. Also report response time, memory Brier score, completion, and attrition.

### Paraphrase test

Select 30 cards before model fitting. Author two meaning-preserving but cue-distant exam-style questions per card. Keep all 60 out of training and retrieval indexes. Compare card recall with question accuracy per topic. If the two rates match suspiciously closely or near-copy detection fires, treat the performance model as contaminated.

### Leakage check

Normalize text, compute exact hashes, token overlap, and semantic-neighbor similarity between every held-back item and all training/generation inputs. Set thresholds before inspection. Flag and remove both exact and near copies; report the excluded count.

### Calibration

- Memory: Brier score, log loss, and reliability bins on chronologically held-back review events.
- Performance: Brier score/log loss and accuracy on held-back questions, with slices by section, timing, difficulty, and coverage.
- Readiness: document the raw-to-scaled mapping and show a range. Until criterion data is sufficient, abstain rather than infer a polished number.

### Systems

- Three Rust unit tests and one Python-through-protobuf test for topic mastery.
- Query must be read-only; compare collection checksum before/after and exercise ordinary scheduler undo independently.
- Load a 50,000-card deck; report median, p95, and worst case.
- Offline conflict fixture: 10 unique phone reviews plus 10 unique desktop reviews merge exactly once. Same-card conflicts use stable event IDs and deterministic server order; retain both events and replay chronologically rather than silently overwriting either.
- Kill each client mid-review 20 times; expect zero corrupted collections.

## 10. What v1 still needs from real use

Before this Brainlift can be called submission-complete:

1. Run authenticated sessions in AAMC Official Prep, Blueprint, and UWorld; capture the same task path, timestamped screenshots, and exact score/uncertainty language.
2. Replace vendor claims in the teardown with observed behavior.
3. Acquire or author a rights-safe MCAT source corpus and official-outline topic map.
4. Freeze training/validation/test splits before using any AI generator.
5. Run the three-arm thesis test and update every POV with what survived.

This v1 is sufficient to constrain implementation. It is not evidence that the thesis works.

## 11. First build contact - 2026-07-30

POV 3 survived the first implementation pass: the useful exam-specific primitive was expressible as a read-only query, with no FSRS scheduling or undo implementation changes. Three Rust tests and a Python bridge test pass. The 50,000-card query initially missed the predeclared 100 ms target when it used Anki's general search table plus a second note-tag fetch. Replacing that path with one cached, minimal SQLite join reduced the optimized 20-run result to 19.752 ms p50, 20.215 ms p95, and 20.860 ms worst case.

This is systems evidence only. POV 1 has not survived or failed yet because no held-back transfer experiment has run. POV 2 remains a product constraint: readiness stays absent until the predeclared evidence floor and a defensible score mapping exist.
