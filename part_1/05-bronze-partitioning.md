# 2.2 — Bronze Partitioning & Clustering

*Test bullet: configure partitioning and clustering on the Bronze table to minimize execution cost while keeping queries on `publisher_id`, `ssp_id` and event date fast.*

**Partitioned by date, as the test asks — on `publish_time`, at hourly grain.** `publish_time` is the only clock no publisher can write to. Hourly rather than daily because Silver reads Bronze 48 times a day, and at daily grain every run rescans the whole day: \~$6,100/month against \~$1,000. Clustering is `publisher_id, ssp_id, event_type`, prefix-ordered, so the key filtered most often and most selectively sits first.

---

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

## Which grain: hourly, not daily

Silver reads Bronze every 30 minutes, so the grain is priced 48 times a day:

| Bronze grain | Silver's read, per run | × 48 runs/day | Scan cost |
|---|---|---|---|
| **DAY** | \~750 GB (day average) | \~36 TB/day | **\~$6,100/month** |
| **HOUR** | \~124 GB | \~6 TB/day | **\~$1,000/month** |

## Event date, answered twice

**On Bronze, arrival time *is* event date, within two measured hours.** An auction reaches its final state within an hour, and a retry lands at most an hour after the original. Every event dated D therefore arrives between D 00:00 and D+1 02:00 — 26 hourly partitions for a 24-hour day, 8% more than the day itself. At daily grain the same query needs two partitions, 100% more. Lateness is measured hourly and per publisher, so if it worsens the arrival range widens by exactly the measured amount and nothing else moves.

## Clustering order is not free

BigQuery clustering is *prefix-ordered*: rows sort by the first key, then by the second inside it. Position 1 goes to the column filtered most often and most selectively.

| Position | Key | Why here |
|---|---|---|
| 1 | `publisher_id` | \~300 values, and every operational or reprocessing query names one |
| 2 | `ssp_id` | The test's own second key; the natural filter for a demand-side investigation |
| 3 | `event_type` | 5 values — the biggest bulk filter (`bid` + `no_bid` are 75-80%) but the coarsest |

**Cost.** Every figure above is bytes scanned at on-demand \$6.25/TiB. A reservation prices slot-time instead. It is the lever to revisit above \~450 TiB/month sustained, where 100 Standard slots running continuously buy the same bytes. Below that, on-demand costs nothing when idle and gives the Part 2 agent its own slot pool for the price of its own project.

## Rejected — one line each

| Option | Why not |
|---|---|
| **No `require_partition_filter`** | Leaves a 10.5 TB unfiltered scan one typo away on Bronze — and an unbounded one on Silver |
| **A BigQuery Editions reservation** | Probably cheaper on the pipeline side, and isolating the Part 2 agent then costs a second reservation to size and maintain, where on-demand isolates it with a project. Revisit above \~450 TiB/month |

---

Next: [**2.3 — Deduplication, Bronze → Silver**](/part_1/06-dedup-sql.md)
