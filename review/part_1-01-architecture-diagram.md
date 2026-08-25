# Review — `part_1/01-architecture-diagram.md` (Bullet 1.1)

## Summary

This page answers the test's headline deliverable — a GCP architecture from raw ingestion to BI — by drawing the picture, walking it in eight hops, and then spending its second half on the failure modes that leave every job green. It lands: the two arguments that carry it (a safety copy that has never been inside BigQuery; five signals for *wrong while successful*) are the kind of thing a CTO asks about out of interest, and the things that cost it are line-level, not structural.

## Grade

- **Decision quality — A.** Two writes vs one write and a copy is a named alternative killed with a specific argument (the copy must sit *upstream* of the system it protects against), and the assertion gate is placed at Gold with the reason it is not at Silver.
- **Narrative — A.** Opens with the shape and the deliberate absence, walks the path once, then pivots to "every signal below is a way this pipeline can be wrong while every job reports success" — the reader is led, not enumerated at.
- **Operability instinct — A.** Half the page is monitoring, and every row states the failure a job-failure alert would miss; the watermark-age left join is a real operator's detail.
- **Technical plausibility — B.** The Pub/Sub, Dataform and BigQuery mechanics are accurate and specific, but the `publisher_payout` assertion and the treatment of dead-lettering as a schema-only event are both things a staff engineer would push on.
- **Signal density — B.** A latency column that says "seconds" four times, a monitor defined twice in consecutive sentences, and an opening that restates the parent page nearly verbatim.
- **Overall — A.** Top of the range: three A dimensions carry it, and everything below is a one-line correction rather than a design error.

## Top findings (max 5)

**1. [BLOCKER] The `publisher_payout` assertion hands an SSP a kill switch on Gold.**
- What: the assertion fires when "any row resolves to null" on an `impression`, but `publisher_payout` derives from `price`, which 2.1 declares nullable-by-design ("an SSP that never reports X is not sending garbage"), so a source that stops reporting price on impressions blocks the Gold rebuild for every publisher.
- Why it matters: it contradicts the nullability rule the sister page states as a principle — *"requiring more hands a third party the ability to stop our pipeline"* — and a hard gate that a third party can trip is the one thing an interviewer will test.
- Fix: scope the assertion to the join failure it is actually about — `gross_revenue IS NOT NULL AND publisher_payout IS NULL` (money computed, share missing) — and say in the row that a null `price` is a *monitor*, not a gate.

**2. [QUESTION] The watermark-age monitor runs inside the system it is designed to watch.**
- What: it exists to catch "a disabled schedule or a deleted release config", but it is itself a Dataform action on the quality tag, so the exact failure it names would also stop the monitor from running.
- Why it matters: the page calls this row load-bearing; a dead-man's switch that dies with the patient is the first thing an operator checks.
- Fix: one clause saying what fires out-of-band — a Cloud Monitoring absence-of-metric alert on the quality job's log line, or the quality workflow held in its own release config so the two cannot be deleted together.

**3. [QUESTION] Dead-lettering is described only as a permanent failure, never a transient one.**
- What: hop 4 gives two causes, both schema-shaped, but a Pub/Sub BigQuery subscription with a dead-letter policy also forwards messages after `max_delivery_attempts` — so a two-hour BigQuery-side outage at 23k/s dead-letters hundreds of millions of good messages.
- Why it matters: it is the exact scenario the closing incident narrative claims self-heals ("the backlog drains, no human is involved"), and a staff engineer will spot the gap between the two paragraphs.
- Fix: state the `max_delivery_attempts` value and one sentence on the transient case — either it is high enough to ride out the outage, or the DLQ replays from the archive by the runbook already drawn.

**4. [QUESTION] The diagram's edges disagree with the page in two places.**
- What: `quality_hour` draws straight to the BI/copilot node, bypassing the semantic layer that hop 7 and Part 2's 3.1 insist is the agent's *only* grant ("no grant on the Gold base tables exists anywhere"); and the dead-letter topic is a terminal node with no consumer, although it is the one signal with a native metric.
- Why it matters: the picture is what a CTO reads first, and here it grants the agent an access the text spends a page refusing.
- Fix: route `quality_hour` through the semantic-layer cluster like the other two facts, and add a dotted DLQ → Monitoring edge so the depth monitor exists on the page as well as in the prose.

**5. [POLISH] The diagram will not survive being rendered at page width.**
- What: 3464 × 1312 (2.6:1) with node labels carrying three lines of DDL; at docsify's content width the labels are unreadable without opening the image separately.
- Why it matters: this is the deliverable the bullet literally asks for, and it is the one artefact a reader judges before reading a word.
- Fix: move the Bronze DDL text off the node (2.2 owns it) and raise node font size, or split the alerting cluster onto a second rank to buy back aspect ratio.

## Cuts (min 2)

