# Review — `part_1/03-hot-cold-separation.md` (Bullet 1.3)

## Summary

This page answers the test's hot/cold bullet by refusing its premise — there is no real-time *processing*, only real-time transport — and puts the boundary at Bronze on a single load-bearing claim: everything before it can fail, nothing before it can be wrong. The reframe is the strongest thinking in Part 1 and is not a dodge, but the load-bearing sentence is stated more absolutely than the design supports, and the author's own page 1.1 supplies the counterexample.

## Grade

| Dimension | Grade | One line |
|---|---|---|
| Decision quality | **A** | Lambda is killed on a structural argument (the hour boundary caps the latency a speed layer would buy), and *continuous maintenance* is named as "the serious alternative" and then beaten on a domain-specific repair — a backdated revenue share — with the simplicity argument explicitly turned around rather than asserted. |
| Narrative | **B** | There is a real spine (one thesis sentence, four repairs, two rejections), but the page negates both halves of the test's phrase before it has answered either, and three passages double back on the table. |
| Operability instinct | **B** | The four-trigger repair taxonomy and "nobody is on call for the ingestion path" are exactly the right instincts; the one hot-path failure that actually needs a human — the dead-letter topic — is missing from a page whose entire subject is what fails where. |
| Technical plausibility | **B** | The numbers survive arithmetic (~10 GB of keyed state at 23k/s × 1h is right to within 20%, and "low thousands/month" for streaming Dataflow on this firehose is honest); the wince is "the only failure available before Bronze is not delivering", which is not true of a dead-lettered write. |
| Signal density | **A** | ~1,100 words carrying four rejected alternatives, a repair taxonomy and a compliance boundary; the ~175 words I would cut are a rounding error at this density. |
| **Overall** | **A** | I would ask about the reframe out of genuine interest, and about the continuous-maintenance reversal out of respect — but the headline claim needs a 25-word qualification before it is defended live, because it is quoted verbatim on `part1-pipeline.md` and propagates. |

**On the reframe specifically, since it is the page's biggest bet:** it is a strong answer, not a dodge. Separating *latency of arrival* from *latency of computation* is the observation that licenses the whole no-Dataflow design, and the page earns it by immediately delivering the hot/cold table the grader is looking for. The risk is presentational and it is real: the first sentence after the quoted bullet tells the grader their word is wrong, and the second does it again for *batch archiving*. This inverts the repo's own rule — lead with their construct, then extend it. Moving the table above line 5 costs nothing and removes the only version of this page a rubric-following grader could mark down.

## Top findings

**1. [BLOCKER] "Nothing before Bronze can be wrong" has a counterexample two pages earlier in the same document.**

- *What:* Page 1.1 says a write BigQuery refuses is dead-lettered with "two causes, both silent" (table/topic schema drift, invalid JSON in `payload`), which is precisely a plausible-but-false number reported by nobody — the exact failure this page exiles to the cold path — yet this page's "Failure mode" cell lists only slower throughput and a synchronous publish refusal, and claims "the only failure available before Bronze is not delivering… a delay rather than a loss."
- *Why it matters to the evaluator:* This sentence is the page's thesis and is quoted as the design's summary on `part1-pipeline.md`; an interviewer who has read 1.1 gets to produce the contradiction from the candidate's own material, which converts a strong claim into an overclaim.
- *Fix:* Qualify in one clause and the claim gets stronger, not weaker: the hot path's only silent failure is *under*-delivery, it is caught by the dead-letter depth monitor rather than prevented by the shape, and it is replayable from the GCS archive — which holds the declined message — inside the 7-day window. Say that the archive is what makes the dead letter a delay.

**2. [QUESTION] The envelope split is quiet work before Bronze; it has just been moved into someone else's process.**

- *What:* The page claims the hot path does "no cast, no join" and that the line is drawn on the absence of *quiet* work, but the producer's collector extracts five fields into named columns, and a collector emitting the wrong `publisher_id` produces a plausible wrong number whose fix is a redeploy rather than a rerun — the page's own definition of the thing that must not sit there — and the claim explicitly covers "everything before Bronze", not just everything after the topic.
- *Why it matters to the evaluator:* It is the first counter a staff engineer reaches for, and 1.2's answer ("their collector already routes on `publisher_id` and `event_type`") is an argument about *cost of asking*, not about *correctness*, so it does not close this.
- *Fix:* One clause here: the promoted fields are values the collector already computes for routing, so the split adds no new derivation — and if `payload` retains them, name the quality-job assertion that compares envelope to payload on a sample. That converts the weakest point on the page into a demonstrated control.

