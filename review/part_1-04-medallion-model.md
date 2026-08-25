# Review — `part_1/04-medallion-model.md`

## Summary

The longest page in the write-up: it sets the rule for each medallion layer, defends a wide-and-permanent Silver against the 7-day raw ceiling, and then spends most of its length on three Gold decisions — hourly stored with daily as a view, bucketing on the auction's clock rather than the event's, and two fact tables because there are two denominators. It lands: both load-bearing modeling claims survive stress-testing, the arithmetic that can be checked checks out, and the failure-mode thinking (`is_settled`, coverage counters, self-healing window) is the best in Part 1 — what it does not do is price the one decision on the page that grows forever.

## Grade

- **Decision quality — A.** Twelve decisions, almost every one paired with the alternative and the reason it lost; the two claims most likely to be attacked both hold under pressure (see interview Q1 and the two-denominator check below), and the nine-row Rejected table contains real losers, not straw men.
- **Narrative — B.** The page has a spine ("type wide, aggregate narrow") and a genuine punchline (SSP 7's fill rate), but the punchline sits at 80% depth behind a matrix opening, and a section titled "two fact tables" is followed by a third table.
- **Operability — B.** `is_settled` on a watermark rather than a wall clock, NULL-never-zero, coverage counters, a 3-day window sized to a Friday failure found on Monday — all excellent; the cost paragraph then prices the rebuild cadence and leaves the unbounded line item unpriced.
- **Technical plausibility — B.** No errors I can find — the conformed-rollup claim, the partition-ceiling arithmetic and the additivity identity all hold — but two things a staff engineer will push on are asserted rather than argued: Silver's cluster keys, and how `auctions_with_bid` is actually computed.
- **Signal density — B.** Most prose is dense, but the two-denominator claim is made six separate times, six of the 26 schema rows carry no argument, and the summary table restates rows that the sections below restate again.
- **Overall — A.** The modeling reasoning here is the strongest thinking in Part 1 and I would ask about the bucketing decision out of interest; the soft spots are editorial or unstated, none of them are mistakes.

## Top findings

**1. [QUESTION] Silver is typed wide and retained indefinitely, and the page prices the rebuild cadence instead.**
- **What:** This page creates the only line item in the entire design that grows without bound — 2B rows/day × ~26 columns, forever, with columns deliberately added that no metric uses — and the marked Cost paragraph costs the hourly-vs-four-hourly rebuild (\~$450 vs \~$113) instead.
- **Why it matters to the evaluator:** Every other page prices exactly the decision it argues (Bronze grain \~$5,100, storage class \~3×, GCS \~$210); this one prices the cheap lever and skips the expensive one, and no other page in the write-up prices Silver storage either — so a CTO asking "what does this cost me in year three" gets no answer anywhere.
- **Fix:** Two clauses in the Cost paragraph: Silver's physical bytes per day and the resulting monthly figure at 12 and 36 months, plus the mitigation that is already true and unstated — the trailing 3-day rebuild window never touches older partitions, so all but three days of Silver sit in BigQuery long-term storage at half price.

**2. [QUESTION] Gold's grain includes the highest-cardinality dimension in the model, and the page never says how many rows that produces.**
- **What:** `gold_ssp` is keyed on `auction_hour, publisher_id, ad_unit_id, ssp_id, format, device, channel`; with ~300 publishers the row count turns entirely on ad-unit cardinality, which is stated nowhere in the write-up.
- **Why it matters to the evaluator:** Part 2 asserts that a Gold scan is "two to three orders of magnitude below the event layers", and that claim is only true if this grain actually compresses — at high ad-unit cardinality an "aggregate" of 1.5B bid/no_bid events can land within one order of magnitude of the events it summarises, which would quietly invalidate the copilot's cost story.
- **Fix:** One sentence with the expected rows per hour for each table and the implied compression ratio, plus the lever if it is wrong (drop `ad_unit_id` from `gold_ssp` and keep it only on `gold_opportunity`, where the auction count is 10-20× smaller).

**3. [QUESTION] Silver's partition and cluster keys appear as a cell in the summary table and are never defended — and the page's own methodology points elsewhere.**
- **What:** `auction_day` / `publisher_id, event_type, ad_unit_id` is asserted with no argument, while the very next page spends a full section establishing that the key question is *"what is the dominant query, and it is not a human's"*.
- **Why it matters to the evaluator:** Applying that rule to Silver gives a different answer — the dominant recurring read of Silver is the `MERGE`'s `ON t.event_id = s.event_id`, 48 times a day against a table with no expiration, and none of the three chosen cluster keys serve it — so an interviewer who read 2.2 first will ask why `event_id` is not the leading key.
- **Fix:** One sentence naming Silver's dominant reader and why the keys serve it (the Gold rebuild scans whole partitions and never filters, so the keys are for operational reads), or change the leading key to `event_id` and say why the MERGE won.

**4. [QUESTION] `auctions_with_bid` is the one measure that needs a per-auction pass, and the page says only where it is *not* computed.**
- **What:** The page states it cannot be derived in the view because the per-event evaluation is destroyed by aggregation, but never says how the Gold build produces it — while the Rejected table two inches away kills a self-join on `auction_id` as "a three-day shuffle on every hourly run".
- **Why it matters to the evaluator:** A staff engineer reads those two lines together and asks why one auction-level pass over 1.5B bid rows is affordable and the other is not; unanswered, the rejected row looks like it was chosen for the phrase rather than the cost.
- **Fix:** One clause — `COUNT(DISTINCT auction_id)` filtered to bid rows, grouped by the dimensions, inside the day partition already being rebuilt: one aggregation, not a join back to every event row, and on-demand billing charges bytes read, not shuffle.

**5. [POLISH] `is_settled` claims two hours and justifies one.**
- **What:** "Two hours because the auction lifecycle is bounded at one and its events publish within seconds" adds up to roughly one hour; the missing second hour is the 1-hour duplicate-arrival bound from the assumptions page, which this page never names.
- **Why it matters to the evaluator:** The whole page is built on stating the derivation rather than the conclusion, and this is the one number where a reader doing the arithmetic finds it short — it reads as a round figure dressed as a derived one.
- **Fix:** Five words: "one hour of lifecycle plus the one-hour retry bound, both measured in `quality_hour`."

## Cuts

**1. The denominator table (lines 87-90) — delete, ~75 words.** By the time a reader reaches it, "two denominators" has been stated in the section heading, in the paragraph explaining that an auction has no `ssp_id`, and in the measures table's two grains; the SSP 7 blockquote immediately below then makes the same point far better. Nothing is lost — the table is the fourth of six statements of one idea.

**2. The Silver column table: 26 rows → ~14, ~90 words.** Defensible as an artifact — a CTO does want to see the author can model a schema — but the prose already states the generating rule ("every structured non-PII field gets a column whether a metric uses it today or not"), so the table's only job is the exceptions. Cut the rows whose Note earns nothing (`event_id`/`publisher_id` "Envelope", the blank `ad_unit_id`), collapse `format, device, channel, country, placement_position` into one grouped row, and drop the four audit timestamps whose derivations appear verbatim as SQL comments in 2.3. What survives — the three *Typed wide* markers, "Null on `auction`", "For latency, never for bucketing" — gets louder for having less around it.

**3. Summary table, the `Retention` and `Personal data` rows — ~35 words.** Both restate `00-retention-anonymisation.md` in full, and the "type wide" paragraph ten lines below restates the retention logic a third time to make its own argument. Keep the restatement where it does work; delete the two cells that only announce it.

**4. "This is free rather than clever…" (line 60) — compress ~55 words to ~25.** The additivity identity is Part 2's semantic-layer argument and appears there almost verbatim. The claim this page needs is one clause: additivity over time and over dimensions are the same property, so a day is the exact sum of its 24 hours. Lost: a good phrase. Kept: the argument, and the ownership stays with the page that defines the rule.

**5. Rejected rows that restate prose finished five lines earlier — ~50 words.** "Flow attribution" and "Dimension tables / a star schema" both carry a second clause that repeats the section immediately above them. Trim each to its first clause; the table's job is to compress arguments the prose did not make, not to summarise the ones it did.

Total: ~300 words, ~13% of the page, with no argument removed.

## Interview questions this page invites

1. **"Why one Silver table when `bid` and `no_bid` are 80% of the rows?"** *Answered in one clause* — "splitting multiplies three mechanisms by five to save a predicate" — and the answer is stronger than the clause admits: the two Gold builds between them consume all five event types (`gold_opportunity` needs `auction` and `bid`, `gold_ssp` needs `bid`, `no_bid`, `win`, `impression`), so no split reduces the dominant read at all. Six more words would close the question permanently instead of inviting it.
2. **"How many rows a day is `gold_ssp` once `ad_unit_id` is in the grain — is it still an aggregate?"** *Not answered*, and Part 2's entire cost argument for the copilot rests on the answer. This is finding 2 as it will actually be asked.
3. **"Revenue is bucketed by the auction's hour; the SSP invoices by impression time. Which number do I reconcile against?"** *Half answered* — "at daily grain this barely matters" is the right defence and it is aimed at ratio distortion, not at reconciliation, so the reader has to make the connection themselves. One clause naming finance as the beneficiary of the daily tier would pre-empt it.

## Claims ledger

**DECISIONS**
- Bronze accepts everything, validates nothing — typed envelope + opaque `payload` JSON. Rejected: promoting `NUMERIC price` / `TIMESTAMP auction_timestamp` out of the payload (a cast can fail; validating is Silver's job).
- Only STRING fields promoted out of the payload, "because a STRING cannot refuse a value".
- One Silver table for all five event types. Rejected: one table per type ("multiplies three mechanisms by five to save a predicate").
- Silver typed wide, ~26 columns, every structured non-PII field gets a column. Rejected: a narrow Silver (only correct when raw is kept forever; here omission is permanent at day 7).
- Every payload-derived column nullable. Rejected: `NOT NULL` (hands a third party the ability to stop the pipeline); rejected: `'unknown'` or defaults.
- `SAFE_CAST` failures become NULL; only a missing `auction_timestamp` diverts the row to `silver_rejects`.
- Money computed in Silver, on `impression` rows only. Rejected: enrichment at ingest (a backdated revenue share becomes a GCS replay instead of a rerun over named partitions); implicitly rejected: recognising revenue on `bid` or `win`.
- FX rate and revenue share as declared external tables over GCS, read in place — no loader, no schedule.
- Revenue share versioned with `valid_from`/`valid_to` in Silver. Rejected: a slowly-changing dimension in Gold.
- Gold hourly stored, daily as a view over it. Rejected: daily stored + hourly derived; rejected: two independently built tables.
- Cohort bucketing on `auction_hour`. Rejected: flow attribution (each event in its own hour) — its error-cancellation defence fails at a deploy, the case the hourly tier exists for.
- `auction_timestamp` denormalised onto every Silver row. Rejected: a self-join on `auction_id` (a three-day shuffle per run).
- `is_settled` published as a column. Rejected: holding unsettled hours back; rejected: a wall-clock settlement rule (watermark instead, so a drain keeps hours unsettled).
- `sources_total` and `sources_reporting_impressions` published per row; a metric a source cannot report is NULL, never 0.
- Two Gold fact tables + `quality_hour`. Rejected: a single fact table at SSP grain (cannot express `auctions`; 10-20× overcount or a placeholder row).
- `responses` stored on `gold_opportunity` although it rolls up from `gold_ssp` — for readability without a join.
- `auctions_with_bid` computed during the Gold build. Rejected: deriving it in the view.
- Both fact tables partitioned `DATE(auction_hour)` — daily partitions holding hourly rows. Rejected: hourly partitions (10,000-partition ceiling).
- Hourly rebuild of the days whose Silver rows changed, inside a trailing 3-day window. Rejected: unconditional rebuild of the whole window (~5× scan); rejected cadences: four-hourly, 30-minute.
- Change detection on `job_update_timestamp`. Rejected: `ingestion_timestamp` (a clock Pub/Sub owns; a late Silver write lands behind Gold's line and is never rebuilt).
- No dimension tables — every dimension is a column on the fact row. Rejected: a star schema in Gold.
- `quality_hour` at `auction_hour × publisher_id`, placed in Gold so the copilot's existing access reaches it. Implicitly rejected: a global total ("a total names nobody").
- One job builds both fact tables in the same run.

**TECH**
BigQuery (partitioning, clustering, `MERGE`, `SAFE_CAST`, external tables over GCS, 10,000-partition limit); Pub/Sub (`publish_time`); Cloud Storage (FX and revenue-share reference tables); the Prebid wrapper (stamps `auction_timestamp`). Tables named: `silver_events` (implied), `silver_rejects`, `gold_opportunity`, `gold_ssp`, `quality_hour`. Dataform is *not* named on this page.

**TERMS**
Bronze/Silver/Gold layer rules; envelope; *type wide, aggregate narrow*; typed wide (marker for columns no metric uses today); cohort attribution vs flow attribution; `is_settled`; watermark (on `publish_time`); conformed rollup; additive measure; `auctions`, `auctions_with_bid`, `responses` (= bids + no_bids across every SSP invited), `bids`, `no_bids`, `wins`, `impressions`, `gross_revenue`, `publisher_payout`; `auction_day`, `auction_hour`, `event_timestamp`, `job_insert_timestamp`, `job_update_timestamp` (Gold's change-detection clock); `sources_total`, `sources_reporting_impressions`, `late_beyond_1h`; denominator (as the thing that distinguishes the two fact tables); pseudonym / "unlinkable from day 8".

**NUMBERS**
5 event types; ~26 Silver columns; Bronze 7-day retention, Silver/Gold indefinite; settlement at `auction_hour + 2h`; auction lifecycle bounded at 1 hour; trailing 3-day rebuild window (a Friday failure found Monday sits at D-3); hourly rebuild; \~$450/month hourly, \~$113 four-hourly, \~$900 at 30 minutes; 8,760 hourly partitions per year against a 10,000 ceiling; ~5× scan for an unconditional rebuild; SSP 7 invited to 4% of auctions; 10-20× opportunity overcount under a single SSP-grain table; `device` has four values.

**ASSUMES**
- The Prebid wrapper stamps `auction_timestamp` once and all five events echo it; sources report it at different paths (2.3 maps them).
- The 1-hour auction lifecycle bound *and* the 1-hour duplicate-arrival bound (assumptions page) — the second is used in the 2h settlement rule but never named here.
- Bronze's 7-day expiry is what makes `auction_id` unlinkable from day 8 (page 00).
- Silver's `MERGE`, watermark and per-source `CASE` mapping exist as described in 2.3.
- The semantic layer's rule that every stored measure is additive — a **forward reference** to Part 2's page 2.1, five pages later; the rule is restated inline, so the page stays self-contained.
- `publisher_id` and `ad_unit_id` are usable as flat string dimensions; Part 2's `resolve_entity` further assumes they are human-readable names, which this page's no-dimension-tables decision makes load-bearing.
- On-demand BigQuery pricing (\$6.25/TiB, stated on 2.2) behind the \~$450/month figure.
- A single reporting currency, an FX table owned by finance and a revenue-share table owned by the contract, both non-overlapping in validity.
- Days and hours are UTC — defined in `CONTEXT.md`, which is not part of the write-up the reviewer sees; the daily tier's timezone is stated on no page.
- Two Gold grains (hourly, daily) requested by the client; ~10 users with no entitlement scoping, so no access-control reason for dimension tables.
