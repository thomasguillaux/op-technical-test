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

`QUALIFY` filters on a window function without the `SELECT ... FROM (…) WHERE rn = 1` wrapper.

`ORDER BY publish_time DESC` keeps the last copy. Both orderings are defensible; last matches the tie-break the `MERGE` below applies, so one rule holds everywhere.

The filter names `publish_time`, not the alias. `publish_time` is the partitioning column and `require_partition_filter` is set. Silver renames it to `ingestion_timestamp` once, here.

## Alone, it dedups only the batch

Duplicates arrive up to an hour late and Silver runs every 30 minutes, so a duplicate and its original usually land in *different runs*. The window function sees one batch: usually it finds nothing to remove, and inserts a row Silver already holds. Silver counts twice, Gold sums it, the dashboard is quietly wrong. Deduplicating against Silver's existing rows takes a `MERGE ON event_id`.

That does not make the window function optional, and the reason is sharper than *"the `MERGE` would fail"*. Two copies of an `event_id` Silver already holds do fail the run — `UPDATE/MERGE must match at most one source row for each target row`. Two copies of an `event_id` it has never seen match nothing, take `WHEN NOT MATCHED`, and insert twice with no error. That second case is the common one, a same-batch double-send of a new event, and the dangerous one. **The window function makes the `MERGE` legal, and the `MERGE` makes the dedup correct.** It guarantees one row per `event_id` *entering* the reference joins. Non-overlapping `valid_from`/`valid_to` on the revenue-share table guarantees one row *leaving* them. That table's validity windows are a correctness property, not a convenience.

## One model, not one per source

The typing step cannot use one fixed JSON path per field: `price` lives at `$.bid.cpm` for one SSP and `$.price_usd` for another. Payloads differ by source. Converging them is a stated objective. The paths live in a declarative mapping in the Dataform repository, one entry per source, expanded at compile time into one `CASE` per column:

```sql
CASE source_id
  WHEN 'ssp_alpha' THEN SAFE_CAST(JSON_VALUE(payload, '$.bid.cpm')   AS NUMERIC)
  WHEN 'ssp_beta'  THEN SAFE_CAST(JSON_VALUE(payload, '$.price_usd') AS NUMERIC)
END AS price
```

`${col("price", "NUMERIC")}` in the script below is the template call that emits exactly that. Nothing evaluates it at runtime: BigQuery receives ordinary SQL, identical to the hand-written version. Adding a source is a data change instead of a code change, at no execution cost.

A source with no path for a field, or no beacon for a whole event type, yields `NULL` there and never `0`.

## What actually runs

```sql
DECLARE watermark, batch_max TIMESTAMP;
DECLARE batch_days ARRAY<DATE>;

-- No row yet is a first run: seed at Bronze's own 7-day window, never NULL.
SET watermark = COALESCE(
  (SELECT last_success FROM pipeline_state WHERE model = 'silver_events'),
  TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
);

SET batch_max = (
  SELECT MAX(publish_time)
  FROM bronze_events
  WHERE publish_time > watermark
);

IF batch_max IS NULL THEN
  RETURN;  -- an empty batch is a valid outcome
END IF;

CREATE TEMP TABLE batch AS
WITH deduped AS (
  SELECT
    * EXCEPT (publish_time),
    publish_time AS ingestion_timestamp
  FROM bronze_events
  WHERE publish_time > watermark
    AND publish_time <= batch_max
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY event_id
    ORDER BY publish_time DESC
  ) = 1
),

typed AS (
  SELECT
    event_id,
    event_type,
    source_id,
    publisher_id,
    ingestion_timestamp,
    ${col("auction_timestamp", "TIMESTAMP")} AS auction_timestamp,
    ${col("price", "NUMERIC")}               AS price,
    ${col("currency", "STRING")}             AS currency,
    …                                        -- one ${col(…)} per typed column
  FROM deduped
)

SELECT
  t.event_id,
  t.event_type,
  t.source_id,
  t.publisher_id,
  t.ingestion_timestamp,
  t.auction_timestamp,
  DATE(t.auction_timestamp)                  AS auction_day,          -- Silver's partition key
  TIMESTAMP_TRUNC(t.auction_timestamp, HOUR) AS auction_hour,         -- Gold's grain
  CURRENT_TIMESTAMP()                        AS job_insert_timestamp, -- kept on UPDATE, set on INSERT
  CURRENT_TIMESTAMP()                        AS job_update_timestamp, -- rewritten on both
  …,                                                                  -- the remaining typed columns
  IF(t.event_type = 'impression', t.price * fx.rate,                      NULL) AS gross_revenue,
  IF(t.event_type = 'impression', t.price * fx.rate * rs.publisher_share, NULL) AS publisher_payout
FROM typed AS t
LEFT JOIN ref_fx_rate AS fx
  ON  fx.currency = t.currency
  AND fx.day      = DATE(t.auction_timestamp)
LEFT JOIN ref_revenue_share AS rs
  ON  rs.publisher_id = t.publisher_id
  AND DATE(t.auction_timestamp) BETWEEN rs.valid_from AND rs.valid_to;

SET batch_days = (
  SELECT ARRAY_AGG(DISTINCT auction_day IGNORE NULLS)
  FROM batch
);

MERGE INTO silver_events AS t
USING (
  SELECT * FROM batch WHERE auction_timestamp IS NOT NULL
) AS s
ON  t.event_id    = s.event_id
AND t.auction_day IN UNNEST(batch_days)

WHEN MATCHED AND s.ingestion_timestamp > t.ingestion_timestamp THEN
  UPDATE SET
    ingestion_timestamp  = s.ingestion_timestamp,
    auction_hour         = s.auction_hour,
    …,
    job_update_timestamp = s.job_update_timestamp

WHEN NOT MATCHED THEN
  INSERT ROW;

-- silver_rejects and pipeline_state writes follow, keyed the same way, below.
DROP TABLE batch;  -- a multi-statement query's temp table otherwise lingers 24 hours
```

