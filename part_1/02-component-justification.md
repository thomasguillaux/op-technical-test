# 1.2 — Component Justification

*Test bullet: justify the use of the chosen components (Pub/Sub, Dataflow/Beam, Cloud Storage, BigQuery, Airflow/Composer).*

| Named in the test | Verdict | Why |
|---|---|---|
| **Pub/Sub** | Kept | A buffer that survives a weekend outage, and a clock nobody can forge |
| **Cloud Storage** | Kept | The only copy that has never been inside BigQuery |
| **BigQuery** | Kept | Storage and compute priced separately: data at rest is a storage line, not a cluster |
| **Dataflow / Beam** | **Rejected** — condition to reinstate stated | The only work it would do is move five values from inside a JSON object to beside it |
| **Airflow / Composer** | **Rejected** — Dataform instead | Right for a mixed DAG. This DAG has one system in it |

## Pub/Sub

*"It decouples producers from consumers"* justifies nothing — a load balancer decouples too. Two specific properties:

- **Durable retention of undelivered messages.** Any failure *downstream* of the buffer — the subscription, the warehouse write, our own bad deploy — loses nothing: the backlog drains, Silver's watermark reads the rows it never saw, the next Gold rebuild repairs the day, no human involved. **That turns the largest class of incidents from a manual backfill into a non-event.** The requirement sets the retention window, not the reverse.
- **`publish_time` is stamped by Google.** Bronze partitions on a clock no publisher can skew — by a wrong container timezone or on purpose, to move revenue across a month boundary. Bullet 2.2 depends on that clock being impossible to tamper with.

## Cloud Storage

**The archive does exactly one job: it is a failure domain independent of BigQuery.** Two jobs it looks like it should also do, and does not — named here before they are asked:

- **It does not extend retention.** The 7-day rule binds the *record*, not the store, so a second copy cannot outlive the obligation by living somewhere else.
- **It is not the source for a metric nobody anticipated.** That job belongs to Silver, typed wide and kept indefinitely precisely because this copy cannot be.

**A single justification carrying the whole line item is the sharpest cost challenge available against this design**, so it is met head-on rather than buried.

A dropped table, a bad DDL, a corrupting backfill, a mis-scoped IAM grant — every one is an error *inside* BigQuery, and time travel is 48 hours. **Past day 7 there is no rebuild path at all, so the archive is the only mechanism by which a mistake made on Tuesday is still fixable on Thursday.** **And BigQuery reads it in place** through a BigLake external table, so *"what did the collector actually send at 14:00?"* is a `SELECT` rather than a restore that could consume the window before the first query.

### Standard class, not Archive — the clause that decides it

| Class | $/GB/month | Minimum duration | Retrieval fee |
|---|---|---|---|
| **Standard** | **\~$0.020** | **none** | **none** |
| Nearline | \~$0.010 | 30 days | $0.01/GB |
| Coldline | \~$0.004 | 90 days | $0.02/GB |
| Archive | \~$0.0012 | 365 days | $0.05/GB |

**Archive is the reflex, and its 365-day minimum duration is why it loses.** The clause is easy to wave away — *"irrelevant, we keep the data anyway"* — and a 7-day window is exactly the case that invalidates that reasoning.

**Deleting at 7 days while being billed for 365 means paying for 365 days of accumulation, forever.** At 1.5 TB/day that is \~547 TB permanently on the invoice for 10.5 TB actually held — **\~$657/month on Archive against \~$210 on Standard.** The cheapest per-byte class is the most expensive in practice, by \~3×, and Standard also removes the retrieval fee on the replay the copy exists to serve. *The reusable mechanism: **minimum-duration clauses invert cold-tier economics whenever retention drops below the minimum**.*

**Cost.** Second export subscription \~$2,100/month plus \~$210 storage — **\~$28k/year, flat, with no growth line because the window is fixed.**

## BigQuery

Four properties are doing real work:

