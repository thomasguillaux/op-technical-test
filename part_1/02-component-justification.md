# 1.2 — Component Justification

*Test bullet: justify the use of the chosen components (Pub/Sub, Dataflow/Beam, Cloud Storage, BigQuery, Airflow/Composer).*

| Named in the test | Verdict | Why |
|---|---|---|
| **Pub/Sub** | Kept | A buffer that survives a weekend outage, a clock no publisher can forge, and a topic schema that refuses a broken envelope at publish — a missing field is an error returned to the caller's own retry logic, not a NULL in a cluster key we find later by watching a queue |
| **Cloud Storage** | Kept | Inside the 7-day window it is the only thing that survives a mistake made inside BigQuery; past day 7 there is no rebuild path at all |
| **BigQuery** | Kept | A native subscription target, so 23k events/second land with no ingestion job of ours — and `MERGE` makes dedup, backfill and restatement one code path |
| **Dataflow / Beam** | **Rejected** — condition to reinstate stated | The only work it would do is move five values from inside a JSON object to beside it |
| **Airflow / Composer** | **Rejected** — Dataform instead | Right for a mixed DAG. This DAG has one system in it |

Two components the test does not name: **Dataform**, argued below, and **Cloud Logging → Cloud Monitoring**.

**Six components lost to the same sentence: *a runtime we operate, placed between us and something we could call directly.*** Three here; Cube, LangChain and a vector database in Part 2. One rule applied six times is a design; six separate verdicts would be taste.

## Cloud Storage: Standard class, not Archive

| Class | $/GB/month | Minimum duration | Retrieval fee |
|---|---|---|---|
| **Standard** | **\~$0.020** | **none** | **none** |
| Nearline | \~$0.010 | 30 days | $0.01/GB |
| Archive | \~$0.0012 | 365 days | $0.05/GB |

*Single-region list prices.* Standard is chosen on minimum duration, not on per-GB price. Archive is the reflex, but its 365-day minimum means deleting at 7 days still bills 365 days of accumulation, forever: \~547 TB permanently on the invoice for the 10.5 TB actually held, \~$657/month against \~$210.

**The cheapest per-byte class is the most expensive in practice, by \~3×.** Standard also has no retrieval fee on the replay the copy exists to serve. Retention shorter than the minimum inverts cold-tier economics.

**Cost.** Second export subscription \~$2,100/month plus \~$210 storage — flat, with no growth line, because the window is fixed.

## Dataflow / Beam — rejected

> Dataflow is right when the transformation cannot be expressed as a query over data the warehouse can already read.

Every candidate job here fails that test:

| Candidate job | Why it is not Dataflow |
|---|---|
| Field split on the hot path | The producer supplies the split |
| Replay from the GCS archive | BigLake reads the objects in place — replay is `INSERT … SELECT` |
| Large Bronze → Silver backfill | The same Dataform model over more partitions |
| Per-source schema normalisation | A field-path lookup per source is a `CASE` over data BigQuery already holds |
| PII stripping at ingest | Stripping is a denylist; a typed Silver schema is an allowlist. A new identifier an SSP starts sending next quarter passes straight through the first |

The last row is the serious one: raw is deleted in 7 days, so identifiers would have to be stripped before they land.

It fails on the quality of the control, not on cost. A denylist enforced by a running process rather than by a table definition means a bug destroys data on the only copy, with no undo — the same constraint that argues for Dataflow is what makes it dangerous.

The two paths overlap across the range: two native export subscriptions (\~$140/TiB) against a standard subscription plus the Storage Write API (\~$105/TiB) plus Dataflow compute. Cost does not decide it. Operational surface does — a streaming job is a deployed service where a subscription is a configuration, and Beam plus SQL means two homes for business logic.

*What brings it back:* the producer refuses to emit the split. Then a streaming Dataflow job does it and nothing downstream changes. Asking their collector for a message format is not asking for analytical work — it already routes on `publisher_id` and `event_type`. Asking *SSPs* to agree on field semantics is a different ask, unavailable at any price, which is why schema convergence is solved in Silver.

## Airflow / Composer — rejected, Dataform instead

Airflow is right for a mixed DAG: trigger a job, wait for an object, call a vendor API, load a warehouse. Once the subscriptions have landed the data, this pipeline's whole job list is: version the SQL, know that Gold depends on Silver, run four schedules, alert on failure, allow a rerun. Nothing event-driven, no branching, nothing outside BigQuery. **Composer's price for that list is a scheduler, a web server and a DAG processor billed continuously whether a DAG fires or not, plus Airflow major-version upgrades we own.**

Dataform: SQLX in Git, dependencies declared in the code, release configurations as the deploy artefact, workflow configurations as the schedule, assertions as the quality checks. Google operates it, it is free, and we pay only for the BigQuery it consumes. `${ref("silver_events")}` compiles the table name *and* creates the dependency edge, so the two cannot drift apart — unlike a DAG file sitting next to its SQL.

Its three real gaps:

| Dataform gap | Why it does not bite here |
|---|---|
| No retry mechanism | The watermark advances only on success, so the next scheduled run *is* the retry |
| A run is skipped if the previous is still going | Silver reads everything since the last successful watermark, so the next run covers 60 minutes instead of 30, identically. A skip creates no workflow invocation and so emits no failure log — what catches it is the watermark-age monitor of bullet 1.1, which is why that monitor exists |
| Orchestrates nothing outside BigQuery | The only work outside BigQuery is GCS replay: rare, human-initiated, a runbook rather than a schedule. The reference data Silver joins is *declared*, not loaded — external tables read in place, so nothing fetches and nothing waits |

Orchestration exists here: dependency resolution, scheduling, release management, quality gating. It is not a separate product to operate.

## Rejected — one line each

| Option | Why not |
|---|---|
| **Dataflow between Pub/Sub and Bronze** | A permanent runtime and its on-call, to perform a field split, at the same cost. Kept as the fallback if the producer will not supply the split |
| **Cloud Run / GKE consumer instead** | The same objection in a cheaper package, plus the acks, retries and redeliveries the native subscription handles for us |
| **Collector writing to BigQuery directly** | Deletes the durable buffer, turning every downstream failure into producer-side data loss |
| **Composer / Airflow** | Right for a mixed DAG; this one has a single system in it. Kept as a future option: Dataform's API lets us add it later |
| **dbt Core** | Its main argument is portability, and the stack is required to be single-warehouse. What remains is a Python runtime we patch, to submit SQL that BigQuery runs anyway |
| **BigQuery scheduled queries** | No dependency graph, and SQL living only in a console object contradicts the core of this design |
| **Pub/Sub retention alone, no GCS copy** | The genuine cheaper alternative. Rejected on inspectability — a replay is a re-ingest, so you cannot look at it without spending it |
| **GCS + BigLake as primary store** | No `MERGE`, no real pruning, no clustering |

---

Next: [**1.3 — Hot/Cold Path Separation**](/part_1/03-hot-cold-separation.md)
