# Part 1 — High-Volume Data Pipeline (GCP)

One page per bullet of the test, in the test's own order. Each stands alone.

## 1. Global Architecture

- [**1.1 — Propose a GCP architecture diagram, from raw event ingestion to availability for BI**](/part_1/01-architecture-diagram.md)
- [**1.2 — Justify the use of the chosen components**](/part_1/02-component-justification.md) — Pub/Sub, Dataflow/Beam, Cloud Storage, BigQuery, Airflow/Composer
- [**1.3 — Separate real-time processing (hot path) from batch archiving/re-processing (cold path)**](/part_1/03-hot-cold-separation.md)

## 2. BigQuery Modeling & Optimization

- [**2.1 — Propose a data organization according to the Medallion pattern**](/part_1/04-medallion-model.md) — Bronze, Silver, Gold
- [**2.2 — Configure partitioning and clustering on the Bronze table**](/part_1/05-bronze-partitioning.md) — minimize cost, fast queries on `publisher_id`, `ssp_id`, event date
- [**2.3 — Write the SQL query (using a window function) to deduplicate on `event_id`**](/part_1/06-dedup-sql.md) — Bronze → Silver

---

Next: [**Part 2 — LLM Agent Integration**](/part2-llm-agent.md)
