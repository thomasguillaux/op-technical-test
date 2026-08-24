# 2.3 — Dedup that survives reruns

*Test bullet: write the SQL query (using a window function) to deduplicate events arriving with the same `event_id` during the Bronze → Silver transition.*

The window function, as asked. Six lines:

```sql
SELECT * EXCEPT (publish_time), publish_time AS ingestion_timestamp
FROM bronze_events
WHERE publish_time > @watermark            -- the partition filter, on the partitioning column
QUALIFY ROW_NUMBER() OVER (
          PARTITION BY event_id
          ORDER BY publish_time DESC
        ) = 1
```

`QUALIFY` filters on a window function without the `SELECT ... FROM (…) WHERE rn = 1` wrapper. Same result, one level of nesting less.

`ORDER BY publish_time DESC` keeps the **last** copy. Both choices are defensible. Keeping the last one makes this tie-break identical to the one the `MERGE` below applies against rows already in Silver, so the rule is written once and holds everywhere.

**`publish_time` is the column name Pub/Sub imposes on Bronze. Silver renames it to `ingestion_timestamp` once, here.** The filter must name `publish_time`, not the alias: it is the partitioning column, and `require_partition_filter` is watching.

## Alone, it dedups only the batch

**Duplicates arrive up to an hour late, and Silver runs every 30 minutes. A duplicate and its original usually land in *different runs*.** That hour is *measured*, not assumed: the daily quality job counts the events that exceed it, per publisher. The window function sees one batch only. So in the common case it sees one copy, finds nothing to remove, and inserts a row Silver already holds. Silver counts twice, Gold sums it, and the number on the dashboard is quietly wrong.

Removing duplicates **against what is already in Silver** takes a `MERGE ON event_id`.

That does not make the window function optional. **BigQuery rejects a `MERGE` whose source contains duplicate keys:** `UPDATE/MERGE must match at most one source row for each target row`. The two are not alternatives:

- the window function makes the `MERGE` **legal**,
- the `MERGE` makes the dedup **correct**.

## What actually runs

```sql
DECLARE watermark TIMESTAMP DEFAULT (
  SELECT last_success FROM silver_state WHERE model = 'silver_events'
);

-- The event days present in this batch. Read from the data, not assumed.
DECLARE batch_days ARRAY<DATE> DEFAULT (
  SELECT ARRAY_AGG(DISTINCT DATE(SAFE_CAST(JSON_VALUE(payload, '$.event_timestamp') AS TIMESTAMP))
                   IGNORE NULLS)
  FROM bronze_events
  WHERE publish_time > watermark
);

MERGE INTO silver_events AS t
USING (
  WITH deduped AS (
    SELECT * EXCEPT (publish_time), publish_time AS ingestion_timestamp
    FROM bronze_events
    WHERE publish_time > watermark
    QUALIFY ROW_NUMBER() OVER (
              PARTITION BY event_id
              ORDER BY publish_time DESC
            ) = 1
  ),
  typed AS (
    SELECT
      event_id, event_type, ingestion_timestamp, publisher_id, ssp_id,
      SAFE_CAST(JSON_VALUE(payload, '$.event_timestamp') AS TIMESTAMP) AS event_timestamp,
      JSON_VALUE(payload, '$.auction_id')  AS auction_id,
      JSON_VALUE(payload, '$.ad_unit_id')  AS ad_unit_id,
      JSON_VALUE(payload, '$.format')      AS format,
      JSON_VALUE(payload, '$.device')      AS device,
      JSON_VALUE(payload, '$.channel')     AS channel,
      SAFE_CAST(JSON_VALUE(payload, '$.price') AS NUMERIC) AS price,
      JSON_VALUE(payload, '$.currency')    AS currency
    FROM deduped
  )
  SELECT
    y.event_id, y.event_type, y.event_timestamp,
    DATE(y.event_timestamp) AS event_day,
    y.ingestion_timestamp, y.publisher_id, y.ad_unit_id, y.auction_id, y.ssp_id,
    y.format, y.device, y.channel, y.price, y.currency,
    IF(y.event_type = 'impression', y.price * fx.rate,                      NULL) AS gross_revenue,
    IF(y.event_type = 'impression', y.price * fx.rate * rs.publisher_share, NULL) AS publisher_payout
  FROM typed y
  LEFT JOIN ref_fx_rate fx                     -- finance-owned, declared external table
    ON  fx.currency = y.currency
    AND fx.day      = DATE(y.event_timestamp)
  LEFT JOIN ref_revenue_share rs               -- contract export, declared external table
    ON  rs.publisher_id = y.publisher_id
    AND DATE(y.event_timestamp) BETWEEN rs.valid_from AND rs.valid_to
  WHERE y.event_timestamp IS NOT NULL          -- typing failures divert to the rejects table
) AS s
ON  t.event_id  = s.event_id
AND t.event_day IN UNNEST(batch_days)          -- 1-2 partitions, never 13 months
WHEN MATCHED AND s.ingestion_timestamp > t.ingestion_timestamp THEN UPDATE SET
  event_type = s.event_type, event_timestamp = s.event_timestamp,
  ingestion_timestamp = s.ingestion_timestamp,
  publisher_id = s.publisher_id, ad_unit_id = s.ad_unit_id, auction_id = s.auction_id,
  ssp_id = s.ssp_id, format = s.format, device = s.device, channel = s.channel,
  price = s.price, currency = s.currency,
  gross_revenue = s.gross_revenue, publisher_payout = s.publisher_payout
WHEN NOT MATCHED THEN INSERT ROW;
```