- **A native Pub/Sub subscription target.** 23k events/second land with no ingestion job of ours. Remove this and something we deploy has to sit in the middle.
- **Storage and compute priced apart.** Bronze's 7-day window at rest is \~$140/month of storage, not a cluster sized to hold it.
- **Cost is bytes scanned, not table size.** That is what makes the partitioning in bullet 2.2 matter, and what makes `maximum_bytes_billed` a real ceiling for the Part 2 agent.
- **`MERGE` and atomic partition replacement.** Dedup, backfill, and restating money after a reference-data correction are all SQL statements — one code path covers steady state and every repair.

**One cost lever, one setting: physical storage billing.** It costs 2× per byte and wins past 2:1 compression, which event JSON clears easily. **Where it earns its keep is Silver, not Bronze:** Bronze takes the setting too, but a 7-day window makes it a \~$140 table, while Silver grows without bound — roughly $3,500/month against $7,000 at five years.

## Dataflow / Beam — rejected

> **Dataflow is right when the transformation cannot be expressed as a query over data the warehouse can already read.**

Every candidate job here fails that test:

| Candidate job | Why it is not Dataflow |
|---|---|
| Field split on the hot path | The producer supplies the split |
| Replay from the GCS archive | BigLake reads the objects in place — replay is `INSERT … SELECT` |
| Large Bronze → Silver backfill | The same Dataform model over more partitions |
| **Per-source schema normalisation** | A field-path lookup per source is a `CASE` over data BigQuery already holds |
| **PII stripping at ingest** | The strongest case, and it fails on the quality of the control |

**The last two are new**, created by the client's own answers, and they deserve to be put at their strongest.

*"Schemas vary by source, so something must normalise them."* True, and it is the classic Dataflow job. But the normalisation is a JSON-path lookup, which BigQuery does natively — so Dataflow would be doing string extraction at the price of a permanent cluster, and the mapping would live in Beam code rather than in one reviewable file.

*"Raw must be deleted in 7 days, so strip the identifiers before they land."* This is the serious one, and it would genuinely reduce the compliance surface. It is rejected on control quality:

> **Stripping at ingest is a denylist: it removes the fields someone enumerated. A typed Silver schema is an allowlist: it admits only the fields someone enumerated. A new identifier an SSP starts sending next quarter passes straight through the first and is invisible to the second.**

The denylist also sits in a worse place — enforced by a running process rather than a table definition, so proving compliance means auditing deployed code instead of reading a schema — and a bug in the stripping logic destroys data on the only copy, with no undo.

**Both are answered by the same observation:**

> **The shorter the raw window, the more valuable it is that every transformation is a rerunnable SQL statement over landed data.**

With 7 days, re-running a fixed transform against data that is still there is the *only* repair left — and it exists precisely because nothing transforms the data before it lands. **The constraint that made Dataflow look necessary is the constraint that makes it most dangerous.**

**Cost is not the argument, and using it would be a mistake.** Native export subscriptions cost \~$140/TiB against \~$105/TiB for a standard subscription plus the Storage Write API, and Dataflow compute at this throughput costs a few hundred to a few thousand a month — **the two totals overlap across that whole range.** What decides it is operational surface: a streaming job is a deployed service where a subscription is a configuration, it has a process that can die and knobs someone owns forever, and Beam plus SQL means two homes for business logic.

***The only work Dataflow would do on this path is move five values from inside a JSON object to beside it. Paying for a cluster that runs permanently, and for its on-call, to do that is a component that has not justified its presence.***

**What brings it back:** the producer refuses to emit the split. Then a streaming Dataflow job does it, and nothing downstream changes. That puts work on a team we do not control — but **we ask for a message format, not analytical work**, and their collector already routes on `publisher_id` and `event_type` today. Asking *SSPs* to agree on field semantics is a different ask, not available at any price, which is why schema convergence is solved in Silver.

## Airflow / Composer — rejected, Dataform instead

Airflow is right for a mixed DAG: trigger a job, wait for an object, call a vendor API, load a warehouse. **Once the subscriptions have landed the data, this pipeline's whole job list is:** version the SQL, know that Gold depends on Silver, run four schedules (Silver every 30 min, Gold hourly, quality hourly and daily), alert on failure, allow a rerun for backfills. Nothing event-driven, no branching, nothing outside BigQuery. **The whole decision is sizing the orchestrator to that list**, and Composer's price for it is a GKE cluster and a scheduler billed every month whether a DAG fires or not, plus Airflow major-version upgrades.

