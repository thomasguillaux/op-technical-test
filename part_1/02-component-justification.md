# 1.2 — Component Justification

*Test bullet: justify the use of the chosen components (Pub/Sub, Dataflow/Beam, Cloud Storage, BigQuery, Airflow/Composer).*

| Named in the test | Verdict | Why |
|---|---|---|
| **Pub/Sub** | Kept | A buffer that survives a weekend outage, a clock no publisher can forge, and a topic schema that refuses a broken envelope at publish — a missing field is an error returned to the caller's own retry logic, not a NULL in a cluster key we find later by watching a queue |
| **Cloud Storage** | Kept | Inside the 7-day window it is the only thing that survives a mistake made inside BigQuery; past day 7 there is no rebuild path at all |
| **BigQuery** | Kept | A native subscription target, so 23k events/second land with no ingestion job of ours — and `MERGE` makes dedup, backfill and restatement one code path |
| **Dataflow / Beam** | **Rejected** — condition to reinstate stated | The only work it would do is move five values from inside a JSON object to beside it |
| **Airflow / Composer** | **Rejected** — Dataform instead | Right for a mixed DAG. This DAG has one system in it |


**Six components lost to the same sentence: *a runtime we operate, placed between us and something we could call directly.*** Three here; Cube, LangChain and a vector database in Part 2. One rule applied six times is a design; six separate verdicts would be taste.

## Cloud Storage: Standard class, not Archive


**Cost.** Export subscriptions bill $50/TiB, and this topic carries \~41 TiB/month: the second one is \~$2,100/month plus \~$210 storage — flat, with no growth line, because the window is fixed.

## Dataflow / Beam — rejected


## Airflow / Composer — rejected, Dataform instead


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

---

Next: [**1.3 — Hot/Cold Path Separation**](/part_1/03-hot-cold-separation.md)
