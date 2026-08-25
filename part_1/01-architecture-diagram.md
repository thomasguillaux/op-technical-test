# 1.1 — Architecture Diagram

*Test bullet: propose a GCP architecture diagram, from raw event ingestion to availability for BI.*

![OptimusAds — event pipeline, ingestion to BI](../assets/architecture.png)

Six GCP services — Pub/Sub, Cloud Storage, BigQuery, Dataform, Cloud Logging, Cloud Monitoring — in two shapes. Left of Bronze, Google-operated configuration: one topic and its envelope schema, two native export subscriptions, a dead-letter topic. Right of Bronze, SQL on a clock. The reference architecture for this on GCP puts Dataflow between the topic and the warehouse; **that box is absent here, and its absence is the design** — argued, with the condition that brings it back, in bullet 1.2.

## The path, hop by hop

| # | Hop | Mechanism | Latency |
|---|---|---|---|
| 1 | Collector → `events` topic | The producer splits the envelope: `event_id`, `source_id`, `publisher_id`, `ssp_id`, `event_type` as named STRING fields on every event, their presence enforced by the topic schema; everything else, the auction context included, stays under `payload` | seconds |
| 2 | topic → `bronze_events` | **BigQuery export subscription.** Google stamps `publish_time` on receipt, so the partition key is a clock no publisher can skew | seconds |
| 3 | topic → GCS raw archive | **Cloud Storage export subscription.** Standard class, 7 days. A second subscription, not a copy of Bronze: it never passes through BigQuery | seconds |
| 4 | subscription → dead-letter topic | Two causes, both silent: BigQuery refuses the write because table and topic schema drifted apart, or `payload` does not hold valid JSON for a `JSON` column. A monitor watches depth. A message failing the *topic* schema never reaches here — the publish itself is refused, synchronously, to the producer | seconds |
| 5 | Bronze → Silver | **Dataform.** Read the rows between the watermark and a ceiling fixed from the data, dedupe on `event_id` with a window function, `MERGE` into `auction_day` partitions | every 30 min |
| 6 | Silver → Gold | **Dataform.** Rebuild the days whose Silver rows changed, within a trailing 3-day window. Hourly grain | hourly |
| 7 | Gold → semantic views → BI, and the Part 2 agent | BigQuery views, each metric formula written once; daily is a view over the hourly table. The agent reads the same views, not its own SQL over the tables | query time |
| 8 | Silver → `quality_hour` | **Dataform**, on its own tag and schedule. It judges the data the build path produced | hourly, plus a daily tier |

## Two writes from one topic, not one write and a copy

A scheduled export from Bronze to GCS would save the second export fee and place the safety copy *downstream* of the system it protects us from. Past day 7 there is no rebuild path, so a copy that has never been inside BigQuery is the only thing that survives a mistake made inside BigQuery — and because the archive subscription writes bytes and consults no schema, it also holds every message BigQuery declined, so a dead letter replays through the path already drawn rather than one invented for it.

## What pages, beyond "the job failed"

Dataform logs every workflow invocation and notifies no one, so Cloud Logging → a log-based alert in Cloud Monitoring → the team's channel is a real box on the diagram rather than decoration. That box covers a job reporting `FAILED`. **Every signal below is a way this pipeline can be wrong while every job reports success.**

Two kinds, and the difference is what happens when they fire — but one delivery path, because Cloud Monitoring cannot query BigQuery. A **monitor** is a Dataform action on the quality tag whose failure reaches the same log-based alert and blocks nothing; only dead-letter depth has a native metric. So the split is dependency wiring, not two systems. A **monitor** alerts into the team's channel and stops nothing. An **assertion** is a Dataform action that fails, blocking the *Gold* rebuild and never the Silver run: a gate upstream of Silver would stall anonymisation and run the 7-day clock down on data nobody can rebuild. Dataform does not do this by default: the Gold action sets `dependOnDependencyAssertions: true`, which is what makes the block real rather than assumed.

| Signal | Kind | Fires when | The failure it catches that a job-failure alert does not |
|---|---|---|---|
| Watermark age, Silver and Gold | monitor | `UNNEST(['silver_events','gold'])` left-joined to `pipeline_state`: no row, or `now − last_success` past 90 min and 3 h respectively | A run that never *started*: a disabled schedule or a deleted release config raises no error. **The join is the load-bearing part** — a query over `pipeline_state` alone cannot report a model whose row is absent, which is exactly the state a new environment is in |
| Dead-letter queue depth | monitor | non-zero and rising | A write BigQuery refused is dead-lettered *by design*, so nothing downstream fails and no job errors. Rising depth means the table schema has drifted from the topic's |
| Lateness beyond the assumed bound | monitor | `late_beyond_1h ÷ events` past its trailing-week baseline, per publisher — a raw non-zero count is guaranteed at 23k/s and would page continuously | Every window in this design derives from the 1-hour arrival bound. This is the row that makes *"we would know"* true |
| Silver writes outside the Gold window | monitor | a partition older than D-3 changed | Gold rebuilds a trailing 3 days. Data older than that lands correctly in Silver and is never aggregated — the one row where the cold path is wrong while every job is green |
| Null `publisher_payout` on an `impression` | **assertion** | any row resolves to null | An expired revenue-share row nulls money silently: the data is complete and wrong |

> **The failure that decides the shape.** A four-hour outage starting Friday at 21:00. Downstream of the durable buffer — the subscription, the warehouse write, a bad deploy — nothing is lost: the backlog drains, Silver's watermark reads the rows it never saw, the next hourly Gold rebuild repairs the day, and no human is involved. Only a failure *upstream* of the buffer loses data, when their collector cannot publish and has no buffer of its own. That turns the largest class of incidents from *"manual backfill on Monday"* into *"it fixed itself on Saturday at 01:00"* — a far stronger reason to put a topic there than *"it decouples producers from consumers."*

---

Next: [**1.2 — Component Justification**](/part_1/02-component-justification.md)