1. **The `Latency` column, hops 1–4** (~25 words + a column). Four consecutive "seconds" restating a fact already in the intro sentence and on the diagram's own cluster label ("Hot path — seconds"). Keep the column only for hops 5–8, or fold the cadences into the Mechanism cells and drop the column entirely. Nothing is lost.
2. **The duplicated monitor definition, in the "What pages" paragraph** (~20 words). "A **monitor** alerts into the team's channel and stops nothing" repeats "whose failure reaches the same log-based alert and blocks nothing" from twenty words earlier; "So the split is dependency wiring, not two systems" is a meta-comment on a distinction the next sentence makes better. Cutting both makes the paragraph parse on first read, which it currently does not.
3. **The opening service enumeration** (~30 words). "Six GCP services — Pub/Sub, Cloud Storage, BigQuery, Dataform, Cloud Logging, Cloud Monitoring — in two shapes… Left of Bronze… Right of Bronze…" is near-verbatim `part1-pipeline.md`, one click earlier. Compress to a half-sentence and get to "that box is absent here, and its absence is the design" in the first line — which is the sentence that earns the page.

## Interview questions this page invites

1. **"What is `max_delivery_attempts` on the BigQuery subscription, and what does a two-hour BigQuery outage do to the dead-letter topic at 23k/s?"** Not answered — hop 4 lists only permanent causes, and the incident narrative assumes the failure drains itself.
2. **"Your watermark monitor catches a deleted release config. What runs the monitor after the release config is deleted?"** Partially answered — hop 8's "its own tag and schedule" is the start of an answer, but a separate schedule inside the same release config does not survive the failure being described.
3. **"An SSP stops sending `price` on impression events. Which of your five signals fires, and does Gold stop building for all 300 publishers?"** Not answered, and the current wording says yes.

## Claims ledger

**DECISIONS**
- No Dataflow between topic and warehouse — rejected; the GCP reference architecture is named as the alternative, argument deferred to 1.2.
- Two export subscriptions from one topic — rejected alternative: a scheduled export Bronze → GCS (saves the second export fee, but places the safety copy downstream of the system it protects against, and would not hold messages BigQuery declined).
- Producer splits five envelope fields (`event_id`, `source_id`, `publisher_id`, `ssp_id`, `event_type`); everything else stays under `payload`.
- Partition key is Pub/Sub `publish_time` — "a clock no publisher can skew".
- GCS archive: Cloud Storage export subscription, Standard class, 7 days, never passes through BigQuery.
- Dead-letter topic attached to the BigQuery subscription; topic-schema violations refused synchronously at publish instead.
- One delivery path for all alerts (Cloud Logging → log-based alert → team channel) — rejected alternative: Cloud Monitoring querying BigQuery, stated as impossible.
- Monitor vs assertion split; assertions gate the **Gold** rebuild and never the Silver run — rejected alternative: a gate upstream of Silver, because it stalls anonymisation while the 7-day clock runs.
- `dependOnDependencyAssertions: true` on the Gold action, so the block is real rather than assumed.
- Lateness alerted as a ratio against a trailing-week baseline — rejected alternative: a raw non-zero late count (would page continuously at 23k/s).
- Watermark-age monitor via `UNNEST([...])` left-joined to `pipeline_state` — rejected alternative: querying `pipeline_state` alone (cannot report an absent row).
- Semantic views are the interface for both BI and the Part 2 agent; daily is a view over hourly.
- Gold rebuild scoped to changed days within a trailing 3-day window.

**TECH**
Pub/Sub (topic, topic schema, `publish_time`, BigQuery export subscription, Cloud Storage export subscription, dead-letter topic); Cloud Storage (Standard class); BigQuery (`bronze_events`, `silver_events`, Gold, `quality_hour`, `pipeline_state`, semantic views, `JSON` column, `MERGE`, window function); Dataform (SQLX, tags, workflow invocations, release configs, assertions, `dependOnDependencyAssertions`); Cloud Logging (log-based alert); Cloud Monitoring; Dataflow (named, absent). Diagram only: BigLake replay, `ref_fx_rate` / `ref_revenue_share` external tables, `gold_opportunity`, `gold_ssp`, `v_opportunity_hourly/_daily`, `v_ssp_hourly/_daily`.

**TERMS**
Envelope (the five named STRING fields the topic schema declares) · payload (opaque JSON beneath it) · hot path / cold path (line at Bronze) · two shapes (Google-operated config vs SQL on a clock) · monitor (alerts, blocks nothing) · assertion (Dataform action that fails and blocks Gold) · watermark · "a ceiling fixed from the data" · `late_beyond_1h` · dead-letter depth · settled / coverage (diagram labels).

**NUMBERS**
6 GCP services · 8 hops · 5 envelope fields · hops 1–4 latency "seconds" · Silver every 30 min · Gold hourly · quality hourly plus a daily tier · watermark-age thresholds 90 min (Silver) and 3 h (Gold) · Gold trailing 3-day window, alert on Silver writes older than D-3 · lateness ratio vs trailing-week baseline · ~23k events/s · GCS archive 7 days, Standard · "past day 7 there is no rebuild path" · incident: 4-hour outage from Friday 21:00, repaired Saturday 01:00. Diagram adds: Bronze 7 days (compliance), subscriptions retain undelivered 7 days.

**ASSUMES (taken as given from elsewhere)**
7-day raw retention ceiling and Silver as source of truth (`00-retention`) · the Dataflow rejection argument (1.2) · Dataform chosen over Composer (1.2) · the 1-hour arrival bound behind every window (`intro/02`) · `pipeline_state` and its `last_success` column (2.3) · Gold's 3-day rebuild window, `quality_hour`, `publisher_payout` and the revenue-share join (2.1) · Bronze DDL and `publish_time` partitioning (2.2) · that the Part 2 agent reads the semantic views only (Part 2, 3.1) · that the producer will supply the envelope split.
