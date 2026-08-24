# 1.2 — Three kept, two rejected

*Test bullet: justify the use of the chosen components (Pub/Sub, Dataflow/Beam, Cloud Storage, BigQuery, Airflow/Composer).*

| Named in the test | Verdict | Why |
|---|---|---|
| **Pub/Sub** | Kept | A buffer that survives a weekend outage, and a clock nobody can forge |
| **Cloud Storage** | Kept | The only copy that made no bet about which fields would matter |
| **BigQuery** | Kept | Storage and compute priced separately: data at rest is a storage line, not a cluster |
| **Dataflow / Beam** | **Rejected** — condition to reinstate stated | The only work it would do is move four values from inside a JSON object to beside it |
| **Airflow / Composer** | **Rejected** — Dataform instead | Right for a mixed DAG. This DAG has one system in it |

## <img src="../assets/icons/pubsub.png" width="22" style="vertical-align:middle"> Pub/Sub

*"It decouples producers from consumers"* justifies nothing — a load balancer decouples too. Two specific properties:

- **Durable retention of undelivered messages.** Any failure *downstream* of the buffer — the subscription, the warehouse write, our own bad deploy — loses nothing: the backlog drains, Silver's watermark reads the rows it never saw, the next Gold rebuild repairs the day, no human involved. That turns the largest class of incidents from *manual backfill* into *non-event*. The requirement sets the retention window, not the reverse.
- **`publish_time` is stamped by Google.** Bronze partitions on a clock no publisher can skew, by a wrong container timezone or on purpose, to move revenue across a month boundary. Bullet 2.2 depends on that clock being impossible to tamper with.

**Beaten alternative:** the collector writing straight to BigQuery via the Storage Write API. One component fewer, and no buffer — every downstream failure becomes data loss at the producer.

## <img src="../assets/icons/storage.png" width="22" style="vertical-align:middle"> Cloud Storage

Fidelity is not the reason: the producer supplies the envelope split, so Bronze already holds the complete message. Three jobs remain:

1. **Retention past Bronze's 90 days.** Silver keeps typed, deduplicated rows — not raw ones. Once a Bronze partition expires, no raw copy exists anywhere else.
2. **A failure domain independent of BigQuery.** A dropped table, a bad DDL, a mis-scoped IAM grant, a backfill that corrupts partitions — all errors *inside* BigQuery, where time travel is 7 days.
3. **The only source for a metric nobody anticipated.** Gold's dimensions are fixed at design time, Silver's schema at transform time; both are bets on what would matter. Raw makes no bet, and in adtech a field that is noise today becomes a segmentation dimension in eighteen months.

Job 3 is what sets retention to indefinite: **keeping unread data costs a few thousand a month, and deleting data we later need cannot be undone at any price.**

**Archive class from the first write, not a lifecycle rule that moves objects there later.** The chance of reading an object is low from the moment it is written, because *Bronze* serves the recent window. The usual objection to cold storage does not apply on GCP: Archive needs no restore delay, objects are read in milliseconds, and BigQuery queries them in place through BigLake. Replaying five years is a query, not a restore project.

**Beaten alternative:** a scheduled export from Bronze instead of a second subscription. It saves the export fee, \~$25k/year, and covers jobs 1 and 3. It fails job 2: the safety copy would pass through the system it exists to survive.

## <img src="../assets/icons/bigquery.png" width="22" style="vertical-align:middle"> BigQuery

Four properties are doing real work:

- **A native Pub/Sub subscription target.** 23k events/second land with no ingestion job of ours. Remove this and something we deploy has to sit in the middle.
- **Storage and compute priced apart.** Bronze's 90-day window standing at rest is \~$1,600/month of storage — against \~$2,700 on logical billing — not a cluster sized to hold it.
- **Cost is bytes scanned, not table size.** This is what makes the partitioning in bullet 2.2 matter, and what makes `maximum_bytes_billed` a real ceiling for the Part 2 agent.
- **`MERGE` and atomic partition replacement.** Dedup, backfill, and restating money after a reference-data correction are all SQL statements — one code path covers steady state and every repair.

**One cost lever, one setting:** physical storage billing on the Bronze and Silver datasets. It costs 2× per byte and wins past 2:1 compression, which event JSON clears easily. That is where the \~$1,600 above comes from, instead of \~$2,700. It also bills time-travel bytes, so Bronze's window drops to the 48-hour minimum: the data is immutable and GCS is the recovery path.

**Beaten alternative:** GCS + BigLake as the primary store. Cheaper storage, but no `MERGE`, no real partition pruning, no clustering — it deletes the dedup guarantee and the cost strategy together.

## <img src="../assets/icons/dataflow.png" width="22" style="vertical-align:middle"> Dataflow / Beam — rejected

> **Dataflow is right when the transformation cannot be expressed as a query over data the warehouse can already read.**

Every candidate job here fails that test:

| Candidate job | Why it is not Dataflow |
|---|---|
| Field split on the hot path | The producer supplies the split |
| Replay from the GCS archive | BigLake reads Archive in place — replay is `INSERT … SELECT` |
| Large Bronze → Silver backfill | The same Dataform model over more partitions |
| Bulk rewrite after wrong promotion logic | SQL, chunked by day |

