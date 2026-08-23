# Repo rules

This repo is public. It answers a real company's technical test, anonymized.

- Never write the real company name anywhere in this repo (files, commits, diagrams, filenames). Use **OptimusAds** instead — in publisher names, URLs, screenshots, everything.
- Real product/business details (from their site, the PDF) can inform the design work, they just can't be attributed by name in checked-in content.

## Design preference

Favor the simplest architecture that satisfies the requirement over a comprehensive or impressive-looking one. When two GCP designs both work, pick the one with fewer moving parts. Justify each component's presence — no component "because it's best practice" or "for future scale" without a concrete reason tied to this scenario.

## Working rules

The output is defended live in a ~1h presentation. Optimize for argumentation, not coverage.

- Before asking a question or writing a paragraph, test it: does this change the design? If not, cut it.
- Never assume a component (Dataflow, Composer, dbt, a specific model). Components are the answer, not the input. Requirements are the input.
- Straight to the point. No fluff, no hedging, no padding to look thorough.
- **One question at a time.** Never batch questions, even when a skill's format suggests a round of them. Ask, wait, then recompute what's still open.
- Every design claim must be defensible under challenge: state the requirement it satisfies and the alternative it beats.
- **Where our design diverges from the test's literal wording, lead with their construct, then extend it.** Answer the question as asked first, then show why it is insufficient and what wraps it. The grader checks a box before judging depth; opening with the divergence reads as not having done what was asked for the seconds before the justification lands. Applies to the dedup SQL (window function, then the MERGE around it) and to Bronze partitioning ("partitioned by date", then which date and why).
- **Pair each defensive choice with a concrete incident narrative.** "3-day window" is forgettable; "a Friday-evening failure found Monday morning repairs itself before anyone logs in" is what makes a decision land. Add new ones to `docs/incident-narratives.md`.
- Record decisions in `docs/` **with the argument that justifies them**, not just the conclusion. The conclusion alone is useless when challenged.

## Where things live

Read the relevant file before working in that area. Linked, not imported — load on demand.

**Business assumptions** — given by the client, not derived. Do not re-litigate.
- [docs/business_assumptions/assumptions.md](docs/business_assumptions/assumptions.md) — volume, timing bounds, freshness, retention, users, deliverable

