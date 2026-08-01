<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import type {
        GraphsResponse_ReviewCountsAndTimes_Reviews,
        TopicMasteryResponse,
    } from "@generated/anki/stats_pb";
    import { graphs, topicMastery } from "@generated/backend";

    interface DashboardState {
        evidence: TopicMasteryResponse;
        gradedReviews: number;
        updatedAt: string;
    }

    function countReviews(review: GraphsResponse_ReviewCountsAndTimes_Reviews): number {
        return (
            review.learn +
            review.relearn +
            review.young +
            review.mature +
            review.filtered
        );
    }

    async function loadDashboard(): Promise<DashboardState> {
        const [evidence, allHistory] = await Promise.all([
            topicMastery({ tagPrefix: "mcat", masteryThreshold: 0.9 }),
            graphs({ search: "", days: 0 }),
        ]);
        const gradedReviews = Object.values(allHistory.reviews?.count ?? {}).reduce(
            (total, review) => total + countReviews(review),
            0,
        );

        return {
            evidence,
            gradedReviews,
            updatedAt: new Intl.DateTimeFormat(undefined, {
                hour: "numeric",
                minute: "2-digit",
            }).format(new Date()),
        };
    }

    function engineEvidence(evidence: TopicMasteryResponse): string {
        if (evidence.totalTaggedCards === 0) {
            return "No cards tagged under mcat yet.";
        }
        if (evidence.cardsWithMemoryState === 0) {
            return `${evidence.totalTaggedCards} tagged cards; no FSRS memory state yet; ${evidence.topics.length} topic groups.`;
        }
        const recallSum = evidence.topics.reduce(
            (sum, topic) => sum + topic.averageRecall * topic.cardsWithMemoryState,
            0,
        );
        const averageRecall = (recallSum / evidence.cardsWithMemoryState) * 100;
        return `${evidence.cardsWithMemoryState}/${evidence.totalTaggedCards} tagged cards have FSRS state; average recall ${averageRecall.toFixed(1)}%; ${evidence.topics.length} topic groups.`;
    }

    const dashboard = loadDashboard();
</script>

<section class="speedrun-dashboard" aria-labelledby="speedrun-dashboard-title">
    <header>
        <div>
            <h2 id="speedrun-dashboard-title">Speedrun · MCAT</h2>
            <p>One Rust engine · three separate claims · honest abstention</p>
        </div>
        <span class="engine-badge">Rust-backed</span>
    </header>

    {#await dashboard}
        <p class="status">Loading topic evidence…</p>
    {:then state}
        <div class="scores">
            <article>
                <h3>Memory</h3>
                <strong>Abstain</strong>
                <span>Range — · confidence none</span>
                <p>{state.gradedReviews}/200 graded reviews</p>
            </article>
            <article>
                <h3>Performance</h3>
                <strong>Abstain</strong>
                <span>Range — · confidence none</span>
                <p>Needs held-back exam-style questions</p>
            </article>
            <article>
                <h3>Readiness</h3>
                <strong>Abstain</strong>
                <span>MCAT range — · confidence none</span>
                <p>Requires 50% official-topic coverage and held-back performance</p>
            </article>
        </div>
        <div class="evidence">
            <strong>Rust engine evidence</strong>
            · {engineEvidence(state.evidence)}
        </div>
        <div class="rule">
            Give-up rule: no score below 200 graded reviews, 50% official-topic
            coverage, and a passing held-back evaluation. Updated {state.updatedAt}.
        </div>
    {:catch error}
        <p class="status error">
            Topic evidence unavailable. Scores remain abstained. {error instanceof Error
                ? error.message
                : String(error)}
        </p>
    {/await}
</section>

<style lang="scss">
    .speedrun-dashboard {
        grid-column: 1 / -1;
        border: 1px solid var(--border-subtle);
        border-radius: 0.75rem;
        padding: 1rem;
        background: var(--canvas-elevated);
        box-shadow: 0 0.15rem 0.5rem rgb(0 0 0 / 8%);
    }

    header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1rem;

        h2 {
            margin: 0;
            font-size: 1.2rem;
        }

        p {
            margin: 0.2rem 0 0;
            opacity: 0.7;
        }
    }

    .engine-badge {
        border-radius: 999px;
        padding: 0.25rem 0.65rem;
        background: rgb(53 111 99 / 14%);
        color: var(--fg-link);
        font-size: 0.8rem;
        font-weight: 600;
        white-space: nowrap;
    }

    .scores {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin-top: 1rem;

        article {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            border: 1px solid var(--border-subtle);
            border-radius: 0.6rem;
            padding: 0.75rem;
        }

        h3,
        p {
            margin: 0;
        }

        h3 {
            font-size: 0.9rem;
            opacity: 0.75;
        }

        strong {
            font-size: 1.15rem;
        }

        span,
        p {
            font-size: 0.82rem;
        }

        span {
            opacity: 0.7;
        }
    }

    .evidence,
    .rule,
    .status {
        margin: 0.8rem 0 0;
        font-size: 0.85rem;
    }

    .rule {
        opacity: 0.7;
    }

    .error {
        font-weight: 600;
    }

    @media only screen and (max-width: 800px) {
        .scores {
            grid-template-columns: 1fr;
        }
    }
</style>