**Cost is not the argument, and using it would be a mistake.** Native export subscriptions cost \~$140/TiB, against \~$105/TiB for a standard subscription plus the Storage Write API. Dataflow compute at this throughput costs between a few hundred and a few thousand a month, depending on tuning. The two totals overlap over that whole range.

What decides it is the operational surface:

1. **A streaming job is a deployed service; a subscription is a configuration.** Pipeline code, a build, an image, a pinned Beam SDK, a VPC, worker service accounts. Changing the field split becomes a code change and a job update, against a topic-schema revision and one IAM binding.
2. **It has a process that can die and knobs someone owns forever.** Ad traffic has a hard daily and weekly cycle: under-provision and the backlog grows through peak, over-provision and we pay for idle vCPU all night.
3. **Poison-message blast radius.** A malformed message can stall an entire key range, diagnosed by reading worker logs. A schema violation on the topic is dead-lettered individually and the stream continues.
4. **A second home for business logic.** Beam plus SQL means two languages, two test harnesses, and two places to look when a column is wrong.

***The only work Dataflow would do on this path is move four values from inside a JSON object to beside it. Paying for a cluster that runs permanently, and for its on-call, to do that is a component that has not justified its presence.***

**What brings it back:** the producer refuses to emit the split. Then a streaming Dataflow job does it, and nothing downstream changes. That dependency has a real cost, because it puts work on a team we do not control. The defence: we ask for a message format, not analytical work. Their collector already routes on `publisher_id` and `event_type` today.

## <img src="../assets/icons/composer.png" width="22" style="vertical-align:middle"> Airflow / Composer — rejected, Dataform instead

Airflow is right for a mixed DAG: trigger a job, wait for an object, call a vendor API, load a warehouse. **Once the subscriptions have landed the data, this pipeline's whole job list is:** version the SQL, know that Gold depends on Silver, run three schedules, alert on failure, allow a rerun for backfills. Nothing event-driven, no branching, nothing outside BigQuery. **The whole decision is sizing the orchestrator to that list.**

Composer's price: a GKE cluster and a scheduler billed every month whether a DAG fires or not, plus Airflow major-version upgrades. **Several hundred dollars a month and a Kubernetes upgrade cycle, to run three SQL jobs on a clock.**

**Dataform:** SQLX in Git, dependencies declared in the code, release configurations as the deploy artefact, workflow configurations as the schedule, assertions as the quality checks. Google operates it, it is free, and we pay only for the BigQuery it consumes. `${ref("silver_events")}` compiles the table name *and* creates the dependency edge, so the two cannot drift apart — unlike a DAG file sitting next to its SQL.

Its three real gaps:

| Dataform gap | Why it does not bite here |
|---|---|
| No retry mechanism | The watermark advances only on success, so the next scheduled run *is* the retry |
| A run is skipped if the previous is still going | Silver reads everything since the last successful watermark — a skipped 30-min run means the next covers 60 min, identically |
| Orchestrates nothing outside BigQuery | The only work outside BigQuery is GCS replay: rare, started by a human, and a runbook rather than a schedule. The reference data Silver joins is *declared*, not loaded: Drive-backed external tables are read in place, so there is no loading step to wait for |

**The one gap we had to fill, and it is on the diagram:** Dataform logs every workflow invocation but sends no notification. Cloud Logging → a log-based alert in Cloud Monitoring → the team's channel exists because otherwise the "alert on failure" requirement is not met.

*Orchestration does exist here: dependency resolution, scheduling, release management, quality gating. It is simply not a separate product to operate, because the DAG has one system in it.* Dataform also exposes an API, so if a truly mixed step appears later, Composer can be added *in front of* it without rewriting a model.

## The spine

Dataflow, Composer and dbt Core all lost to the same sentence: **a runtime we operate, placed between us and something we could call directly.** One rule applied three times is a design; three separate verdicts would be taste. By the end of Part 2 the same rule accounts for three more: Cube, LangChain and a vector database.

## Rejected — one line each

| Option | Why not |
|---|---|
| **Dataflow between Pub/Sub and Bronze** | Four permanent maintenance duties, to perform a field split, at the same cost. Kept as the fallback if the producer will not supply the split |
| **Cloud Run / GKE consumer instead** | The same objection in a cheaper package, plus the at-least-once handling the native subscription does for us |
| **Collector writing to BigQuery directly** | Deletes the durable buffer, turning every downstream failure into producer-side data loss |
| **Raw blobs in a staging table, promoted by SQL** | Adds a table, a job, and a second copy of 2B rows/day to move four fields |
| **Composer / Airflow** | Right for a mixed DAG; this one has a single system in it. Kept as a future option: Dataform's API lets us add it later |
| **SQL embedded in Airflow operators** | All of Composer's cost, and changing a definition or changing a schedule becomes the same commit |
| **dbt Core** | Its main argument is portability, and the stack is required to be single-warehouse. What remains is a Python runtime we patch, to submit SQL that BigQuery runs anyway |
| **BigQuery scheduled queries** | No dependency graph, and SQL living only in a console object contradicts the core of this design |
| **Scheduled export from Bronze to GCS** | \~$25k/year cheaper, and it routes the safety copy through the system it exists to survive |
| **GCS + BigLake as primary store** | No `MERGE`, no real pruning, no clustering |
| **Logical storage billing** | Strictly worse here: \~$1,100/month more for the same bytes |

---

Next: [**1.3 — Where the hot path stops**](/part_1/03-hot-cold-separation.md)
