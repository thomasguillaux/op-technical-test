# 2.2 — Bronze Partitioning & Clustering

*Test bullet: configure partitioning and clustering on the Bronze table to minimize execution cost while keeping queries on `publisher_id`, `ssp_id` and event date fast.*

```sql
CREATE TABLE bronze.bronze_events (
  subscription_name STRING,     -- the three metadata columns the BigQuery subscription
  message_id        STRING,     -- requires alongside publish_time; declared, never read
  attributes        JSON,
  publish_time      TIMESTAMP,  -- Silver reads it as `ingestion_timestamp`
  event_id          STRING,
  source_id         STRING,
  event_type        STRING,
  publisher_id      STRING,
  ssp_id            STRING,
  payload           JSON               -- the topic schema is used, so no `data` column
)
PARTITION BY TIMESTAMP_TRUNC(publish_time, HOUR)
CLUSTER BY publisher_id, ssp_id, event_type
OPTIONS (
  partition_expiration_days = 7,     -- compliance ceiling, not a cost target
  require_partition_filter  = TRUE
);

-- Dataset-level options: neither is a table property.
ALTER SCHEMA bronze SET OPTIONS (
  max_time_travel_hours = 48,        -- BigQuery's minimum
  storage_billing_model = 'LOGICAL'  -- physical bills the expiry residue
);
```

Partitioned on date, as the test asks, at a grain finer than a day. Two choices need defending: **which clock, and which grain.**

## Which clock: arrival, not event time

`publish_time` is the only clock no publisher can write to: Pub/Sub stamps it, and Pub/Sub belongs neither to us nor to the producer. The producer's own timestamps are not Bronze columns at all; they sit unparsed inside `payload`. A `TIMESTAMP` cast can fail, and there is no compute between the topic and the table to derive one.

> **A client has a skewed clock reporting the year 2029.** Partitioning on arrival, the row lands in the current partition and nothing else notices. On the producer's clock it opens a partition years in the future and breaks two things silently: retention, because that partition never expires on schedule, and pruning, because every scan now covers a range with a hole in it.

## Which grain: hourly, not daily

Daily is the reflex reading of *"partitioned by date"*. The column does not change; only the grain does. The dominant query decides it.

**The dominant Bronze query is not a human's — it is Silver's watermark read, 48 times a day.** `WHERE publish_time > watermark` wants the last 30 minutes of arrivals. At daily grain it prunes to one partition, then scans everything accumulated inside it — including `payload`, \~90% of the row width. At 23:30 the run reads most of \~1.5 TB to find thirty minutes of rows.

Block pruning cannot rescue daily grain. BigQuery prunes blocks on **clustering** columns only, and `CLUSTER BY publisher_id, ssp_id, event_type` scatters `publish_time` across them. The clustering is the test's own requirement, so it cannot be traded for the arrival order block pruning needs. Partition grain is the only lever left.

| Bronze grain | Silver's read, per run | × 48 runs/day | Scan cost |
|---|---|---|---|
| **DAY** | \~750 GB (day average) | \~36 TB/day | **\~$6,100/month** |
| **HOUR** | \~124 GB | \~6 TB/day | **\~$1,000/month** |

\~$5,100/month on one clause of DDL. The partition ceiling is not a constraint: 7 days × 24 = 168 partitions against a limit of 10,000.

## Event date, answered twice

Two of the three columns the test wants fast are cluster keys. The partition answers the third.

**On Bronze, arrival time *is* event date, within two measured hours.** An auction reaches its final state within an hour, and a retry lands at most an hour after the original. Every event dated D therefore arrives between D 00:00 and D+1 02:00 — 26 hourly partitions for a 24-hour day, 8% more than the day itself. At daily grain the same query needs two partitions, 100% more. Lateness is measured hourly and per publisher, so if it worsens the arrival range widens by exactly the measured amount and nothing else moves.

Beyond that, event-date analysis belongs in Silver, partitioned on `auction_day` = `DATE(auction_timestamp)`. Two date columns, one per job: Bronze needs a clock no publisher can skew, Silver a business meaning stable across every event of one auction.

## Clustering order is not free

BigQuery clustering is *prefix-ordered*: rows sort by the first key, then by the second inside it. Position 1 goes to the column filtered most often and most selectively.

| Position | Key | Why here |
|---|---|---|
| 1 | `publisher_id` | \~300 values, and every operational or reprocessing query names one |
| 2 | `ssp_id` | The test's own second key; the natural filter for a demand-side investigation |
| 3 | `event_type` | 5 values — the biggest bulk filter (`bid` + `no_bid` are 75-80%) but the coarsest |

**`event_type` is last, even though it removes the most rows.** Putting a 5-value column first would sort every block by the coarsest key there is, weakening the two filters the test named. Behind the prefix it still contributes block pruning to any query that also filters `publisher_id`.

## The options in the DDL

`require_partition_filter = TRUE` makes an unqualified query *fail* instead of scanning seven days. A query naming an arrival range and a publisher prunes to a few \~62 GB partitions, then to the blocks holding that publisher, and costs cents. The same query without a partition filter scans 10.5 TB.

`partition_expiration_days = 7` makes retention a table property, not a job that can be scheduled wrong or quietly paused.

`max_time_travel_hours = 48` is BigQuery's minimum. Bronze is immutable and the GCS archive is the recovery path, so a longer window only pays to keep a rollback of data we are obliged to delete.

`storage_billing_model = 'LOGICAL'`, not physical. Physical bills compressed bytes and wins past 2:1, which this data clears at \~3.4:1. It *also* bills time-travel and fail-safe bytes, \~16 days for a 7-day table, which moves the break-even to \~4.6:1. **Physical storage is a bet on compression that an expiring table loses.**

**Cost.** Every figure above is bytes scanned at on-demand \$6.25/TiB. A reservation prices slot-time instead. It is the lever to revisit above \~450 TiB/month sustained, where 100 Standard slots running continuously buy the same bytes. Below that, on-demand costs nothing when idle and gives the Part 2 agent its own slot pool for the price of its own project.

## Rejected — one line each

| Option | Why not |
|---|---|
| **No `require_partition_filter`** | Leaves a 10.5 TB unfiltered scan one typo away on Bronze — and an unbounded one on Silver |
| **A BigQuery Editions reservation** | Probably cheaper on the pipeline side, and isolating the Part 2 agent then costs a second reservation to size and maintain, where on-demand isolates it with a project. Revisit above \~450 TiB/month |

---

Next: [**2.3 — Deduplication, Bronze → Silver**](/part_1/06-dedup-sql.md)
