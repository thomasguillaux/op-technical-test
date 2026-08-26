# 1.1 — Architecture Diagram

*Test bullet: propose a GCP architecture diagram, from raw event ingestion to availability for BI.*

**Eight hops, and not one of them is a runtime we operate.** The path from raw event to BI is two native Pub/Sub export subscriptions and three Dataform models. The durable buffer sits at the topic, so every failure downstream of it is a rerun rather than a backfill — where a collector writing to BigQuery directly turns each of those same failures into producer-side data loss.

---

![OptimusAds — event pipeline, ingestion to BI](../assets/architecture.png)

## The path, hop by hop

| # | Hop | Mechanism | Latency |
|---|---|---|---|
| 1 | Collector → `events` topic | The producer splits the envelope: `event_id`, `source_id`, `publisher_id`, `ssp_id`, `event_type` as named STRING fields on every event, their presence enforced by the topic schema; everything else, the auction context included, stays under `payload` | — |
| 2 | topic → `bronze_events` | **BigQuery export subscription.** Google stamps `publish_time` on receipt, so the partition key is a clock no publisher can skew | — |
| 3 | topic → GCS raw archive | **Cloud Storage export subscription**, Avro carrying the topic schema, so BigLake reads it in place on a replay. Standard class, 7 days. A second subscription, not a copy of Bronze: it never passes through BigQuery | — |
| 4 | subscription → dead-letter topic | Two causes, both silent: BigQuery refuses the write because table and topic schema drifted apart, or `payload` does not hold valid JSON for a `JSON` column. A monitor watches depth. A message failing the *topic* schema never reaches here — the publish itself is refused, synchronously, to the producer | — |
| 5 | Bronze → Silver | **Dataform.** Read the rows between the watermark and a ceiling fixed from the data, dedupe on `event_id` with a window function, `MERGE` into `auction_day` partitions | every 30 min |
| 6 | Silver → Gold | **Dataform.** Rebuild the days whose Silver rows changed, within a trailing 3-day window. Hourly grain | hourly |
| 7 | Gold → semantic views → BI, and the Part 2 agent | BigQuery views, each metric formula written once; daily is a view over the hourly table. The agent reads the same views, not its own SQL over the tables | query time |
| 8 | Silver → `quality_hour` | **Dataform**, on its own tag and schedule. It judges the data the build path produced | hourly, plus a daily tier |

A **monitor** is a Dataform action on the quality tag. Its failure reaches the same log-based alert and blocks nothing. Two monitors are Cloud Monitoring policies instead — dead-letter depth at hop 4, and delivery reconciliation below — because their inputs are native Pub/Sub metrics and no SQL can reach them. The split is dependency wiring, not two systems.

An **assertion** is a Dataform action that fails, blocking the *Gold* rebuild and never the Silver run. A gate upstream of Silver would stall anonymisation and run the 7-day clock down on data nobody can rebuild.

| Signal | Kind | Fires when | The failure it catches that a job-failure alert does not |
|---|---|---|---|
| Watermark age, Silver and Gold | monitor | `UNNEST(['silver_events','gold'])` left-joined to `pipeline_state`: no row, or `now − last_success` past 90 min and 3 h respectively | A run that never *started*: a disabled schedule or a deleted release config raises no error. **The join is the load-bearing part** — a query over `pipeline_state` alone cannot report a model whose row is absent, which is exactly the state a new environment is in |
| Delivery reconciliation | monitor | hourly: the topic's published-message count (`topic/message_sizes`) against `subscription/ack_message_count` on each export subscription — a message whose write fails is nacked, so an ack means the row landed. Any divergence | A message Pub/Sub acknowledged to the producer that a sink never wrote. Nothing fails, nothing dead-letters, and past day 7 there is nothing left to compare against. **Two sinks on one topic make the check free** — three native counters that must agree, so a sink drifting alone is visible without reading a byte of either copy |
| Null `publisher_payout` on an `impression` | **assertion** | any row resolves to null | An expired revenue-share row nulls money silently: the data is complete and wrong |

> **The failure that decides the shape.** A four-hour outage starting Friday at 21:00. Downstream of the durable buffer — the subscription, the warehouse write, a bad deploy — nothing is lost: the backlog drains, Silver's watermark reads the rows it never saw, the next hourly Gold rebuild repairs the day, and no human is involved. Only a failure *upstream* of the buffer loses data, when their collector cannot publish and has no buffer of its own. That turns the largest class of incidents from a manual backfill on Monday into a self-repair at 01:00 on Saturday.

---

Next: [**1.2 — Component Justification**](/part_1/02-component-justification.md)
