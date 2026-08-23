# 2.2 — How do you configure partitioning and clustering on the Bronze table to minimize execution costs while ensuring fast queries on `publisher_id`, `ssp_id`, and event date?

```sql
CREATE TABLE bronze.bronze_events (
  publish_time  TIMESTAMP,   -- written by the subscription; this design's `ingestion_timestamp`
  event_id      STRING,
  event_type    STRING,
  publisher_id  STRING,
  ssp_id        STRING,
  payload       JSON
)
PARTITION BY TIMESTAMP_TRUNC(publish_time, HOUR)
CLUSTER BY publisher_id, ssp_id, event_type
OPTIONS (
  partition_expiration_days = 90,
  require_partition_filter  = TRUE,
  max_time_travel_hours     = 48
);

ALTER SCHEMA bronze SET OPTIONS (storage_billing_model = 'PHYSICAL');
```

`publish_time` is the metadata column a Pub/Sub BigQuery subscription writes when metadata is enabled. The name is fixed by the platform; everything downstream reads it as `ingestion_timestamp`.

## Partitioned by time of arrival — which clock, then which grain

Time-partitioned on arrival, as the test asks: date-based pruning, at a grain finer than a day. **Two choices need defending — which clock, and which grain.**

### Which clock: arrival, not event time

**`publish_time` is the only clock no publisher can write to.** A third party to both us and the producer — Pub/Sub — stamps it, so nothing a client sends can influence which partition a row lands in.

> **A client has a skewed clock reporting the year 2029.** Because Bronze partitions on arrival, the row lands in the current partition and nothing else notices. Partitioning on producer-supplied `event_timestamp` would have opened a partition years out — silently breaking retention (that partition never expires on schedule) and pruning (every scan now spans a range with a hole in it).

There is a second, harder reason: **`event_timestamp` is not a Bronze column at all.** It sits inside `payload`, unparsed, because a `TIMESTAMP` cast can fail and Bronze is the layer that refuses to validate. Partitioning on it would require deriving it — and there is no compute between the topic and the table to derive anything.

### Which grain: hourly, not daily

**The dominant Bronze query is not a human's — it is Silver's watermark read, 48 times a day.** `WHERE publish_time > watermark` wants the last 30 minutes of arrivals. At daily grain it prunes to one partition and then scans the whole accumulated day, reading `payload` for every `JSON_VALUE` — and `payload` is ~90% of the row width. Day-averaged that is ~750 GB per run, ~36 TB/day, **~$6,100/month** — and the `batch_days` DECLARE in bullet 2.3 issues the same scan a second time.

**Block min/max metadata does not rescue it, and the reason is our own DDL.** BigQuery's automatic reclustering sorts blocks by the cluster keys, so `CLUSTER BY publisher_id, ssp_id, event_type` actively scatters `publish_time` across blocks. The natural arrival ordering that would have made block pruning work is destroyed by the clustering the test asked for.

An hourly partition is ~62 GB logical, ~18.5 GB on disk. A 30-minute run touches one or two — ~124 GB, ~6 TB/day, **~$1,000/month.** Same SQL, one DDL line.

**The ceiling is not close.** 90 days × 24 = **2,160 partitions** against BigQuery's 10,000-partition limit: 4.6× headroom, binding only past ~416 days of retention, which Bronze will never reach because it is a reprocessing window and GCS holds the indefinite copy. A separate limit caps a single job at **4,000 partitions modified**; a one-statement 90-day replay touches 2,160, and the replay runbook chunks by day (24 partitions) anyway.

**The honest cost is ergonomic:** a human must filter on a timestamp range rather than `DATE(publish_time) = …` for pruning to fire reliably. For a layer whose queries are arrival-ranges by nature — the next section — that is arguably the more honest shape.

## Event date, the third column — answered on Bronze, then again in Silver

Two of the test's three fast-query columns are cluster keys. The third is answered by the partition itself.

**On Bronze, arrival time *is* event date, to within a measured hour.** An auction reaches its final state inside an hour and a retry lands at most an hour after the original, so every event whose event date is D arrives between D 00:00 and D+1 01:00: **25 hourly partitions to cover a 24-hour day, a 4% skirt.** Prune to those 25, then filter `event_timestamp` within them.

**Hourly grain is what keeps the skirt tight.** At daily grain the same query needs two partitions to cover one day — a 100% overshoot against 4%.

That one-hour bound is an assumption, and it is the one assumption in the design that measures itself: the daily quality job records lateness p99 per publisher. *"What if lateness is worse than you assumed?"* — **the arrival range widens by exactly the measured amount, and nothing else in the design moves.**

**Beyond that, analytical event-date work belongs in Silver** — which is the Medallion pattern the same bullet asks for. Silver partitions on `event_day` = `DATE(event_timestamp)`: typed, deduplicated, and reachable by exactly the filter an analyst would write. **The pipeline has two date columns on purpose, one per job** — Bronze needs a clock no publisher can skew, Silver needs business meaning that is stable across retries. Collapsing them into one is the mistake, not the divergence.

And Bronze's own queries are arrival-shaped by nature: *"replay everything that arrived between these two times"*, *"what did publisher X send this morning"*. It is a landing and reprocessing layer, not an analytics one.

## Clustering order, because prefix order is not free

