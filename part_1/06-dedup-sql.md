# 2.3 — Deduplication, Bronze → Silver

*Test bullet: write the SQL query (using a window function) to deduplicate events arriving with the same `event_id` during the Bronze → Silver transition.*

**A window function picks the surviving row; the `MERGE` around it makes that choice correct across runs.** `ROW_NUMBER` over `event_id` answers the bullet as written, but a query alone re-inserts duplicates the moment the same Bronze rows are read twice — and re-reading is the normal case here, not the exception, because late data and reruns both replay the same window. The `MERGE` and the watermark it advances are what make that safe.

---

```sql
SELECT * EXCEPT (publish_time), publish_time AS ingestion_timestamp
FROM bronze_events
WHERE publish_time > @watermark AND publish_time <= @batch_max   -- the partition filter
QUALIFY ROW_NUMBER() OVER (
          PARTITION BY event_id
          ORDER BY publish_time DESC
        ) = 1
```

That does not make the window function optional, and the reason is not simply that the `MERGE` would fail. Two copies of an `event_id` Silver already holds do fail the run — `UPDATE/MERGE must match at most one source row for each target row`. Two copies of an `event_id` it has never seen match nothing, take `WHEN NOT MATCHED`, and insert twice with no error. That second case is the common one, a same-batch double-send of a new event, and the dangerous one. **The window function makes the `MERGE` legal, and the `MERGE` makes the dedup correct across runs — within the auction day.** It guarantees one row per `event_id` *entering* the reference joins. Non-overlapping `valid_from`/`valid_to` on the revenue-share table guarantees one row *leaving* them. That table's validity windows are a correctness property, not a convenience.

```sql
CASE source_id
  WHEN 'ssp_alpha' THEN SAFE_CAST(JSON_VALUE(payload, '$.bid.cpm')   AS NUMERIC)
  WHEN 'ssp_beta'  THEN SAFE_CAST(JSON_VALUE(payload, '$.price_usd') AS NUMERIC)
END AS price
```

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

> **A message stamped 10:29:58 becomes queryable at 10:30:04.** The subscription writes Bronze in parallel, so the order rows are *stamped* is not the order they *appear*. The 10:30 Silver run had already read; the highest stamp it saw was 10:29:59. Had that become the new line, the 10:29:58 row would have sat behind it forever — merged by nothing, counted by nothing, and no job would have failed.

```sql
MERGE INTO pipeline_state AS t
USING (SELECT 'silver_events' AS model,
              TIMESTAMP_SUB(batch_max, INTERVAL 2 MINUTE) AS last_success) AS s
ON t.model = s.model
WHEN MATCHED THEN UPDATE SET last_success = s.last_success
WHEN NOT MATCHED THEN INSERT (model, last_success) VALUES (s.model, s.last_success);
```

## Rejected — one line each

| Option | Why not |
|---|---|
| **`SELECT DISTINCT` / `GROUP BY event_id`** | No tie-break rule, and no way to express "keep the later copy" |
| **A wall-clock ceiling — `CURRENT_TIMESTAMP()` at the start of the run** | Simpler, and wrong: a message stamped before the ceiling can surface after it and land behind the line. A ceiling read from the data is a value we have seen; a clock reading is a prediction |
| **Dedup at ingest, before Bronze** | Needs \~10 GB of live keyed state on the hot path to hold a 1h window at 23k/s, and lets duplicates through *silently* when that state is lost, where the `MERGE` fails loudly and can be rerun |
| **Bound the target on `ingestion_timestamp`, or a rolling last-N-days window** | Not the partition column, so it prunes nothing and `require_partition_filter` rejects it — and anchored to now, it misses every backfill's duplicates |
| **`CAST` instead of `SAFE_CAST`** | One malformed value fails the whole run instead of one row |
| **Push convergence to the producers** | The right answer when it is available, and it is not: the SSPs are third parties. We can demand an *envelope format* from our own collector; we cannot demand *field semantics* from them |
| **One SQLX model per source** | Copy-pastes the `MERGE`, the watermark and the assertions N times, so a dedup fix has to land in every copy |

---

Next: [**1.1 — Copilot Scope & Question Classes**](/part_2/01-question-classes.md)
