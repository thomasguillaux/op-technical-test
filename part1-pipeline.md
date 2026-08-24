# Part 1 — High-Volume Data Pipeline (GCP)

One page per bullet of the test, in the test's order. Each page stands alone.

One page comes first that is not a bullet: the client's retention rule reshaped six of the answers below, so it is stated once instead of six times.

- [**Retention & Anonymisation**](/part_1/00-retention-anonymisation.md) — the durable record is the anonymised event layer, and the error budget it sets

## 1. Global Architecture

- [**1.1 — Architecture Diagram**](/part_1/01-architecture-diagram.md) — ingestion to BI, six services split across a hot and a cold path
- [**1.2 — Component Justification**](/part_1/02-component-justification.md) — Pub/Sub, Dataflow/Beam, Cloud Storage, BigQuery, Airflow/Composer — three kept, two rejected
- [**1.3 — Hot/Cold Path Separation**](/part_1/03-hot-cold-separation.md) — where the hot path stops, and why batch owns everything past it

## 2. BigQuery Modeling & Optimization

- [**2.1 — Medallion Model**](/part_1/04-medallion-model.md) — Bronze, Silver, Gold — three layers, three contracts
- [**2.2 — Bronze Partitioning & Clustering**](/part_1/05-bronze-partitioning.md) — minimum cost, fast queries on `publisher_id`, `ssp_id`, event date
- [**2.3 — Deduplication, Bronze → Silver**](/part_1/06-dedup-sql.md) — the window function on `event_id`, and the `MERGE` that survives reruns

---

Next: [**Retention & Anonymisation**](/part_1/00-retention-anonymisation.md)
