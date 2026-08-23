# 1.2 — Justify the use of the chosen components (Pub/Sub, Dataflow/Beam, Cloud Storage, BigQuery, Airflow/Composer)

| Named in the test | Verdict | Why |
|---|---|---|
| **Pub/Sub** | Kept | A buffer that outlasts a weekend outage, and a clock we cannot forge |
| **Cloud Storage** | Kept | The only copy that made no bet about which fields would matter |
| **BigQuery** | Kept | Storage and compute priced apart: 40 TB standing is a storage line, not a cluster |
| **Dataflow / Beam** | **Rejected** — condition to reinstate stated | The only work it would do is move four values from inside a JSON object to beside it |
| **Airflow / Composer** | **Rejected** — Dataform instead | Right for a heterogeneous DAG. This DAG has one system in it |

## Pub/Sub

*"It decouples producers from consumers"* justifies nothing — a load balancer decouples too. Two specific properties:

- **Durable retention of undelivered messages.** Any failure *downstream* of the buffer — the subscription, the warehouse write, our own bad deploy — loses nothing: the backlog drains, Silver's watermark picks up rows it never saw, the next Gold rebuild repairs the day, no human involved. That converts the largest class of incidents from *manual backfill* into *non-event*. The requirement sets the retention window, not the other way round.
- **`publish_time` is stamped by Google.** Bronze partitions on a clock no publisher can skew — whether by a wrong container timezone or deliberately, to move revenue across a month boundary. Bullet 2.2 depends on that being untamperable.

**Beaten alternative:** the collector writing straight to BigQuery via the Storage Write API. One component fewer, and no buffer — every downstream failure becomes data loss at the producer.

## Cloud Storage

Not fidelity: the producer supplies the envelope split, so Bronze already holds the complete message. Three jobs remain:

1. **Retention past Bronze's 90 days.** Silver keeps typed, deduplicated rows — not raw ones. Once a Bronze partition expires, no raw copy exists anywhere else.
2. **A failure domain independent of BigQuery.** A dropped table, a bad DDL, a mis-scoped IAM grant, a backfill that corrupts partitions — all errors *inside* BigQuery, where time travel is 7 days.
3. **The only source for a metric nobody anticipated.** Gold's dimensions are fixed at design time and Silver's schema at transform time; both are bets on what would matter. Raw made no bet — and in adtech, a field that is noise today is a segmentation dimension in eighteen months.

Job 3 is what sets retention to indefinite: **keeping unread data costs a few thousand a month; deleting data later needed cannot be undone at any price.**

**Archive class, written directly rather than lifecycled into it** — read probability is uniformly low from the moment the object is written, because *Bronze* serves the recent window. The usual objection to cold storage does not apply on GCP: Archive has no thaw, objects read in milliseconds, and BigQuery queries them in place through BigLake. Replaying five years is a query, not a restore project.

**Beaten alternative:** a scheduled export from Bronze instead of a second subscription. Saves the export fee outright — ~$25k/year — satisfies jobs 1 and 3, and fails job 2: the safety copy would route through the system it exists to survive.

## BigQuery

Four properties are doing real work:

- **A native Pub/Sub subscription target.** 23k events/second land with no ingestion job of ours. Remove this and something we deploy has to sit in the middle.
- **Storage and compute priced apart.** 40 TB standing in Bronze is ~$1,600/month of storage — against ~$2,700 on logical billing — not a cluster sized to hold it.
- **Cost is bytes scanned, not table size.** This is what makes bullet 2.2's partitioning load-bearing rather than cosmetic, and what makes `maximum_bytes_billed` a real ceiling for the Part 2 agent.
- **`MERGE` and atomic partition replacement.** Dedup, backfill, and restating money after a reference-data correction are all SQL statements — one code path covers steady state and every repair.

**One cost lever, one setting:** physical storage billing on the Bronze and Silver datasets. It costs 2× per byte and wins past 2:1 compression: Bronze's 135 TB logical land at ~40 TB on disk, ~3.4:1, which is where the ~$1,600 above comes from instead of ~$2,700. It also bills time-travel bytes, so Bronze's window goes to the 48-hour minimum — the data is immutable and GCS is the recovery path.

**Beaten alternative:** GCS + BigLake as the primary store. Cheaper storage, but no `MERGE`, no real partition pruning, no clustering — it deletes the dedup guarantee and the cost strategy together.

## Dataflow / Beam — rejected

> **Dataflow is right when the transformation cannot be expressed as a query over data the warehouse can already read.**

Every candidate job here fails that rule:

| Candidate job | Why it is not Dataflow |
|---|---|
| Field split on the hot path | The producer supplies the split |
| Replay from the GCS archive | BigLake reads Archive in place — replay is `INSERT … SELECT` |
| Large Bronze → Silver backfill | The same Dataform model over more partitions |
| Bulk rewrite after wrong promotion logic | SQL, chunked by day |

**Cost is not the argument, and claiming it would be a trap.** Native export subscriptions run ~$140/TiB against ~$105/TiB for a standard subscription plus the Storage Write API; Dataflow compute at this throughput lands anywhere from several hundred to low thousands a month depending on tuning. The two totals overlap across that entire band.

What decides it is operational surface:

