# Review — `part_1/06-dedup-sql.md` (2.3 Deduplication, Bronze → Silver)

## Summary

The page answers the test's one mandated artifact — a window function deduplicating on `event_id` — in seven lines, then spends the rest arguing that the window function alone is wrong across runs and that a `MERGE` keyed on `event_id` is what makes the dedup actually hold. It lands: the extra 2,000 words are the strongest thinking in Part 1, and the one place the page loses altitude is the tail, where a 15-row rejection table restates prose that already made the same points.

## Grade

- **Decision quality — A.** Every choice is paired with the alternative it beats, and the central split (*the window function makes the `MERGE` legal, the `MERGE` makes the dedup correct*) is a real insight, not a restatement of the requirement.
- **Narrative — A.** Opens with the asked-for answer in seven lines, then earns each subsequent section with a claim as its heading; only the last third sprawls into a bullet list and a table wall.
- **Operability instinct — A.** Catch-up over fixed lookback, keyed writes so failure means doing work twice rather than skipping, `RETURN` on an empty batch, temp table dropped, settable watermark for backfill, and detection where prevention is too expensive.
- **Technical plausibility — B.** The SQL runs and the mechanism is right, but three claims a staff engineer would push on: the pruning fallback sentence contradicts the page's own `require_partition_filter`, the re-stamp worked example assumes an outcome that only holds when `batch_days` has one day in it, and the headline query parameterises differently from the script whose pruning argument depends on that difference.
- **Signal density — B.** Dense, but the rejection table repeats the prose almost verbatim (the `MERGE` error string appears twice, word for word) and one paragraph defends the Dataform template against a challenge nobody would make.
- **Overall — A.** Strong senior work; I would open the interview on this page.

## Top findings (max 5)

**1. [QUESTION] The 2-minute watermark offset is a magic constant with no stated source and no detector.**
- **What:** The incident narrative demonstrates ~6 seconds of publish-to-queryable skew and the design then jumps to a 2-minute safety margin, with nothing on this page or elsewhere measuring that skew or alerting when it exceeds 2 minutes.
- **Why it matters to the evaluator:** The whole watermark argument rests on this number, and the failure it fails at is exactly the one the page describes as unsurvivable — a row behind the line, merged by nothing, counted by nothing, no job failed. Under a *partial* subscription lag (some writers ahead, some behind by minutes), `batch_max` advances past rows not yet written and they are lost silently, which also undercuts 1.1's claim that "the backlog drains, Silver's watermark reads the rows it never saw."
- **Fix:** One sentence saying the offset is set from the measured p99.9 of `publish_time` → queryable skew, and one row added to the quality job (or the 1.1 monitor table) that counts Bronze rows arriving with `publish_time` below the current watermark. The page holds itself to *"being wrong must be visible and rerunnable"* two sections later; apply it here.

**2. [QUESTION] The re-stamp worked example has a second, worse outcome the page does not name.**
- **What:** `batch_days` is every `auction_day` in the batch, not just the new one, so near midnight it is `{D4, D5}` — the `ON` clause *does* reach the D4 target row, the `MATCHED` branch fires, and the row is updated with `auction_hour` in D5 while `auction_day` stays D4 because it is deliberately excluded from `UPDATE SET`.
- **Why it matters to the evaluator:** The page's example says the `ON` clause "looks in D5 only, finds nothing, and inserts a second row" — true only when the batch spans one day. The other outcome leaves a Silver row whose partition key disagrees with its own grain column, which Gold buckets on; and 2.1 states Silver's grain as one row per `event_id`, where what this design actually guarantees is one row per (`event_id`, `auction_day`).
- **Fix:** State the real invariant once — *at most one row per `event_id` per `auction_day`* — and add a clause acknowledging that when the batch spans midnight the row is updated in place, leaving `auction_day ≠ DATE(auction_timestamp)`, which is the same producer bug surfacing in a second shape and is caught by the same quality counter.

