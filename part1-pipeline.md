# Part 1 — High-Volume Data Pipeline (GCP)

**2B events/day — \~23,000/second sustained, \~1.5 TB/day raw.**

![OptimusAds — event pipeline, ingestion to BI](assets/architecture.png)

## The design in ten sentences

Six GCP services — Pub/Sub, Cloud Storage, BigQuery, Dataform, Cloud Logging, Cloud Monitoring — in **two shapes**: everything left of Bronze is Google-operated configuration, everything right of it is SQL on a clock; **no third shape** — no service we deploy, no runtime we patch, no process of ours that can fail between the publisher and the dashboard.

One topic feeds two export subscriptions in parallel: Bronze in BigQuery, and a GCS archive that has never been inside BigQuery.

The hot/cold line sits at Bronze, because **the hot path can fail but cannot be wrong** — no dedup, no join, no cast, only an envelope check that refuses a message or lets it through — so every error lives on the cold path, where the repair is running the same SQL again.

Raw logs are transient at 7 days, so the durable record is not raw: it is **Silver**, typed, anonymous and retained indefinitely.

Bronze itself validates nothing — a typed envelope plus an opaque JSON payload, partitioned **hourly** on Pub/Sub's `publish_time`, the *arrival* clock no publisher can skew, clustered on `publisher_id, ssp_id, event_type`, expiring at 7 days.

An event is queryable in Bronze in seconds, in Silver within 30 minutes, and in Gold at the next hourly rebuild.

Silver types, deduplicates and anonymises: a window function on `event_id` makes the `MERGE` legal, the `MERGE` makes the dedup correct across runs, and the typed schema *is* the anonymisation boundary — an allowlist fails closed where a stripping filter fails open.

Gold stores **hourly** rows bucketed by the *auction's* clock, with the daily tier as a view over them, so a day is the exact sum of its 24 hours and the two tiers cannot disagree.

**Two fact tables, not one, because there are two denominators**: `auctions`, for what share of inventory sold, and `bids + no_bids`, for whether a given SSP is worth keeping.

Dataform runs all of it — SQLX in Git, dependencies declared in the code, assertions as the quality gate — because this DAG has one system in it.

## Two spines

**Six components lost to the same sentence: *a runtime we operate, placed between us and something we could call directly.*** Dataflow, Composer and dbt Core here; Cube, LangChain and a vector database in Part 2. One rule applied six times is a design; six separate verdicts would be taste. Dataform's compile-time templating is not a counterexample — **a build step is not a runtime.**

**Raw data is transient; the durable record is the anonymised event layer.** The error budget moves from *we can always rebuild* to *we must be right inside 7 days, and know it* — which is why quality monitoring is load-bearing here rather than hygiene, and why the checks run hourly. A check that surfaces a problem on day 3 is a repair; the same check running weekly is an obituary.

**Cost.** No total on this page, and none anywhere — each page prices its own decision, so no argument rests on a figure. Worth knowing before reading further: the largest single lever in Part 1 is not a component choice. It is Bronze's partition grain, **\~$5,100/month between hourly and daily**, on one clause of DDL.

## Where to go deeper

One page per bullet of the test, in the test's order. Each page stands alone and ends with the options it rejected, one line each.

| Page | The claim it defends |
|---|---|
| [**Retention & Anonymisation**](/part_1/00-retention-anonymisation.md) | Not a bullet — the client's 7-day rule makes Bronze a replay buffer and Silver the source of truth |
| [**1.1 — Architecture Diagram**](/part_1/01-architecture-diagram.md) | Two writes from one topic, not one write and a copy — and the five signals that fire while every job reports success |
| [**1.2 — Component Justification**](/part_1/02-component-justification.md) | Pub/Sub, Cloud Storage, BigQuery kept; Dataflow and Composer rejected, each with the condition that brings it back |
| [**1.3 — Hot/Cold Path Separation**](/part_1/03-hot-cold-separation.md) | Four repair triggers, one code path — and why a batch path must exist regardless |
| [**2.1 — Medallion Model**](/part_1/04-medallion-model.md) | Type wide, aggregate narrow; hourly stored and daily derived; `is_settled` published, not inferred |
| [**2.2 — Bronze Partitioning & Clustering**](/part_1/05-bronze-partitioning.md) | The dominant Bronze query is not a human's — it is Silver's watermark read, 48 times a day |
| [**2.3 — Deduplication, Bronze → Silver**](/part_1/06-dedup-sql.md) | The window function as asked, then the `MERGE` that makes it correct across runs |

---

Next: [**Retention & Anonymisation**](/part_1/00-retention-anonymisation.md)
