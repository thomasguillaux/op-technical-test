# Review — `part_1/05-bronze-partitioning.md` (Bullet 2.2)

## Summary

This page defends a Bronze DDL — hourly partitions on Pub/Sub's `publish_time`, clustering on `publisher_id, ssp_id, event_type`, 7-day expiry, and two dataset options — against the test's literal ask for "partitioned by date" with fast queries on `publisher_id`, `ssp_id` and event date. It lands: the DDL is syntactically clean, every number I checked reconciles, and the central move (the dominant Bronze query is a machine's, not a human's) is the kind of reframing that earns an interview slot — but the page never turns that same reframing on its own clustering decision.

## Grade

| Dimension | Grade | Why |
|---|---|---|
| Decision quality | **A** | Clock and grain are each argued against a priced alternative, and the reservation option carries a reinstate threshold (~450 TiB/month) rather than a dismissal — the one gap is that `publish_time` is never considered as a cluster key. |
| Narrative | **A** | Artifact first, then "two choices need defending: which clock, and which grain", then the test's literal word answered on its own terms; a busy reader is led, not enumerated at. |
| Operability instinct | **B** | Strong on failure modes (skewed clock, unfiltered-scan typo) and on how the design evolves if lateness worsens, but silent on how the grain itself migrates and on what watches the $5,100 lever after launch. |
| Technical plausibility | **A** | The 10,000-partition limit, the 48h time-travel minimum, LOGICAL/PHYSICAL semantics, $6.25/TiB, the 16-days-of-bytes derivation and the 450 TiB slot break-even all check out; two small arithmetic slips, no wince. |
| Signal density | **B** | Very high in the grain and clock sections; the Rejected table is four-sixths restatement, and the page's sharpest arithmetic defends its smallest number without saying so. |
| **Overall** | **A** | A strong senior candidate wrote this. I would open the interview on the clustering order. |

## Top findings

**1. [QUESTION] The page proves the dominant query is Silver's watermark read, then picks cluster position 1 by a different criterion and never reconciles them.**
- What: "The dominant Bronze query is not a human's — it is Silver's watermark read, 48 times a day" carries the grain decision; three sections later position 1 goes to `publisher_id` because "every operational or reprocessing query names one" — i.e. a human's. `publish_time` as a leading or trailing cluster key is neither priced nor rejected.
- Why it matters: on the page's own arithmetic the gap is visible — each run reads two ~62 GB partitions to find ~31 GB of rows, so the unpruned remainder is roughly half the ~$1,000/month hourly figure, an order of magnitude more than the storage-billing decision the page argues at length. A reader who accepts the grain argument will immediately ask why it stops at the partition boundary.
- Fix: one paragraph plus a Rejected row. The defensible answer is already implicit — the partition already satisfies the time predicate, so a leading time key would prune only the sub-hour remainder, on rows the automatic re-clusterer has not yet touched, while demoting the two keys the test named by name.

**2. [QUESTION] "Silver's dataset is PHYSICAL, because nothing there expires" applies the page's own rule with the wrong test.**
- What: the paragraph above it correctly identifies *time-travel and fail-safe bytes*, not expiry, as what kills PHYSICAL — and Silver is `MERGE`d 48 times a day forever, which is the standard way to generate time-travel bytes; expiry is only the Bronze-specific accelerant.
- Why it matters: the page hands a reviewer a sharpened version of its own argument and then walks into it in the following clause. This is the one sentence on the page a staff engineer can attack using nothing but the page.
- Fix: either drop the Silver clause (it is a claim about another table on a page about Bronze) or argue it in one line — the `MERGE` touches at most two `auction_day` partitions per run and appends more than it rewrites, so rewritten bytes stay a small fraction of a table whose live bytes grow without bound, and the 3.4:1 compression clears the unadjusted 2:1 break-even.