**3. [QUESTION] Trigger 4 says "everything downstream then reruns unchanged", and two steps are hiding inside that.**

- *What:* Rows replayed from GCS land with their original `publish_time`, which is *behind* Silver's watermark, so the next scheduled run does not see them — the watermark must be rewound (2.3 makes it settable, but this page does not say so) — and if the replayed partition is older than D-3, Gold needs the targeted rebuild of trigger 3 as well; separately, `publish_time` only survives the round trip if the archive subscription writes Avro or Parquet with message metadata, which no page in the write-up states.
- *Why it matters to the evaluator:* "One code path covers all four repairs" is the page's payoff line, and the one trigger that is actually a runbook is presented as the one that needs no intervention.
- *Fix:* Add "set the watermark back and let the next run pick it up" to the trigger-4 mechanism cell — it *is* still one code path, just with one `UPDATE` in front of it — and state the archive's write format once, on 1.1 or 1.2, since `publish_time` is Bronze's partition key.

**4. [QUESTION] "The only intraday consumer is our own team" is asserted, and the free counter-argument is left on the table.**

- *What:* The lambda rejection is correct about *hourly figures*, but the deploy-day case is not about figures — it is "did the release just kill 40% of traffic", and with Silver at ≤30 min and Gold hourly, a bad release at 10:01 can be invisible for the better part of an hour, which in ad tech is money.
- *Why it matters to the evaluator:* A CTO in this domain will not accept a latency argument that never prices the outage it tolerates, and the page prices the speed layer but not the thing the speed layer would insure.
- *Fix:* Name the answer that costs nothing: Pub/Sub publishes topic throughput as a native Cloud Monitoring metric, so traffic collapse is detectable in minutes without a speed layer, a metric implementation, or a second definition of anything. That is a sharper kill on lambda than the hour-boundary argument.

**5. [POLISH] Two cells in the table make the reader decode rather than read.**

- *What:* The cold-path Latency cell reads "30 min · hourly · hourly and daily" with no key, and the reader has to map three items onto Silver, Gold and the quality tables; "State held: None between runs" sits one row above a design whose watermark is state between runs, rescued only by the parenthetical.
- *Why it matters to the evaluator:* The table is the page's direct answer to the bullet, and it is the one artefact a grader will read in isolation.
- *Fix:* Label the latencies ("Silver 30 min · Gold hourly · quality hourly + daily") and merge the watermark clause into a "State" row that says it plainly.

## Cuts

1. **The blockquote at line 25 (~45 words).** It restates two cells of the table directly above it — "Failure mode: slower throughput, which Google handles" and "Who operates it: GCP" — in prose. It is also not an incident narrative, so it spends one of the document's ~5–6 blockquote slots on a paraphrase. *Lost:* the "job of ours crashing at 03:00" image, which is genuinely good; keep it as a clause inside the Failure mode cell, or as spoken ammunition.

2. **Line 19, "The raw payload exists only on the hot path… the only table with an expiration set" (~30 words).** Restates the table's Personal data row and compresses the whole of `part_1/00`. *Lost:* the phrase "the hot/cold line is also the compliance boundary", which is worth six words inside the table row rather than a standalone sentence.

3. **The second half of the Cost paragraph (~40 words),** from "a speed layer means a streaming runtime…" to "next to a second implementation of every metric." Lambda is now argued three times on one page: the prose section, the cost paragraph, and the rejected table. *Lost:* nothing — the "low thousands per month" figure can stay in one clause.

4. **The final clause of line 23, "The envelope is the five named fields the topic schema declares…" (~25 words).** Restates 1.1 hop 1 verbatim in substance. *Lost:* nothing on this page; the rejected table's last row already makes the "refuses a message, never alters one" point better.

5. **Rejected rows 1 and 2 (~35 words)** are one-line compressions of the two prose sections immediately above them. Either drop the rows or drop the section headings and let the table carry them — running both is the house convention working against itself when the prose is only two paragraphs away.

Total ≈ 175 words, ~15% of the page, none of it argument.

## Interview questions this page invites

1. **"A write BigQuery refuses is dead-lettered and no job fails. How is that not the hot path being quietly wrong?"** — *Not answered here.* 1.1 answers half of it (the archive holds declined messages, a monitor watches depth); this page asserts the opposite and needs the qualification.
2. **"You didn't remove the transformation before Bronze, you moved it into the publisher's collector. What catches a collector that puts the wrong `publisher_id` in the envelope?"** — *Not answered.* 1.2 argues why asking for the split is cheap, not what detects it going wrong.
3. **"Replayed rows carry their old `publish_time`, which is behind Silver's watermark. What re-reads them?"** — *Not answered here;* 2.3 supplies the settable watermark, but the trigger table claims "reruns unchanged", which is the wrong answer to this question.

