# Part 1 — High-Volume Data Pipeline (GCP)

One page per bullet of the test, in the test's order. Each page stands alone.

## 1. Global Architecture

- [**1.1 — Six services, two shapes**](/part_1/01-architecture-diagram.md) — the architecture diagram, ingestion to BI
- [**1.2 — Three kept, two rejected**](/part_1/02-component-justification.md) — Pub/Sub, Dataflow/Beam, Cloud Storage, BigQuery, Airflow/Composer
- [**1.3 — Where the hot path stops**](/part_1/03-hot-cold-separation.md) — hot path against batch archiving and re-processing

## 2. BigQuery Modeling & Optimization

- [**2.1 — Three layers, three contracts**](/part_1/04-medallion-model.md) — the Medallion pattern: Bronze, Silver, Gold
- [**2.2 — Partition by arrival, cluster by publisher**](/part_1/05-bronze-partitioning.md) — minimum cost, fast queries on `publisher_id`, `ssp_id`, event date
- [**2.3 — Dedup that survives reruns**](/part_1/06-dedup-sql.md) — the window function on `event_id`, Bronze → Silver

---

Next: [**Part 2 — LLM Agent Integration**](/part2-llm-agent.md)