**3. [QUESTION] Partition granularity is the one property in this DDL that cannot be `ALTER`ed, and the page's biggest lever rests on it with no migration story.**
- What: the page states the conditions under which the arrival-window assumption moves ("if lateness worsens the arrival range widens by exactly the measured amount") but not what happens if the *grain* has to move — for instance if Silver's cadence changes, or if the measured lateness bound makes hourly the wrong unit.
- Why it matters: a CTO reading "$5,100/month on one clause of DDL" will ask what it costs to be wrong about that clause; unanswered, the page's confidence reads as untested.
- Fix: one sentence. Bronze is a 7-day table with a GCS archive behind it, so a grain change is create-the-new-table, re-point the subscription, and let the old one age out — the cheapest schema migration in the design, and the reason the lever is safe to pull.

**4. [POLISH] The 25-partition bound does not compose the page's own two one-hour bounds.**
- What: "an auction reaches its final state within an hour *and* a retry lands at most an hour after the original" gives a worst case of D+1 02:00, i.e. 26 partitions and ~8% overhead, not 25 and 4%.
- Why it matters: the conclusion is unaffected, but this page's authority *is* its arithmetic, and it is the one figure on it a careful reader can falsify from the page's own sentence.
- Fix: say 26 and ~8%, or state explicitly that the retry bound is measured from the auction rather than from the original send, so the two bounds do not stack.

**5. [POLISH] "`no_bid` is 75-80% of volume" contradicts the business assumptions page.**
- What: `intro/02` says `bid` + `no_bid` together are 75-80% of the count; this page attributes the whole share to `no_bid` alone.
- Why it matters: the number is load-bearing here (it is the argument for `event_type` being the coarsest-but-biggest filter), and cross-page numeric drift is the cheapest credibility loss available.
- Fix: "`bid` + `no_bid` together are 75-80% of volume" — the clustering argument is unchanged.

## Cuts

**1. The Rejected table, rows 1, 3, 4 and 5 (~90 words).** *Partitioning on the producer's timestamp* restates the blockquoted incident verbatim; *Daily partitioning* restates the section and the table above it; *`event_type` as the first cluster key* restates a bolded sentence three paragraphs up; *No `require_partition_filter`* restates the options paragraph, minus its numbers. Compress each to a half-line, or keep only the two rows that carry an argument made nowhere else (`event_date` as a Bronze column, the Editions reservation). Lost: nothing but the second telling.

**2. The `storage_billing_model` paragraph (~95 words → ~40).** The reasoning is genuinely good, and it defends roughly $65/month on a 10.5 TB table — against the $5,100/month sitting three sections above it. The page never says so, which invites the reader to weight it as material. Compress to the mechanism and the number: physical bills time-travel and fail-safe bytes, an expiring table pays for ~16 days to hold 7, break-even moves from 2:1 to ~4.6:1, worth ~$65/month. Lost: the walkthrough; gained: the reader can rank it.

**3. The Editions reservation row in the Rejected table (~40 words).** It is a compressed copy of the Cost paragraph immediately above it, including the same ~450 TiB threshold. Keep the paragraph, drop the row.

## Interview questions this page invites

1. **"Your dominant query is Silver's 30-minute watermark read. Why isn't `publish_time` your first cluster key — or any cluster key?"** Not answered. The page establishes the premise and then silently switches criteria.
2. **"Automatic re-clustering on a streamed table is asynchronous, so the freshest rows sit in write-optimised storage un-clustered. Does the block pruning you price exist for the last 30 minutes — the only window Silver ever reads?"** Not answered. It does not move the $1,000/$6,100 figures (those come from partition pruning) but it does undercut the "costs cents" claim for operational queries on recent data.
3. **"Why is `payload` a `JSON` column rather than `STRING`? A `JSON` column is the only thing in this design that can refuse a message."** Partially answered elsewhere — 1.1 names invalid JSON as a dead-letter cause — but the *choice* is never defended on the page that declares it, and `JSON_VALUE` works over `STRING` at the same cost.

## Claims ledger