**3. [QUESTION] "Where pruning stops, results stay correct and only the bill changes" is not true on this Silver table.**
- **What:** The page asserts twice that `silver_events` carries `require_partition_filter = TRUE` (it is the argument that kills Dataform's native incremental), and on such a table a predicate BigQuery cannot use for partition elimination is *rejected*, not billed.
- **Why it matters to the evaluator:** The paragraph explicitly invites the reader to check the reasoning, so the one sentence that is wrong is the one a staff engineer lands on — and the correct answer is a better story than the hedge, because it fails loudly at the first run rather than quietly on the invoice. Secondarily, the load-bearing claim is about a *scalar* script variable while the actual predicate is `IN UNNEST(<array variable>)` inside a `MERGE` `ON`, which is a step further out than the sentence covers.
- **Fix:** Replace the fallback sentence with "and if BigQuery ever stops pruning it, `require_partition_filter` rejects the statement rather than silently billing a full scan." Add half a clause confirming the array-variable form prunes (a dry-run byte figure would settle it outright).

**4. [QUESTION] Revenue is computed once, at merge time, against reference data that may not exist yet.**
- **What:** `gross_revenue` joins `ref_fx_rate` on `fx.day = DATE(t.auction_timestamp)`, and Silver merges an event within 30 minutes of the auction — but a same-day FX rate owned by finance typically does not exist that early, and the `MERGE` never revisits the row once written.
- **Why it matters to the evaluator:** An interviewer will ask what `gross_revenue` is for an auction 20 minutes old. The null is *caught* (1.1's assertion on null `publisher_payout` blocks Gold), so this is not a silent-wrong; but it means the design's normal daily state is a blocked Gold build, and no repair path for already-merged nulls is stated on the page that computes the money.
- **Fix:** One line on the FX table's own convention (previous close carried forward, or a rate valid from D-1) and one line saying a late rate is repaired by the same settable-watermark rewind already described, not by a new mechanism.

**5. [POLISH] The headline query uses `@watermark` / `@batch_max`; the script uses script variables.**
- **What:** The seven-line answer is parameterised, the script that actually runs declares variables, and 100 lines later the page argues that the distinction between a fixed-before-execution value and a subquery is what makes pruning work.
- **Why it matters to the evaluator:** Having told the reader the mechanism matters, using a different one in the artifact the test asked for invites a question with no payoff.
- **Fix:** Use the same form in both blocks, or add four words to the first block noting that a query parameter prunes for the same reason.

## Cuts (minimum 2)

1. **The Rejected table, rows 1–2 and 5–9 and 12** (~190 words). "Window function alone", "`MERGE` alone", "wall-clock ceiling", "fixed 3h read window", "partition filter in a subquery", "dropping the partition filter", "`ORDER BY ASC`" and "each statement reading Bronze directly" are each argued in full in the prose above — the `MERGE` error string is quoted twice verbatim, three paragraphs apart. Keep the rows whose argument appears *nowhere else* (`SELECT DISTINCT`, dedup at ingest, Dataform's native incremental, push convergence to producers, one SQLX model per source, `CAST`, overlapping validity windows). Lost: nothing; gained: the eight surviving rows read as new information instead of a checklist.
2. **The template defence in "One model, not one per source"** (~45 words): "Nothing evaluates it at runtime — BigQuery receives ordinary SQL, identical to the hand-written version … and deleting the template call and pasting the generated blocks in gives the same compiled SQL, the same cost and the same results." Three restatements of one point, pre-empting an objection nobody raises about a compile-time macro. Keep "adding a source is a data change instead of a code change"; cut the rest.
3. **The tail of the loud-vs-silent paragraph** (~40 words): the `valid_from`/`valid_to` sentence duplicates the last row of the Rejected table. Keep it in one place — the prose, since that is where the loud/silent frame it depends on lives.
4. **The upsert aside in the watermark paragraph** (~30 words): "An upsert rather than an `UPDATE` because the run that finds no line is the run that writes it, so a rebuilt environment needs no deployment step to seed." The `MERGE` shown says this; the sentence is oral defence material, not page content.
5. **Bullet 3 of "Four choices inside the run"** (~30 words of compression): 130 words carrying two arguments (why the `ON`-clause predicate prunes; why a hardcoded day range fails). Split them or drop the backfill sentence, which repeats the "settable watermark" point made later.

## Interview questions this page invites

1. **"Where does two minutes come from, and what tells you the day it isn't enough?"** — Not answered. The page justifies *that* there is an offset, never its size, and names no signal for skew beyond the margin.
2. **"A producer retries an event at 00:03 and re-stamps the auction into the new day. How many rows does Silver hold, and what is the partition key of each?"** — Half answered: the page names the two-row outcome and calls it a trade, but not the in-place update that happens when the same batch also contains previous-day auctions.
3. **"Silver requires a partition filter. Show me that `t.auction_day IN UNNEST(batch_days)` in a `MERGE` `ON` clause actually prunes — and what happens if it doesn't?"** — Asserted, not evidenced, and the stated consequence of failure ("only the bill changes") is inconsistent with the table option the page relies on elsewhere.

## Claims ledger

**DECISIONS**
- `ROW_NUMBER()` + `QUALIFY` for in-batch dedup — rejected: `SELECT DISTINCT` / `GROUP BY event_id` (no tie-break, cannot express "keep the later copy").
- Keep the **last** copy (`ORDER BY publish_time DESC`) — rejected: `ASC`/keep-first (defensible, but batch rule and `MERGE` rule would then disagree).
- `MERGE ON event_id` into Silver for cross-run dedup — rejected: window function alone (batch-scoped; the duplicate usually lands in a later run).
- Keep the window function *even with* the `MERGE` — rejected: `MERGE` alone (loud failure on a known `event_id`; silent double-insert on a new one, which is the common case).
- Dedup after Bronze in SQL — rejected: dedup at ingest (~10 GB live keyed state on the hot path; silent loss when state is lost).
- Per-source JSON path mapping, declarative in Dataform, compiled to one `CASE source_id` per column — rejected: one SQLX model per source (N copies of the `MERGE`/watermark/assertions); pushing convergence to the producers (SSPs are third parties; we can demand an envelope format, not field semantics).
- Watermark stored as a row in `pipeline_state` (one per model) — rejected: Dataform native incremental / `SELECT MAX(ingestion_timestamp) FROM ${self()}` (refused by `require_partition_filter`; unsettable for backfill).
- Watermark semantics = *process everything since the last success* — rejected: fixed 3h lookback (no catch-up; a draining backlog is skipped for good).
- Ceiling `batch_max` read from the data — rejected: `CURRENT_TIMESTAMP()` wall-clock ceiling ("a ceiling read from the data is a value we have seen; a clock reading is a prediction").
- Watermark saved at `batch_max − 2 minutes`; overlap discarded by the keyed `MERGE`.
- `pipeline_state` written as an upsert `MERGE`, not `UPDATE`, so a rebuilt environment self-seeds.
- Partition filter `t.auction_day IN UNNEST(batch_days)` inside the `MERGE` `ON` clause, `batch_days` derived from the batch — rejected: the same predicate as a subquery (no pruning); a hardcoded "today and yesterday"; dropping the filter entirely.
- No `WHEN NOT MATCHED BY SOURCE` branch (named as the clause that would force a full target scan).
- One pass over `payload` into a temp table; every later statement reads the temp table — rejected: each statement reading Bronze directly (doubles the largest scan).
- `SAFE_CAST` — rejected: `CAST` (one malformed value would fail the whole run).
- `auction_day` excluded from `UPDATE SET`; `auction_hour` included.
- Rows with no usable `auction_timestamp` diverted to `silver_rejects` as keys + reason, never payload.
- Day-scoped dedup accepted as a trade, closed by detection (quality job counts `event_id`s with more than one `auction_timestamp`) rather than prevention.
- Non-overlapping `valid_from`/`valid_to` on the revenue-share table treated as a correctness property — rejected: overlapping windows (fan-out duplicates after dedup).
- `RETURN` on an empty batch; `DROP TABLE batch` at the end of the script.

**TECH**
BigQuery — `QUALIFY`, `ROW_NUMBER() OVER`, `MERGE` (`WHEN MATCHED` / `WHEN NOT MATCHED THEN INSERT ROW`), `SAFE_CAST`, `JSON_VALUE`, `CREATE TEMP TABLE`, scripting (`DECLARE`, `SET`, `IF`, `RETURN`), `ARRAY_AGG(DISTINCT … IGNORE NULLS)`, `IN UNNEST`, `TIMESTAMP_SUB`, `TIMESTAMP_TRUNC`, `SELECT * EXCEPT`, `require_partition_filter`, partition pruning, query parameters vs script variables. Dataform — declarative mapping, `${col(…)}` compile-time template, `${self()}`, native incremental models, SQLX. Pub/Sub — `publish_time`, the subscription writing Bronze in parallel. Tables named: `bronze_events`, `silver_events`, `silver_rejects`, `pipeline_state`, `ref_fx_rate`, `ref_revenue_share`, temp `batch`.

**TERMS**
Watermark (`last_success` per model) · ceiling / `batch_max` · `batch_days` · overlap ("saved two minutes behind the ceiling") · `ingestion_timestamp` (Bronze `publish_time`, renamed once, the `MERGE` tie-break) · `auction_timestamp` (carried, not generated) · `auction_day` (Silver partition key) · `auction_hour` (Gold's grain) · `job_insert_timestamp` (kept on update) / `job_update_timestamp` (rewritten on both) · rejects boundary · day-scoped dedup · loud vs silent failure · envelope format vs field semantics · "stamped in order" vs "appear in order".

**NUMBERS**
Seven lines for the asked-for query · Silver runs every 30 min · duplicates arrive up to 1 hour late · first-run watermark seeded 7 days back · watermark saved `batch_max − 2 min` · overlap ≈ 7% of the Bronze read · `payload` ≈ 90% of row width · rejected ingest-side dedup: ~10 GB live state for a 1h window at 23k/s · rejected fixed lookback: 3 hours · unclaimed temp table lingers 24 hours · Bronze retains the reject's payload 7 days · repair scope after a re-stamp: two days · narrative timestamps 10:29:58 / 10:29:59 / 10:30:04 · backlog scale "two-day vs two-minute".

**ASSUMES (taken as given from elsewhere)**
1-hour duplicate-arrival and auction-lifecycle bounds (`intro/02`) · Silver's 30-min cadence and Bronze's continuous ingest (`intro/02`) · Bronze DDL: hourly partition on `publish_time`, `require_partition_filter = TRUE`, 7-day expiry (2.2) · bullet 2.2's scan figures already assume the single-pass temp table · Silver: `auction_day` partition, `require_partition_filter = TRUE`, **no expiration** (2.1/2.2) · Silver's ~26 typed columns and the "everything from payload is nullable" rule (2.1) · `auction_timestamp` stamped once by the Prebid wrapper and echoed by all five events (2.1) · payload schemas differ per source and convergence is an objective (`intro/02`) · `quality_hour` and the quality job exist and run hourly (2.1) · Dataform is the runtime and the compile step (1.2) · `ref_fx_rate` / `ref_revenue_share` exist as declared external tables owned outside the pipeline (2.1) · Gold rebuilds a trailing 3-day window (2.1) · `pipeline_state` is also read by the watermark-age monitor (1.1).