## Four choices worth pointing at

**`t.event_day IN UNNEST(batch_days)` sits in the `ON` clause, not in a subquery.** That line *is* the partition pruning. Put it anywhere BigQuery cannot evaluate before the scan and pruning stops silently: the results stay correct, only the bill changes. Without it, every run matches against 13 months of Silver.

**`batch_days` is read from the data, not assumed to be "today and yesterday".** A backfill three days old targets its own partition automatically. A hardcoded window would scan the wrong partitions *and* miss the duplicates it was meant to catch.

**`event_day` is absent from the `UPDATE SET` on purpose.** A duplicate whose event day moved is not a duplicate: the producer re-stamped the timestamps on retry while reusing `event_id`. Updating the column would move the row to another partition and hide a producer bug. So it stays out, and the anomaly stays visible to the quality job. The next section gives the price of that choice.

**`SAFE_CAST` plus `WHERE y.event_timestamp IS NOT NULL` is the rejects boundary.** A second `INSERT` writes the excluded rows, with their raw payload, to `silver_rejects`. One publisher sending malformed timestamps must not stop Silver for everyone, and `SAFE_CAST` is what makes a bad value fail the row instead of the statement.

## Day-scoped dedup is a trade, not an oversight

`t.event_day IN UNNEST(batch_days)` is what makes the `MERGE` cheap. It is also what limits it. Here is the one case where that limit shows:

1. Silver holds `event_id = X` at `event_day = D4`
2. The producer retries X and re-stamps `event_timestamp` into D5. `batch_days = [D5]`
3. The `ON` clause looks for X **in D5 only**, finds nothing, and `WHEN NOT MATCHED` inserts it

Two rows, one `event_id`. The `UPDATE SET` exclusion above never applies, because the row was never matched.

**Closing this inside the `MERGE` means dropping the partition filter and matching against 13 months of Silver on every 30-minute run.** That is the exact cost bullet 2.2 works to avoid, paid 48 times a day, to protect against a producer bug that should not exist.

So it is closed by **detection instead of prevention**: the daily quality job counts the `event_id`s that appear with more than one `event_timestamp`. Zero in steady state. Non-zero means a producer is re-stamping, which is the only way to reach this limit. It appears as a number on `quality_day` the next morning, and the repair is a targeted rebuild of the two days involved. **The rule the whole design runs on: being wrong must be visible and rerunnable, not impossible.** A limit we have priced and instrumented is not the same as one we did not notice.

## A watermark, not a fixed window

`WHERE publish_time > watermark` reads every Bronze row ingested since the last **successful** run.

A fixed lookback, say 3 hours, has no catch-up mode. A backlog that drains on Sunday arrives outside every following window and is skipped for good, and Gold then rebuilds Friday from a Silver that already lost those rows.

This is safe **because `publish_time` is our clock.** Pub/Sub stamps it, so the watermark only moves forward and nothing can arrive behind it. A watermark on the producer's `event_timestamp` would let one skewed client write rows below the mark, invisible forever.

It also states the rule more simply: *process everything not yet processed*. A two-day backlog runs the same code as a two-minute one, which is the single-code-path property the whole cold path rests on.

**One consequence, because it affects a metric:** `ingestion_timestamp` in Silver means *when the copy we kept arrived*, not when the event first reached us. So lateness figures measure the last arrival: they over-report, never under-report. Bronze holds every copy for 90 days if we ever want a true first-arrival measurement.

## Midnight is a non-issue

The obvious question: an event at 23:59:59 whose duplicate arrives after midnight. Do they land in different partitions and miss each other?

No. `event_day` comes from `event_timestamp`, which travels with the event, so both copies carry the same day whatever their arrival time. A batch that spans midnight simply produces two entries in `batch_days` and targets both partitions.

## Rejected — one line each

| Option | Why not |
|---|---|
| **Window function alone** | Limited to one batch. The duplicate usually arrives in a later run than the original, so in the common case it removes nothing |
| **`MERGE` alone, no window function** | Illegal: BigQuery refuses a source with duplicate keys, `UPDATE/MERGE must match at most one source row for each target row` |
| **`SELECT DISTINCT` / `GROUP BY event_id`** | No tie-break rule, and no way to express "keep the later copy" |
| **`ORDER BY publish_time ASC` (keep first)** | Defensible, but then the batch rule and the `MERGE` rule disagree, and that disagreement only shows on a row that arrived twice |
| **Dedup at ingest, before Bronze** | Needs \~10 GB of live keyed state on the hot path to hold a 1h window at 23k/s, and lets duplicates through *silently* when that state is lost, where the `MERGE` fails loudly and can be rerun |
| **A fixed 3h read window** | No catch-up: a draining backlog is skipped for good, and only the numbers show it |
| **Partition filter in a subquery instead of the `ON` clause** | Same results, no pruning: the failure is invisible except on the bill |
| **Dropping the partition filter to make dedup day-independent** | 13 months of Silver matched on every 30-minute run, to prevent a producer bug that `quality_day` already reports the next morning |
| **`CAST` instead of `SAFE_CAST`** | One malformed value fails the whole run instead of one row |

---

Part 1 complete. Next: [**Part 2 — LLM Agent**](/part2-llm-agent.md)