**DECISIONS**
- Partition key = Pub/Sub `publish_time` (arrival). Rejected: producer/event timestamp (skewed clock breaks retention *and* pruning); promoting an `event_date` column (no compute between topic and table, a `DATE` cast can fail).
- Partition grain = `HOUR`. Rejected: `DAY` (~$6,100/mo vs ~$1,000/mo).
- Cluster order = `publisher_id, ssp_id, event_type`. Rejected: `event_type` first (5 values sorts every block by the coarsest key).
- `require_partition_filter = TRUE`. Rejected: leaving it off (10.5 TB scan one typo away).
- `partition_expiration_days = 7` as a table property. Rejected implicitly: a scheduled deletion job that can be paused.
- `max_time_travel_hours = 48` (BigQuery minimum). Rejected: longer (paying to keep a rollback of data we must delete).
- `storage_billing_model = 'LOGICAL'` for the Bronze dataset. Rejected: PHYSICAL (expiring table loses the compression bet). Asserted: Silver's dataset is PHYSICAL.
- On-demand pricing. Rejected: BigQuery Editions reservation; reinstate above ~450 TiB/month sustained.
- `payload` and `attributes` typed `JSON`; no `data` column (topic schema in use); `subscription_name`, `message_id`, `publish_time` declared as subscription metadata, never read.
- Event-date analysis belongs in Silver on `auction_day` = `DATE(auction_timestamp)`, not in Bronze.

**TECH** — BigQuery (partitioning, clustering, block pruning, time travel, fail-safe, logical/physical storage billing, `ALTER SCHEMA`, on-demand pricing, Editions/Standard slots, `TIMESTAMP_TRUNC`); Pub/Sub (topic schema, BigQuery export subscription, `publish_time`); Cloud Storage (archive, referenced as the recovery path); Dataform (implicit, as "Silver's run").

**TERMS** — Bronze; Silver; arrival clock vs. producer clock; partition pruning vs. block pruning; prefix-ordered clustering; watermark read; `bronze_events`; `ingestion_timestamp` (Silver's name for `publish_time`); `auction_day`; time travel; fail-safe; logical vs. physical storage billing; "compliance ceiling, not a cost target".

**NUMBERS** — 7-day partition expiry; 24 partitions/day, 168 total, vs. a 10,000-partition limit; 48 Silver runs/day (30-min cadence); ~750 GB read per run at DAY grain; ~36 TB/day; ~$6,100/month; ~124 GB per run at HOUR grain; ~6 TB/day; ~$1,000/month; ~$5,100/month delta; ~62 GB per hourly partition; ~1.5 TB/day raw; 10.5 TB full-table scan; `payload` ≈ 90% of row width; ~300 `publisher_id` values; 5 `event_type` values; `no_bid` 75-80% of volume (conflicts with `intro/02`); 25 hourly partitions per event-day, 4% overhead vs. 100% at daily grain; 1-hour auction lifecycle; 1-hour retry bound; 48h time travel; 7-day fail-safe; ~16 days of bytes for a 7-day table; 2:1 physical break-even, ~3.4:1 observed compression, ~4.6:1 adjusted break-even; $6.25/TiB on-demand; ~450 TiB/month; 100 Standard slots.

**ASSUMES** — 2B events/day and ~1.5 TB/day (`intro/02`); Silver runs every 30 minutes and reads `WHERE publish_time > watermark` in a single pass over `payload` (2.1, 2.3); 1-hour auction lifecycle and 1-hour retry bound (`intro/02`, marked Assumed there); 7-day raw retention (`intro/02`); Silver is partitioned on `auction_day` and its dataset is PHYSICAL (2.1 for the partition, nowhere for the billing model); the GCS archive is the recovery path (1.1, 1.3); the topic schema promotes the five envelope fields so the subscription can write them as columns (1.1); ~300 publishers and ~3.4:1 compression — both first appear here, neither is sourced, and both are load-bearing for the clustering and storage-billing arguments respectively.