## Four choices inside the run

- **One pass over `payload`, and everything else reads the temp table.** Day detection and the `MERGE` both need the typed batch. Bullet 2.2's figures already assume that single pass. Written the obvious way, both re-scan `payload`, the widest \~90% of the row, and those figures double. The table is dropped before the script ends, so no event data outlives the run.
- **Every read is bounded above by `batch_max`, not only below by the watermark.** Bronze grows while the run executes, so an open-ended predicate means each statement reads a different table — and lets the watermark advance past rows the `MERGE` never saw.
- **`t.auction_day IN UNNEST(batch_days)` sits in the `ON` clause, and `batch_days` is read from the data.** That line *is* the partition pruning. It works for two reasons a reviewer can check. BigQuery prunes on a script variable, and on a query parameter, because the value is fixed before the statement runs; the same predicate written as a subquery prunes nothing. And this `MERGE` has no `WHEN NOT MATCHED BY SOURCE` branch, the clause that forces a full scan of the target regardless.

  A backfill three days old targets its own partition automatically. A hardcoded "today and yesterday" would scan the wrong partitions *and* miss the duplicates it exists to catch. Where pruning stops, results stay correct and only the bill changes. Silver has no expiration, so the unpruned scan grows forever.
- **`auction_day` is absent from the `UPDATE SET`, and `SAFE_CAST` plus `WHERE auction_timestamp IS NOT NULL` is the rejects boundary.** A duplicate whose auction day moved is not a duplicate. It is the producer re-stamping on retry while reusing `event_id`, and updating the column would move the row to another partition and hide that bug. `auction_hour` *is* updated, because it derives from a value that should never have changed.

  A row with no usable auction clock is unplaceable rather than incomplete. It diverts to `silver_rejects` as keys and a reason, never a payload. Bronze still holds the payload under the same partition key for the seven days the reject is worth investigating.

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

The overlap costs scan and nothing else: \~7% of the Bronze read, discarded by the `MERGE`. Every write in the run is keyed rather than appended, so failure lands in the direction of doing work twice, never of skipping it.

The watermark lives in a table, one row per model, not in a `SELECT MAX(ingestion_timestamp) FROM ${self()}`. That `MAX` is over a non-partitioned column on a table with `require_partition_filter = TRUE`, so BigQuery refuses to run it. A row also makes the watermark *settable*, so *"reprocess from Tuesday"* is an `UPDATE`, not a code change.

## Day-scoped dedup is a trade, not an oversight

`t.auction_day IN UNNEST(batch_days)` is what makes the `MERGE` cheap, and it is also what limits it. Silver holds `event_id = X` at day D4; the producer retries X and re-stamps the auction clock into D5; the `ON` clause looks in D5 only, finds nothing, and inserts a second row under one `event_id`. Bucketing on the auction's clock keeps that rare. `auction_timestamp` is an attribute the producer *carries*, not one it *generates*. Its value is identical on every event of an auction, so midnight raises no edge case: an auction cannot straddle a day boundary no matter when its impression fires.

Closing the retry gap inside the `MERGE` costs the partition filter. Every run would then match against the whole history of a table with no expiration, 48 times a day, to defend against a bug in someone else's code.

So it is closed by detection instead of prevention: the quality job counts the `event_id`s appearing with more than one `auction_timestamp`. Zero in steady state; non-zero means a producer is re-stamping, and the repair is a targeted rebuild of the two days involved. Being wrong has to be visible and rerunnable rather than impossible.

## Rejected — one line each

| Option | Why not |
|---|---|
| **`SELECT DISTINCT` / `GROUP BY event_id`** | No tie-break rule, and no way to express "keep the later copy" |
| **A wall-clock ceiling — `CURRENT_TIMESTAMP()` at the start of the run** | Simpler, and wrong: a message stamped before the ceiling can surface after it and land behind the line. A ceiling read from the data is a value we have seen; a clock reading is a prediction |
| **Dedup at ingest, before Bronze** | Needs \~10 GB of live keyed state on the hot path to hold a 1h window at 23k/s, and lets duplicates through *silently* when that state is lost, where the `MERGE` fails loudly and can be rerun |
| **`CAST` instead of `SAFE_CAST`** | One malformed value fails the whole run instead of one row |
| **Push convergence to the producers** | The right answer when it is available, and it is not: the SSPs are third parties. We can demand an *envelope format* from our own collector; we cannot demand *field semantics* from them |
| **One SQLX model per source** | Copy-pastes the `MERGE`, the watermark and the assertions N times, so a dedup fix has to land in every copy |

---

Part 1 complete. Next: [**Part 2 — LLM Agent**](/part2-llm-agent.md)
