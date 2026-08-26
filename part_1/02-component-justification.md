# 1.2 — Component Justification

*Test bullet: justify the use of the chosen components (Pub/Sub, Dataflow/Beam, Cloud Storage, BigQuery, Airflow/Composer).*

**Three of the five named components are kept and two are rejected, on one sentence: no component sits between us and something we could call directly.** Pub/Sub, Cloud Storage and BigQuery each do work nothing else does. Dataflow would move five values from inside a JSON object to beside it; Composer would schedule a DAG with one system in it. Each rejection carries the condition that reinstates it. **Choosing components also fixes how many copies of the raw record exist**, so the four the 7-day rule binds are counted below.

---

| Named in the test | Verdict | Why |
|---|---|---|
| **Pub/Sub** | Kept | A buffer that survives a weekend outage, a clock no publisher can forge, and a topic schema that refuses a broken envelope at publish — a missing field is an error returned to the caller's own retry logic, not a NULL in a cluster key we find later by watching a queue |
| **Cloud Storage** | Kept | Inside the 7-day window it is the only thing that survives a mistake made inside BigQuery; past day 7 there is no rebuild path at all |
| **BigQuery** | Kept | A native subscription target, so 23k events/second land with no ingestion job of ours — and `MERGE` makes dedup, backfill and restatement one code path |
| **Dataflow / Beam** | **Rejected** — condition to reinstate stated | The only work it would do is move five values from inside a JSON object to beside it |
| **Airflow / Composer** | **Rejected** — Dataform instead | Right for a mixed DAG. This DAG has one system in it |

## Cloud Storage: Standard class, not Archive

**Cost.** Export subscriptions bill $50/TiB, and this topic carries \~41 TiB/month: the second one is \~$2,100/month plus \~$210 storage — flat, with no growth line, because the window is fixed.

## Dataflow / Beam — rejected

**Dataflow is right when the transformation cannot be expressed as a query over data the warehouse can already read** — no job here qualifies, and the condition that reinstates it is precise: the producer refuses to emit the field split, at which point a streaming job does it and nothing downstream changes.

## Airflow / Composer — rejected, Dataform instead

Airflow is right for a mixed DAG; **Composer's price for this one is a scheduler, a web server and a DAG processor billed continuously whether a DAG fires or not** — where Dataform is free, Google-operated, and compiles the dependency edge out of the SQL itself.

## Every copy of the raw record, named

| Copy | Expires by | At |
|---|---|---|
| **Pub/Sub backlog**, and the dead-letter topic with it | subscription retention on both, declared in Terraform — 7 days is also the default, so the control is the review, not the value | 7 days |
| **Bronze table** | `partition_expiration_days` — a table property, not a job that has to run | 7 days |
| **GCS archive** | bucket lifecycle rule, with soft-delete retention set to **0**: the default puts every lifecycle-deleted object in a 7-day holding area behind it | 7 days |
| **Bronze time travel, then fail-safe** | `max_time_travel_hours = 48`, BigQuery's minimum, then a fixed 7-day fail-safe that cannot be configured, queried, or shortened | **day 16** at the earliest |

Three of the four are declared, by Terraform or as a table property; the fourth cannot be configured at all. Beneath the archive, GCS soft delete is switched off. None of them is a job that has to run.

**The last row is disclosed rather than denied: raw payload survives in fail-safe until day 16.** No query of ours can read that residue, no process of ours can pause it, and no request of ours can extend it. It expires on a clock the storage engine runs.

**Cost.** Bronze's 7 days are \~$200/month against \~$2,500 at 90 days. The residue in the last row costs nothing. Bronze bills logically, and logical billing does not charge for time-travel or fail-safe bytes. Bullet 2.2 shows why an expiring table takes that setting. The GCS archive holds the same week for \~$210.

## Rejected — one line each

| Option | Why not |
|---|---|
| **Dataflow between Pub/Sub and Bronze** | A permanent runtime and its on-call, to perform a field split, at the same cost. Kept as the fallback if the producer will not supply the split |
| **One GCS sink, Bronze loaded by Dataform** | \~$1,840/month cheaper — one export subscription instead of two, plus \~$260 of external-table scan. It buys that by replacing a delivery Google guarantees with a time-window assumption our own SQL makes, on the one copy that cannot be rebuilt past day 7 |
| **Cloud Run / GKE consumer instead** | The same objection in a cheaper package, plus the acks, retries and redeliveries the native subscription handles for us |
| **Collector writing to BigQuery directly** | Deletes the durable buffer, turning every downstream failure into producer-side data loss |
| **Composer / Airflow** | Right for a mixed DAG; this one has a single system in it. Kept as a future option: Dataform's API lets us add it later |
| **dbt Core** | Its main argument is portability, and the stack is required to be single-warehouse. What remains is a Python runtime we patch, to submit SQL that BigQuery runs anyway |
| **BigQuery scheduled queries** | No dependency graph, and SQL living only in a console object contradicts the core of this design |
| **Pub/Sub retention alone, no GCS copy** | Not cheaper: retained messages bill at \$0.27/GiB-month, \~$2,640 for the same week against \~$210 in GCS Standard. And a replay is a re-ingest, so you cannot look at it without spending it |
| **GCS + BigLake as primary store** | No `MERGE`, no real pruning, no clustering |
| **Backlog retention at Pub/Sub's 31-day maximum** | A deeper buffer is a longer-lived copy of the raw record. Replay past day 7 has nothing to replay *into* — Bronze is gone — so the depth breaches the ceiling and buys nothing |
| **Leaving GCS soft delete at its 7-day default** | Turns a 7-day lifecycle rule into a 14-day one, invisibly, on the copy the rule binds hardest |
| **Time travel at BigQuery's 7-day default** | **Five** extra days of queryable raw payload past expiry — pushing the last row from day 16 to day 21 — to protect a table that is immutable and already archived to GCS |

---

Next: [**1.3 — Hot/Cold Path Separation**](/part_1/03-hot-cold-separation.md)
