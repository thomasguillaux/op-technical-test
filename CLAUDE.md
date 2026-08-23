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
- **Pair each defensive choice with a concrete incident narrative.** "3-day window" is forgettable; "a Friday-evening failure found Monday morning repairs itself before anyone logs in" is what makes a decision land. Add new ones to `incident-narratives.md`.
- Record decisions in `docs/` **with the argument that justifies them**, not just the conclusion. The conclusion alone is useless when challenged.

## Where things live

List the folder and read the relevant file before working in that area. Nothing here is imported — load on demand.

- **`docs/business_assumptions/`** — given by the client, not derived. **Do not re-litigate.**
- **`docs/design_decisions/`** — one file per decision, each carrying the argument that justifies it. All decided. `incident-narratives.md` in there is presentation material, not a decision.
- **`CONTEXT.md`** — domain vocabulary, business terms only, no architecture.
- **`diagrams_src/`** → **`assets/`** — render with `.venv/bin/python diagrams_src/<file>.py`.
- **`local_docs/`** — the test PDF. Gitignored, and stays that way: it carries the real company name.

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