## Claims ledger

**DECISIONS**
- Hot/cold boundary placed at **Bronze** — rationale: everything before it can fail, nothing before it can be wrong. No alternative placement stated as rejected.
- Hot path = **ingestion only** (receive, envelope check, durable buffer, two landings). Rejected: payload validation or enrichment on the hot path, because the fix there is a redeploy rather than a rerun.
- **No processing of ours is real-time**; the test's phrase is reframed as transport, not computation.
- **GCS archive is not batch** — a live export subscription writing as events arrive; only the read-back is cold.
- **Lambda / speed layer rejected** — two implementations of every metric that must agree, to serve a latency the hour boundary already caps.
- **Continuous / streaming maintenance rejected** (stateful dedup on `event_id`, 1h TTL) — a backdated revenue share requires a "rebuild these named past days" operation a continuous aggregate cannot express, so a batch path exists regardless and the streaming design ships two execution models.
- **Cold path runs hourly, not once daily** — rejected: a single daily run leaves D-1 wrong for 24 hours.
- **Four repair triggers, one code path**: rerun (watermark never advanced) · trailing-3-day rebuild for lateness · targeted named-day rebuild for older data or backdated revenue share · GCS replay via BigLake `INSERT … SELECT` into Bronze.
- **Detection over prevention** for the out-of-window case — an alert fires when Silver writes outside Gold's trailing window ("detected, not noticed").
- Bronze is the **only table with an expiration**, so the hot/cold line doubles as the compliance boundary.

**TECH**
Pub/Sub (topic, envelope/topic schema, two export subscriptions), BigQuery (Bronze, Silver, Gold, `MERGE`, `INSERT … SELECT`), Cloud Storage (raw archive), BigLake external table. Implied but not named on this page: Dataform (referred to only as "SQL on a clock" and "the orchestrator"), the `pipeline_state` watermark table, Cloud Monitoring.

**TERMS**
hot path · cold path · the line (at Bronze) · envelope (the five named STRING fields) · *quiet work* (work that can produce a plausible wrong number nobody reports) · watermark ("a value, not a process") · replay · backfill · targeted rebuild · trailing 3-day window · lambda / speed layer · continuous maintenance · anonymisation boundary · "detected, not noticed" · one code path.

**NUMBERS**
- Hot path latency: **seconds**.
- Cold path: Silver **30 min**; Gold **hourly**; quality **hourly and daily**.
- Bronze / personal data expiration: **7 days**.
- Late-arrival rebuild window: **3 days** trailing; older than 3 days ⇒ targeted rebuild.
- Rejected streaming dedup: **1-hour TTL**, **~10 GB** of live keyed state.
- Lambda illustration: **4 seconds** (speed layer) vs **10 minutes** (batch) produce the same hourly figure at the same moment.
- Speed layer cost: **low thousands per month**, described as the smaller half of the bill.
- Single daily run: leaves D-1 wrong for **24 hours**.

**ASSUMES (taken as given from elsewhere)**
- 7-day raw retention ceiling and Silver as the durable, indefinitely retained source of truth — `intro/02`, `part_1/00`.
- Bronze partitioned hourly on `publish_time`, 7-day partition expiry — `part_1/05`.
- Silver watermark + `MERGE` semantics, and that the watermark is settable — `part_1/06`.
- Gold rebuilt hourly over a trailing 3 days, change-detected on `job_update_timestamp` — `part_1/04`.
- The GCS archive is a second export subscription that holds every message including those BigQuery declined — `part_1/01`.
- Envelope schema enforced at publish, refusal returned synchronously to the producer — `part_1/01`, `part_1/02`.
- The monitor that fires when Silver writes outside Gold's window — `part_1/01`.
- Revenue share joined in Silver with `valid_from`/`valid_to`, hence restatable from Silver without touching raw — `part_1/04`, `part_1/06`.
- Volume of ~23k events/s (implied by the ~10 GB state figure) — `intro/02`.
- The only intraday consumer is the DE team; no sub-hourly business consumer exists — `intro/02` rhythm line.
- An orchestrator, a change-detection step and a `MERGE` exist and would survive a streaming redesign — `part_1/02`, `part_1/04`.
