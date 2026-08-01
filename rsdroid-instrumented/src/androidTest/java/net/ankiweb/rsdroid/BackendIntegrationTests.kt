/*
 * Copyright (c) 2020 David Allison <davidallisongithub@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify it under
 * the terms of the GNU General Public License as published by the Free Software
 * Foundation; either version 3 of the License, or (at your option) any later
 * version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
 * PARTICULAR PURPOSE. See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along with
 * this program.  If not, see <http://www.gnu.org/licenses/>.
 */
package net.ankiweb.rsdroid

import androidx.test.ext.junit.runners.AndroidJUnit4
import anki.ankidroid.SchedTimingTodayLegacyRequest
import anki.notes.AddNoteRequest
import anki.notes.Note
import net.ankiweb.rsdroid.ankiutil.InstrumentedTest
import org.hamcrest.MatcherAssert.assertThat
import org.hamcrest.core.Is
import org.junit.Assert
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.rules.Timeout
import org.junit.runner.RunWith
import java.util.concurrent.TimeUnit

@RunWith(AndroidJUnit4::class)
class BackendIntegrationTests : InstrumentedTest() {
    /** Ensure that the database can't be locked  */
    @get:Rule
    var timeout = Timeout(5, TimeUnit.MINUTES)

    @Before
    fun test() {
        require(isEmulator) { "do not run on real device yet" }
    }

    @Test
    fun testBackendException() {
        val Backend = closedBackend
        try {
            Backend.closeCollection(true)
            Assert.fail("call should have failed - needs an open collection")
        } catch (ex: BackendException) {
            // OK
        }
    }

    @Test
    fun schedTimingTodayCall() {
        val backend = getBackend("initial_version_2_12_1.anki2")
        backend.schedTimingTodayLegacy(SchedTimingTodayLegacyRequest.getDefaultInstance())
    }

    @Test
    fun fullQueryTest() {
        val backendV1 = getBackend("initial_version_2_12_1.anki2")
        backendV1.fullQuery("select * from col")
    }

    @Test
    fun topicMasteryRunsThroughAndroidRustBackend() {
        val backend = getBackend("initial_version_2_12_1.anki2")

        val request = topicNoteRequest(backend, index = 1)
        backend.addNote(request.note, request.deckId)

        val response = backend.topicMastery(tagPrefix = "mcat", masteryThreshold = 0.9f)

        Assert.assertEquals("mcat", response.tagPrefix)
        Assert.assertEquals(0.9f, response.masteryThreshold, 0.0001f)
        Assert.assertEquals(1, response.totalTaggedCards)
        Assert.assertEquals("mcat::topic001", response.topicsList.single().topic)
    }

    @Test
    fun topicMasteryMeetsFiftyThousandCardDashboardBudget() {
        val backend = getBackend("initial_version_2_12_1.anki2")
        val totalCards = 50_000

        (0 until totalCards).chunked(5_000).forEach { indices ->
            val response = backend.addNotes(indices.map { topicNoteRequest(backend, it) })
            Assert.assertEquals(indices.size, response.nidsCount)
        }

        repeat(3) {
            Assert.assertEquals(
                totalCards,
                backend.topicMastery(tagPrefix = "mcat", masteryThreshold = 0.9f).totalTaggedCards,
            )
        }
        val timingsMs =
            List(20) {
                val startedAt = System.nanoTime()
                val response = backend.topicMastery(tagPrefix = "mcat", masteryThreshold = 0.9f)
                Assert.assertEquals(totalCards, response.totalTaggedCards)
                (System.nanoTime() - startedAt) / 1_000_000.0
            }.sorted()
        val median = (timingsMs[9] + timingsMs[10]) / 2
        val p95 = timingsMs[18]
        val worst = timingsMs.last()

        println(
            "SPEEDRUN_ANDROID_BENCH cards=$totalCards iterations=20 " +
                "median_ms=%.3f p95_ms=%.3f worst_ms=%.3f".format(median, p95, worst),
        )
        Assert.assertTrue("p95 ${"%.3f".format(p95)} ms exceeded 100 ms", p95 < 100)
    }

    @Test
    fun columnNamesTest() {
        val backendV1 = getBackend("initial_version_2_12_1.anki2")
        val names = backendV1.getColumnNames("select * from col")
        assertThat(
            names,
            Is.`is`(
                arrayOf(
                    "id",
                    "crt",
                    "mod",
                    "scm",
                    "ver",
                    "dty",
                    "usn",
                    "ls",
                    "conf",
                    "models",
                    "decks",
                    "dconf",
                    "tags",
                ),
            ),
        )
    }

    private fun topicNoteRequest(
        backend: Backend,
        index: Int,
    ): AddNoteRequest =
        AddNoteRequest
            .newBuilder()
            .setNote(
                Note
                    .newBuilder()
                    .setNotetypeId(backend.getNotetypeIdByName("Basic"))
                    .addFields("Speedrun benchmark card $index")
                    .addFields("Deterministic answer $index")
                    .addTags("mcat::topic${"%03d".format(index % 100)}")
                    .build(),
            ).setDeckId(1)
            .build()
}