**Design decisions** — reached by grilling. Each carries the argument that justifies it.
- [docs/design_decisions/execution-model.md](docs/design_decisions/execution-model.md) — **DECIDED: scheduled batch.** Continuous rejected: it removes none of the mechanisms it claims to, since backfill/replay/restatement are batch regardless. Also defines hot path vs cold path.
- [docs/design_decisions/incoming-data.md](docs/design_decisions/incoming-data.md) — producer boundary, event types, envelope/payload split, **Bronze DDL** — partition on arrival date (event-date queries are Silver's job, which is the Medallion answer), clustering order justified on prefix-ordering, `require_partition_filter`
- [docs/design_decisions/hot-path.md](docs/design_decisions/hot-path.md) — **DECIDED.** Pub/Sub + native BigQuery/GCS export subscriptions, no stream processor. **Dataflow has no job anywhere** — every candidate is expressible as SQL over data BigQuery already reads; it stays named as the fallback if the producer won't split the envelope. Argument is operational surface, not cost — cost is a wash and saying so first is the defence.
- [docs/design_decisions/raw-archive.md](docs/design_decisions/raw-archive.md) — **DECIDED.** Live GCS subscription (independent failure domain), Archive class from day 0, **indefinite** retention. Third purpose is decisive: raw is the only source for a metric nobody anticipated, since Gold's grain and Silver's schema are both fixed at design time. Archive class survives the reprocessing use case on the numbers.
- [docs/design_decisions/transform-orchestration.md](docs/design_decisions/transform-orchestration.md) — **DECIDED.** Dataform, no Composer, no dbt runtime. Its two gaps (no retries, skipped overlapping runs) are neutralised by the watermark. Must still build: Cloud Logging log-based alert.
- [docs/design_decisions/silver.md](docs/design_decisions/silver.md) — watermark read boundary, MERGE dedup, partitioning, enrichment from mutable reference data applied here rather than at ingest, and the **typed schema** — one table for all five types, `ssp_id` nullable on `auction`, revenue recognised on `impression`, **no residual payload** (the archive already holds it, indefinitely)
- [docs/design_decisions/gold.md](docs/design_decisions/gold.md) — 4h refresh, 3-day window, change detection, and **two fact tables** (`gold_opportunity`, `gold_ssp`) because inventory fill and SSP participation have denominators neither can express for the other
- [docs/design_decisions/retention-and-storage.md](docs/design_decisions/retention-and-storage.md) — **DECIDED.** One principle sets all four retention figures (pay indefinitely for what can't be recreated, shortest useful window for what can). Physical storage billing, time-travel reduction, partition expiration over purge jobs. FinOps material for Part 2 Q3.
- [docs/design_decisions/data-quality.md](docs/design_decisions/data-quality.md) — daily check job, lateness monitoring, quality table
- [docs/design_decisions/llm-approach.md](docs/design_decisions/llm-approach.md) — **DECIDED.** One agent, four tools, built not bought. Free SQL for *what*, fixed routine for *why* — split derived from catchability, not compromise. Guardrails, scope of access, the end-to-end flow, and why no vector DB.
- [docs/design_decisions/diagnose-change.md](docs/design_decisions/diagnose-change.md) — **DECIDED.** The *why*-question routine, specified: quality check first, structural factorisation, then an exact rate-effect/mix-effect attribution one dimension at a time. Localises a change, does not claim to explain it.
- [docs/design_decisions/semantic-layer.md](docs/design_decisions/semantic-layer.md) — **DECIDED.** BigQuery views, ratios at read time, additive measures only in Gold. Full metric list: eCPM on gross, fill rate factored into its three stages (each a different owner and fix), `rpm` because eCPM and fill rate trade against each other. Two views, and `diagnose_change` reads them rather than the base tables.
- [docs/design_decisions/incident-narratives.md](docs/design_decisions/incident-narratives.md) — presentation material

**Domain vocabulary** — [CONTEXT.md](CONTEXT.md), business terms only, no architecture.

## Work order

Cover every line of the evaluation grid before deepening any one of them. Go deep only where the test names a deliverable.

1. ~~**Execution model**~~ — **done.** Scheduled batch.
2. ~~**Component choices, both parts at once, box level only**~~ — **done.** Ingestion, transform, orchestration, semantic layer, model, guardrails, alerting all settled with the alternative each beats.
3. ~~**Architecture diagram**~~ — **done.** Two diagrams, one per test question. `diagrams_src/architecture.py` → `assets/architecture.png` (hot/cold as the layout, partition keys and watermark on the picture). `diagrams_src/agent.py` → `assets/agent.png` (flow + the *what*/*why* fork + four numbered guardrails + Bronze/Silver drawn **outside** the IAM grant). Render: `.venv/bin/python diagrams_src/<file>.py`.
4. ~~**Gold model and semantic layer together**~~ — **done.** Two fact tables, full metric list, view shape.
5. ~~**BigQuery deliverables** (Part 1 Q2)~~ — **done.** Bronze DDL in `incoming-data.md`, dedup `QUALIFY` + full `MERGE` in `silver.md`, typed schema in `silver.md`.
6. ~~**Part 2 remainder**~~ — **done.** Agent flow, dictionary handling (Dataform descriptions → `INFORMATION_SCHEMA` → prompt), guardrails, FinOps.
7. **Write-up** — `part1-pipeline.md`, `part2-llm-agent.md`. The only thing the reviewer sees. Rules, settled:
   - **`docs/` is private material, not a deliverable.** The write-up is **self-contained** — no links into `docs/`, every load-bearing argument written out. A linked argument is an absent one.
   - **Ordered by the test's bullets, not by our dependency order.** The grader checks boxes in their sequence; matching it is free.
   - Per bullet: the answer flat, the argument compressed (requirement satisfied + alternative beaten), the artifact where one exists (diagram, DDL, SQL, metric table), and the rejected options as a one-line table.
   - **Port the rejection tables first.** Highest density in the repo — every named component with the reason it lost, one line each.
   - **Incident narratives: one per major section, blockquoted, ~5-6 total.** Chosen where the mechanism is otherwise abstract (3-day window, durable buffer, two denominators, `check_quality`, `rpm`). The remaining ~14 stay in `incident-narratives.md` as spoken ammunition.
   - **The spine, stated explicitly rather than left to be noticed:** six components lost to the same argument — *a runtime we operate, placed between us and something we could call directly* (Dataflow, Composer, dbt Core, Cube, LangChain, a vector DB).
