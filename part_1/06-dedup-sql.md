# 2.3 — Deduplication, Bronze → Silver

*Test bullet: write the SQL query (using a window function) to deduplicate events arriving with the same `event_id` during the Bronze → Silver transition.*

The window function, as asked. Seven lines:

```sql
SELECT * EXCEPT (publish_time), publish_time AS ingestion_timestamp
FROM bronze_events
WHERE publish_time > @watermark AND publish_time <= @batch_max   -- the partition filter
QUALIFY ROW_NUMBER() OVER (
          PARTITION BY event_id
          ORDER BY publish_time DESC
        ) = 1
```

`QUALIFY` filters on a window function without the `SELECT ... FROM (…) WHERE rn = 1` wrapper. `ORDER BY publish_time DESC` keeps the **last** copy — both directions are defensible, but keeping the last matches the tie-break the `MERGE` below applies, so one rule holds everywhere. The filter names `publish_time`, not the alias: it is the partitioning column, and `require_partition_filter` is watching. Silver renames it to `ingestion_timestamp` once, here.

## Alone, it dedups only the batch

Duplicates arrive up to an hour late and Silver runs every 30 minutes, so a duplicate and its original usually land in *different runs*. The window function sees one batch: usually it finds nothing to remove, and inserts a row Silver already holds. Silver counts twice, Gold sums it, the dashboard is quietly wrong. Deduplicating against Silver's existing rows takes a `MERGE ON event_id`.

That does not make the window function optional, and the reason is sharper than *"the `MERGE` would fail"*. Two copies of an `event_id` Silver **already holds** do fail the run — `UPDATE/MERGE must match at most one source row for each target row`. Two copies of an `event_id` it has **never seen** match nothing, take `WHEN NOT MATCHED`, and insert twice with no error at all. That second case is the common one, a same-batch double-send of a new event, and it is the dangerous one. **The window function makes the `MERGE` legal, and the `MERGE` makes the dedup correct.** It guarantees one row per `event_id` *entering* the reference joins; non-overlapping `valid_from`/`valid_to` on the revenue-share table is what guarantees one row *leaving* them, which is why that table's validity windows are a correctness property and not a convenience.

## One model, not one per source

Payloads differ by source and converging them is a stated objective, so the typing step cannot be one JSON path per field: `price` lives at `$.bid.cpm` for one SSP and `$.price_usd` for another. The paths live in a declarative mapping in the Dataform repository, one entry per source, expanded at compile time into one `CASE` per column:

```sql
CASE source_id
  WHEN 'ssp_alpha' THEN SAFE_CAST(JSON_VALUE(payload, '$.bid.cpm')   AS NUMERIC)
  WHEN 'ssp_beta'  THEN SAFE_CAST(JSON_VALUE(payload, '$.price_usd') AS NUMERIC)
END AS price
```

`${col("price", "NUMERIC")}` in the script below is the template call that emits exactly that. Nothing evaluates it at runtime — BigQuery receives ordinary SQL, identical to the hand-written version — so **adding a source is a data change instead of a code change**, at no execution cost, and deleting the template call and pasting the generated blocks in gives the same compiled SQL, the same cost and the same results. A source with no path for a field, or no beacon for a whole event type, yields `NULL` there and never `0`: zero reads as inventory won and never served rather than as a gap.

## What actually runs