**Dataform:** SQLX in Git, dependencies declared in the code, release configurations as the deploy artefact, workflow configurations as the schedule, assertions as the quality checks. Google operates it, it is free, and we pay only for the BigQuery it consumes. `${ref("silver_events")}` compiles the table name *and* creates the dependency edge, so the two cannot drift apart — unlike a DAG file sitting next to its SQL.

Its three real gaps:

| Dataform gap | Why it does not bite here |
|---|---|
| No retry mechanism | The watermark advances only on success, so the next scheduled run *is* the retry |
| A run is skipped if the previous is still going | Silver reads everything since the last successful watermark — a skipped 30-min run means the next covers 60 min, identically |
| Orchestrates nothing outside BigQuery | The only work outside BigQuery is GCS replay: rare, human-initiated, a runbook rather than a schedule. The reference data Silver joins is *declared*, not loaded — external tables read in place, so nothing fetches and nothing waits |

**The one gap we had to fill, and it is on the diagram:** Dataform logs every workflow invocation but sends no notification, so Cloud Logging → a log-based alert in Cloud Monitoring → the team's channel exists because otherwise the "alert on failure" requirement is not met.

*Orchestration does exist here — dependency resolution, scheduling, release management, quality gating. It is simply not a separate product to operate, because the DAG has one system in it.* And Dataform exposes an API, so a genuinely mixed step later means adding Composer *in front of* it, not rewriting a model.

## The spine

Dataflow, Composer and dbt Core all lost to the same sentence: **a runtime we operate, placed between us and something we could call directly.** One rule applied three times is a design; three separate verdicts would be taste. By the end of Part 2 the same rule accounts for three more: Cube, LangChain and a vector database.

**The obvious counterexample, closed:** bullet 2.3 uses Dataform's compile-time templating to expand a per-source mapping into `CASE` branches. That is a function evaluated while SQL we were writing anyway is compiled — it produces text, it runs in CI, and nothing about it exists at execution time. **A build step is not a runtime**, and that distinction is exactly the one the six rejections turn on.

## Rejected — one line each

| Option | Why not |
|---|---|
| **Dataflow between Pub/Sub and Bronze** | Four permanent maintenance duties, to perform a field split, at the same cost. Kept as the fallback if the producer will not supply the split |
| **Dataflow for per-source normalisation** | A field-path lookup is a `CASE` over data BigQuery already holds, and Beam moves the mapping from a reviewable config into pipeline code |
| **Dataflow for PII stripping at ingest** | A denylist enforced by a running process, against an allowlist enforced by a table definition — and it destroys data on the only copy, with no undo |
| **Cloud Run / GKE consumer instead** | The same objection in a cheaper package, plus the at-least-once handling the native subscription does for us |
| **Collector writing to BigQuery directly** | Deletes the durable buffer, turning every downstream failure into producer-side data loss |
| **Composer / Airflow** | Right for a mixed DAG; this one has a single system in it. Kept as a future option: Dataform's API lets us add it later |
| **dbt Core** | Its main argument is portability, and the stack is required to be single-warehouse. What remains is a Python runtime we patch, to submit SQL that BigQuery runs anyway |
| **BigQuery scheduled queries** | No dependency graph, and SQL living only in a console object contradicts the core of this design |
| **Archive or Nearline on the raw copy** | \~3× and \~2× more expensive at a 7-day window because of their minimum-duration clauses, plus a retrieval fee on the replay the copy exists to serve |
| **Indefinite retention on the archive** | Unlawful under the stated rule rather than merely expensive — the ceiling binds the record wherever it sits. Silver carries the durability instead |
| **Pub/Sub retention alone, no GCS copy** | The genuine cheaper alternative. Rejected on inspectability — a replay is a re-ingest, so you cannot look at it without spending it |
| **Scheduled export from Bronze to GCS** | \~$25k/year cheaper, and it routes the safety copy through the system it exists to survive |
| **GCS + BigLake as primary store** | No `MERGE`, no real pruning, no clustering |

---

Next: [**1.3 — Hot/Cold Path Separation**](/part_1/03-hot-cold-separation.md)