BigQuery clustering is **prefix-ordered**: rows are sorted by the first key, then the second within it, and so on. So position 1 goes to the column filtered most often and most selectively.

| Position | Key | Why here |
|---|---|---|
| 1 | `publisher_id` | ~300 values, and every operational and reprocessing query names one |
| 2 | `ssp_id` | The test's own second key; the natural filter for a demand-side investigation |
| 3 | `event_type` | 5 values — the biggest bulk filter (`no_bid` is 75-80% of volume) but the coarsest |

**`event_type` is last despite pruning the most rows.** A non-prefix clustered column still prunes through block min/max metadata — partial, not zero. Putting a 5-value column first would sort every block by the coarsest key available and weaken the two filters the test actually named.

## What this costs to query

A query naming an arrival range and a publisher prunes to a handful of ~62 GB partitions, then to the blocks holding that publisher — roughly single-digit gigabytes, i.e. cents on on-demand pricing. The same query without partitioning would scan **135 TB**: on-demand bills logical bytes, so the 40 TB compressed on disk is not what an unpruned scan costs.

**That gap is the entire cost story, which is why `require_partition_filter = TRUE` is in the DDL:** an unqualified `SELECT` against Bronze *fails* rather than scanning 90 days. One line, and it is the cheapest guardrail in the design — the same class of protection as the copilot's byte ceiling in Part 2, applied to humans.

Two more options in that DDL are cost decisions rather than defaults:

- **`max_time_travel_hours = 48`** — the minimum. Bronze is immutable and the GCS archive is the recovery path, so a 7-day rollback window is capability we would pay to store and never use. This matters *because* of the next line.
- **Physical storage billing.** Billed on compressed bytes at 2× the rate, so it wins whenever compression beats 2:1 — and this data lands at ~3.4:1 (135 TB logical, ~40 TB on disk), turning ~$2,700/month of Bronze storage into ~$1,600. It also bills time-travel and fail-safe bytes, which logical billing does not, hence the 48-hour floor above.

And **`partition_expiration_days = 90` makes retention a table property, not a job.** No orchestrated deletion, nothing to schedule, nothing to fail, and no chance of a purge job with a wrong predicate deleting the wrong partitions. The safest deletion job is the one that does not exist.

## On-demand or a reservation — the billing model is a decision, not a default

Every figure above prices **bytes scanned**, which assumes on-demand billing at $6.25/TiB. That assumption is the largest single cost lever in Part 1, so it gets stated rather than defaulted into.

The pipeline's entire workload is 48 Silver runs, 6 Gold rebuilds and one quality job a day, plus ~10 analysts — call it **~300 TB scanned/month, ~$1,900 on-demand.**

A BigQuery Editions reservation prices **slot-time** instead, which inverts the arithmetic: a well-pruned 124 GB scan costs $0.76 on-demand and a fraction of that in slot-seconds. **An autoscaling Standard reservation would plausibly land below on-demand on the pipeline half, and claiming otherwise would be the same trap as claiming Dataflow costs more.** On-demand wins on two grounds that are not price:

1. **It isolates the Part 2 agent from the pipeline.** Under on-demand, a hallucinated heavy query hits `maximum_bytes_billed` and fails alone. Under a shared reservation it consumes slots and **starves Silver's 30-minute cadence** — the copilot's blast radius stops being a bill and becomes a freshness incident.
2. **Zero tuning surface.** A reservation is a baseline, a max, an edition and an assignment per workload, each drifting as volume grows. The pruning above is what makes on-demand cheap, and that work is already done.

**The threshold to revisit, named rather than left to feel:** sustained scan past **~450 TB/month**, where 100 baseline Standard slots (~$2,900/month) buy the same bytes — or a second heavy consumer that needs isolation of its own. Neither is close.

The one reservation argument that is about risk rather than price — on-demand is uncapped, and one unqualified query is billable — is already answered a line higher up: `require_partition_filter` makes the 135 TB scan **fail instead of bill.**

## Rejected — one line each

| Option | Why not |
|---|---|
| **Partitioning on `event_timestamp`** | Hands the partition key to the producer: one skewed clock opens a partition years out and breaks both retention and pruning |
| **Promoting `event_date` as a Bronze column** | Fails on the path, not on taste — the subscription writes what was published, there is no compute in between, and a `DATE` cast is exactly the failure Bronze exists not to own |
| **Daily partitioning** | Makes every 30-minute Silver run scan the whole accumulated day — ~$6,100/month, doubled by the `batch_days` DECLARE — and block pruning cannot rescue it, because clustering scatters `publish_time` |
| **`event_type` as the first cluster key** | Sorts every block by a 5-value column and weakens the two keys the test named |
| **No `require_partition_filter`** | Leaves a 135 TB unqualified scan one typo away |
| **Logical storage billing** | Strictly worse here: at ~3.4:1 it costs ~$1,100/month more for the same bytes |
| **A BigQuery Editions reservation** | Plausibly cheaper on the pipeline half — and it shares slots with the Part 2 agent, turning a hallucinated query from a failed bill into a freshness incident. Revisit past ~450 TB/month |
| **A scheduled purge job** | Partition expiration does the same with no code, no schedule, and no mis-scoped `DELETE` |

---

Next: [**2.3 — The deduplication query**](/part_1/06-dedup-sql.md)