```sql
DECLARE watermark, batch_max TIMESTAMP;
DECLARE batch_days ARRAY<DATE>;

-- No row yet is a first run: seed at Bronze's own 7-day window, never NULL.
SET watermark = COALESCE(
  (SELECT last_success FROM pipeline_state WHERE model = 'silver_events'),
  TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY));

-- A ceiling read from the data and fixed for the run, so every statement below sees one
-- batch rather than successive snapshots of a table that grows while we work.
SET batch_max = (SELECT MAX(publish_time) FROM bronze_events WHERE publish_time > watermark);
IF batch_max IS NULL THEN RETURN; END IF;         -- an empty batch is a valid outcome

-- The only pass over `payload` in the run. Nothing after this line reads it again.
CREATE TEMP TABLE batch AS
WITH deduped AS (
  SELECT * EXCEPT (publish_time), publish_time AS ingestion_timestamp
  FROM bronze_events
  WHERE publish_time > watermark AND publish_time <= batch_max
  QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY publish_time DESC) = 1
), typed AS (
  SELECT event_id, event_type, source_id, publisher_id, ingestion_timestamp,
         ${col("auction_timestamp", "TIMESTAMP")} AS auction_timestamp,
         ${col("price", "NUMERIC")}               AS price, …
  FROM deduped                                    -- one ${col(…)} per typed column
)
SELECT                                            -- silver_events' columns, in its order
  event_id, event_type, source_id, publisher_id, ingestion_timestamp, auction_timestamp,
  DATE(auction_timestamp)                  AS auction_day,     -- Silver's partition key
  TIMESTAMP_TRUNC(auction_timestamp, HOUR) AS auction_hour,    -- Gold's grain
  CURRENT_TIMESTAMP() AS job_insert_timestamp,    -- kept on UPDATE, set on INSERT
  CURRENT_TIMESTAMP() AS job_update_timestamp,    -- rewritten on both
  … ,                                             -- the remaining typed columns
  gross_revenue, publisher_payout                 -- from the FX / revenue-share joins of 2.1
FROM typed;   -- plus the LEFT JOINs to ref_fx_rate and ref_revenue_share of 2.1

-- The auction days actually present. A script variable, not a subquery: BigQuery prunes on
-- a value fixed before the statement runs, never on a predicate it still has to evaluate.
SET batch_days = (SELECT ARRAY_AGG(DISTINCT auction_day IGNORE NULLS) FROM batch);

MERGE INTO silver_events AS t
USING (SELECT * FROM batch WHERE auction_timestamp IS NOT NULL) AS s  -- else silver_rejects
ON  t.event_id    = s.event_id
AND t.auction_day IN UNNEST(batch_days)           -- 1-2 partitions, never the whole table
WHEN MATCHED AND s.ingestion_timestamp > t.ingestion_timestamp THEN UPDATE SET
  ingestion_timestamp = s.ingestion_timestamp, auction_hour = s.auction_hour,
  … ,                                             -- every column but the two omitted:
  job_update_timestamp = s.job_update_timestamp   -- auction_day and job_insert_timestamp
WHEN NOT MATCHED THEN INSERT ROW;

-- Then, both keyed the same way and for the same reason: silver_rejects (the rows the
-- WHERE above excluded — keys and a reason, never a payload) and pipeline_state, below.
DROP TABLE batch;   -- a multi-statement query's temp table otherwise lingers 24 hours
```

## Four choices inside the run

- **One pass over `payload`, and everything else reads the temp table.** Day detection and the `MERGE` both need the typed batch; written the obvious way they each re-scan `payload`, the widest \~90% of the row. Bullet 2.2's figures already assume this single pass; written the obvious way they double, and the table is dropped before the script ends, so no event data outlives the run.
- **Every read is bounded above by `batch_max`, not only below by the watermark.** Bronze grows while the run executes, so an open-ended predicate means each statement reads a different table — and lets the watermark advance past rows the `MERGE` never saw.
- **`t.auction_day IN UNNEST(batch_days)` sits in the `ON` clause, and `batch_days` is read from the data.** That line *is* the partition pruning, and it works for two reasons a reviewer should be able to check: BigQuery prunes on a script variable because its value is fixed before the statement runs — the same predicate written as a subquery prunes nothing — and this `MERGE` has no `WHEN NOT MATCHED BY SOURCE` branch, which is the clause that forces a full scan of the target regardless. A backfill three days old targets its own partition automatically; a hardcoded "today and yesterday" would scan the wrong partitions *and* miss the duplicates it was meant to catch. Where pruning stops, results stay correct and only the bill changes — and Silver has no expiration, so the unpruned scan grows forever.
- **`auction_day` is absent from the `UPDATE SET`, and `SAFE_CAST` plus `WHERE auction_timestamp IS NOT NULL` is the rejects boundary.** A duplicate whose auction day moved is not a duplicate — it is the producer re-stamping on retry while reusing `event_id` — and updating the column would move the row to another partition and hide that bug. `auction_hour` *is* updated, because it derives from a value that should never have changed. A row with no usable auction clock is unplaceable rather than incomplete, so it diverts to `silver_rejects` as keys and a reason: never a payload, which Bronze still holds under the same partition key for the seven days the reject is worth investigating.

## A watermark, saved two minutes behind the ceiling

`WHERE publish_time > watermark` reads every Bronze row ingested since the last *successful* run. A fixed lookback, say 3 hours, has no catch-up mode: a backlog draining on Sunday arrives outside every following window and is skipped for good. The watermark's rule — *process everything not yet processed* — runs a two-day backlog with the same code as a two-minute one.

`publish_time` is stamped by the platform. But *stamped in order* and *appear in order* are different claims, and only the first is true:

> **A message stamped 10:29:58 becomes queryable at 10:30:04.** The subscription writes Bronze in parallel, so the order rows are *stamped* is not the order they *appear*. The 10:30 Silver run had already read; the highest stamp it saw was 10:29:59. Had that become the new line, the 10:29:58 row would have sat behind it forever — merged by nothing, counted by nothing, and no job would have failed.

So the line saved is not the ceiling that was read:

```sql
MERGE INTO pipeline_state AS t
USING (SELECT 'silver_events' AS model,
              TIMESTAMP_SUB(batch_max, INTERVAL 2 MINUTE) AS last_success) AS s
ON t.model = s.model
WHEN MATCHED THEN UPDATE SET last_success = s.last_success
WHEN NOT MATCHED THEN INSERT (model, last_success) VALUES (s.model, s.last_success);
```

The overlap costs scan and nothing else: \~7% of the Bronze read, discarded by the `MERGE`, which is why every write in the run is keyed rather than appended — failure lands in the direction of doing work twice, never of skipping it. An upsert rather than an `UPDATE` because the run that finds no line is the run that writes it, so a rebuilt environment needs no deployment step to seed. And the watermark lives in a table, one row per model, not in a `SELECT MAX(ingestion_timestamp) FROM ${self()}`: that `MAX` is over a non-partitioned column on a table with `require_partition_filter = TRUE`, so BigQuery refuses to run it — and a row also makes the watermark *settable*, so *"reprocess from Tuesday"* is an `UPDATE`, not a code change.

## Day-scoped dedup is a trade, not an oversight

`t.auction_day IN UNNEST(batch_days)` is what makes the `MERGE` cheap, and it is also what limits it. Silver holds `event_id = X` at day D4; the producer retries X and re-stamps the auction clock into D5; the `ON` clause looks in D5 only, finds nothing, and inserts a second row under one `event_id`. Bucketing on the auction's clock keeps that rare — `auction_timestamp` is an attribute the producer *carries*, not one it *generates*, which is also why midnight is not an edge case but an impossibility: the value is identical on all five events of an auction, so an auction cannot straddle a day boundary no matter when its impression fires. Closing the retry gap inside the `MERGE` costs the partition filter: every run would then match against the whole history of a table with no expiration, 48 times a day, to defend against a bug in someone else's code.

So it is closed by detection instead of prevention: the quality job counts the `event_id`s appearing with more than one `auction_timestamp`. Zero in steady state; non-zero means a producer is re-stamping, and the repair is a targeted rebuild of the two days involved. **Being wrong must be visible and rerunnable, not impossible.**

## Rejected — one line each

| Option | Why not |
|---|---|
| **Window function alone** | Limited to one batch. The duplicate usually arrives in a later run than the original, so it removes nothing |
| **`MERGE` alone, no window function** | Fails loudly on a duplicate of a row Silver already holds — `UPDATE/MERGE must match at most one source row for each target row` — and fails *silently* on a duplicate of one it does not, inserting both |
| **`SELECT DISTINCT` / `GROUP BY event_id`** | No tie-break rule, and no way to express "keep the later copy" |
| **`ORDER BY publish_time ASC` (keep first)** | Defensible, but the batch rule and the `MERGE` rule then disagree, and only on a row that arrived twice |
| **A wall-clock ceiling — `CURRENT_TIMESTAMP()` at the start of the run** | Simpler, and wrong: a message stamped before the ceiling can surface after it and land behind the line. A ceiling read from the data is a value we have seen; a clock reading is a prediction |
| **Dataform's native incremental model** | `SELECT MAX(ingestion_timestamp) FROM ${self()}` is refused outright by `require_partition_filter`, and the watermark becomes unsettable for a backfill |
| **Dedup at ingest, before Bronze** | Needs \~10 GB of live keyed state on the hot path to hold a 1h window at 23k/s, and lets duplicates through *silently* when that state is lost, where the `MERGE` fails loudly and can be rerun |
| **A fixed 3h read window** | No catch-up: a draining backlog is skipped for good, and only the numbers show it |
| **Partition filter in a subquery instead of the `ON` clause** | Same results, no pruning: the failure is invisible except on the bill |
| **Dropping the partition filter to make dedup day-independent** | Matches every 30-minute run against a table with no expiration, to prevent a producer bug the quality job already reports |
| **`CAST` instead of `SAFE_CAST`** | One malformed value fails the whole run instead of one row |
| **Each statement reading Bronze directly** | Doubles the largest scan in the pipeline to save one temp table — every figure in bullet 2.2, twice |
| **Push convergence to the producers** | The right answer when it is available, and it is not: the SSPs are third parties. We can demand an *envelope format* from our own collector; we cannot demand *field semantics* from them |
| **One SQLX model per source** | Copy-pastes the `MERGE`, the watermark and the assertions N times, so a dedup fix has to land in every copy |
| **Overlapping revenue-share validity windows** | Two matching reference rows duplicate an `event_id` after the window function has run — the same loud-or-silent split as above, from a source the dedup cannot see |

---

Part 1 complete. Next: [**Part 2 — LLM Agent**](/part2-llm-agent.md)