1. **A streaming job is a deployed service; a subscription is a configuration.** Pipeline code, a build, an image, a pinned Beam SDK, a VPC, worker service accounts. Changing the field split becomes a code change and a job update, against a topic-schema revision and one IAM binding.
2. **It has a process that can die and knobs someone owns forever.** Ad traffic has a hard daily and weekly cycle: under-provision and the backlog grows through peak, over-provision and we pay for idle vCPU all night.
3. **Poison-message blast radius.** A malformed message can stall an entire key range, diagnosed by reading worker logs. A schema violation on the topic is dead-lettered individually and the stream continues.
4. **A second home for business logic.** Beam plus SQL means two languages, two test harnesses, and two places to look when a column is wrong.

***The only work Dataflow would do on this path is move four values from inside a JSON object to beside it. Paying for a permanently-running cluster, and its on-call, to do that is the definition of a component that has not justified its presence.***

**The condition that reinstates it:** the producer refuses to emit the split. Then a streaming Dataflow job does it and nothing downstream changes. That dependency is a real cost — work pushed onto a team we do not control — and the defence is that it is a message format, not analytical work: their collector already routes on `publisher_id` and `event_type` today.

## Airflow / Composer — rejected, Dataform instead

Airflow is right for a heterogeneous DAG: trigger a job, wait on an object, call a vendor API, load a warehouse. **After the subscriptions land the data, this pipeline's entire job list is** — version the SQL, know that Gold depends on Silver, run three schedules, alert on failure, allow a rerun for backfills. Nothing event-driven, nothing branching, nothing outside BigQuery. **Sizing the orchestrator to that list is the whole decision.**

Composer's price for it: a GKE cluster and scheduler carrying a standing monthly floor whether or not a DAG fires, plus an Airflow major-version upgrade path — **several hundred dollars a month and a Kubernetes upgrade cadence, to run three SQL jobs on a clock.**

**Dataform:** SQLX in Git, dependencies declared in the code, release configurations as the deploy artefact, workflow configurations as the schedule, assertions as the quality checks. Google operates it, it is free, and we pay only the BigQuery consumed. `${ref("silver_events")}` compiles the table name *and* creates the dependency edge — so unlike a DAG file sitting beside its SQL, the two cannot drift.

Its three real gaps, named before a reviewer finds them:

| Dataform gap | Why it does not bite here |
|---|---|
| No retry mechanism | The watermark advances only on success, so the next scheduled run *is* the retry |
| A run is skipped if the previous is still going | Silver reads everything since the last successful watermark — a skipped 30-min run means the next covers 60 min, identically |
| Orchestrates nothing outside BigQuery | The only non-BigQuery work is GCS replay: rare, human-initiated, and a runbook rather than a schedule. The reference data Silver joins is *declared*, not loaded — Drive-backed external tables read in place — so it adds no step to wait on |

**The one gap that needed building, and is on the diagram:** Dataform logs every workflow invocation but ships no notification, so Cloud Logging → a log-based alert in Cloud Monitoring → the team's channel exists because the "alert on failure" requirement would otherwise go unmet.

*Orchestration absolutely exists here — dependency resolution, scheduling, release management, quality gating. It is not a separate product to operate, because the DAG has one system in it.* And Dataform exposes an API, so if a genuinely heterogeneous step appears later, Composer can be added *in front of* it without rewriting a model.

## The spine

Dataflow, Composer and dbt Core all lost to the same sentence: **a runtime we operate, placed between us and something we could call directly.** One rule applied three times is a design; three separate verdicts would be taste. By the end of Part 2 the same rule accounts for three more — Cube, LangChain, and a vector database.

## Rejected — one line each

| Option | Why not |
|---|---|
| **Dataflow between Pub/Sub and Bronze** | Four standing maintenance obligations to perform a field split; cost is a wash. Retained as the fallback if the producer will not supply the split |
| **Cloud Run / GKE consumer instead** | The same objection in a cheaper wrapper, plus the at-least-once reasoning the native subscription handles |
| **Collector writing to BigQuery directly** | Deletes the durable buffer, turning every downstream failure into producer-side data loss |
| **Raw blobs in a staging table, promoted by SQL** | Adds a table, a job, and a second copy of 2B rows/day to move four fields |
| **Composer / Airflow** | Right for a heterogeneous DAG; this one has a single system in it. Retained as a future option — Dataform's API makes it additive |
| **SQL embedded in Airflow operators** | All of Composer's cost, and changing a definition and changing a cadence become the same commit |
| **dbt Core** | Portability is its central argument, and the stack is mandated single-warehouse. What remains is a Python runtime we patch to submit SQL BigQuery runs anyway |
| **BigQuery scheduled queries** | No dependency graph, and SQL living only in a console object contradicts the design's core defence |
| **Scheduled export from Bronze to GCS** | ~$25k/year cheaper, and it routes the safety copy through the system it exists to survive |
| **GCS + BigLake as primary store** | No `MERGE`, no real pruning, no clustering |
| **Logical storage billing** | Strictly worse: at ~3.4:1 it costs ~$1,100/month more for the same bytes |

---

Next: [**1.3 — Hot path and cold path**](/part_1/03-hot-cold-separation.md)
