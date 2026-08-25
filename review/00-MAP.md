# 00 — MAP

Inventory of the write-up under review. Docsify site; `_sidebar.md` is the navigation, `index.html` the shell. Source brief: `local_docs/technical_test.pdf` (gitignored, carries the real company name — anonymised to **OptimusAds** everywhere in the repo).

**18 pages, ~21,600 words.** Three top-level pages are summary-and-routing only; the arguments live in the 15 numbered pages beneath them.

## Page inventory

| # | Path | Words | Purpose (one line) |
|---|---|---|---|
| 1 | `introduction.md` | 70 | Routing stub: two pages of framing before the answers |
| 2 | `intro/01-methodology.md` | 573 | How every decision was argued: requirements in, components out; why each section ends with a **Rejected** table |
| 3 | `intro/02-business-assumptions.md` | 520 | The requirement table everything rests on — volume, mix, freshness, 7-day retention, 10 users; marks each line Given/Derived/Confirmed |
| 4 | `part1-pipeline.md` | 764 | Part 1 summary: the design in ten sentences + routing table to the seven pages below |
| 5 | `part_1/00-retention-anonymisation.md` | 1,019 | Client rule, not a test bullet: 7-day raw ceiling makes **Silver** the source of truth; names every copy of the raw record and its expiry |
| 6 | `part_1/01-architecture-diagram.md` | 1,104 | **Bullet 1.1** — the diagram, then the path hop by hop (8 hops), two writes from one topic, what pages on failure |
| 7 | `part_1/02-component-justification.md` | 1,359 | **Bullet 1.2** — verdict table on the five components the test names; Dataflow and Composer rejected with reinstate conditions; GCS storage-class arithmetic |
| 8 | `part_1/03-hot-cold-separation.md` | 1,125 | **Bullet 1.3** — the line sits at Bronze because the hot path can fail but cannot be wrong; four replay triggers, one code path |
| 9 | `part_1/04-medallion-model.md` | 2,350 | **Bullet 2.1** — Bronze/Silver/Gold rules, grains, the ~26-column Silver schema, two Gold fact tables (two denominators) |
| 10 | `part_1/05-bronze-partitioning.md` | 1,285 | **Bullet 2.2** — Bronze DDL: hourly partition on `publish_time`, cluster on `publisher_id, ssp_id, event_type`, 7-day expiry, dataset options |
| 11 | `part_1/06-dedup-sql.md` | 2,284 | **Bullet 2.3** — the asked-for window function, then the `MERGE` that makes it correct across runs; per-source JSON path mapping |
| 12 | `part2-llm-agent.md` | 510 | Part 2 summary: the design in six sentences + routing table to the six pages below |
| 13 | `part_2/01-question-classes.md` | 1,493 | **Bullet 1.1** — catchability splits *what* (model writes SQL) from *why* (fixed decomposition); four tools |
| 14 | `part_2/02-agent-flow.md` | 1,542 | **Bullet 1.2** — nine-hop flow user → FastAPI/Cloud Run → Gemini → validator → dry run → BigQuery; own loop over LangChain |
| 15 | `part_2/03-semantic-layer.md` | 1,781 | **Bullet 2.1** — dedicated BigQuery views; Gold stores only additive measures, every ratio computed at read time |
| 16 | `part_2/04-glossary-and-entities.md` | 1,194 | **Bullet 2.2** — dictionary as Dataform column descriptions injected whole; entities resolved live; no vector DB |
| 17 | `part_2/05-query-layer.md` | 995 | **Bullet 3.1** — Gold, and not its base tables: the views only, via authorized datasets |
| 18 | `part_2/06-guardrails.md` | 1,654 | **Bullet 3.2** — four layers (static validation, dry run, `maximum_bytes_billed`, IAM), fired in the reverse of the bullet's order |

## Reading order

Linear. Every page ends with a `Next:` link and the chain is unbroken from `introduction.md` to `part_2/06-guardrails.md` (the last page has no `Next:`, correctly).

```
introduction → 01-methodology → 02-business-assumptions
  → part1-pipeline → 00-retention → 1.1 diagram → 1.2 components → 1.3 hot/cold
    → 2.1 medallion → 2.2 partitioning → 2.3 dedup
  → part2-llm-agent → 1.1 question-classes → 1.2 agent-flow
    → 2.1 semantic-layer → 2.2 glossary → 3.1 query-layer → 3.2 guardrails
```

Sidebar order matches the `Next:` chain exactly. Page numbering restarts per part and mirrors the test's own bullet numbering — with one insertion: `part_1/00-retention-anonymisation.md` is not a test bullet and sits ahead of bullet 1.1.

## Weight distribution

- Intro: 1,163 words (5%)
- Part 1: 10,290 words (48%) across 8 pages
- Part 2: 10,169 words (47%) across 7 pages
- Heaviest pages: `04-medallion-model` (2,350), `06-dedup-sql` (2,284), `03-semantic-layer` (1,781), `06-guardrails` (1,654)
- Lightest substantive page: `05-query-layer` (995)

## Artifacts

- `assets/architecture.png` — Part 1 pipeline diagram, embedded on `part1-pipeline.md` and `part_1/01-architecture-diagram.md`
- `assets/agent.png` — Part 2 copilot flow, embedded on `part2-llm-agent.md` and `part_2/02-agent-flow.md`
- Sources: `diagrams_src/architecture.py`, `diagrams_src/agent.py`
- Inline artifacts: Bronze DDL (2.2), dedup SQL + `MERGE` + `CASE` mapping (2.3), Silver column table (2.1), storage-class cost table (1.2), guardrail layer table (3.2)

## House conventions the pages follow

Recurring structure worth knowing when reviewing a single page in isolation:

- Each numbered page opens by quoting its **test bullet** in italics.
- Most sections close with a **Rejected** table: option, reason it lost, and the condition that reinstates it.
- **Cost** appears only in marked paragraphs, never in the prose; no TCO total anywhere.
- Incident narratives are blockquoted, capped at ~5–6 across the whole document.
- Present tense throughout — a superseded position is written as a rejected alternative, never as a reversal.
- One argument recurs across both parts: *"a runtime we operate, placed between us and something we could call directly"* — the sentence that removes Dataflow, Composer, dbt Core (Part 1) and Cube, LangChain, a vector database (Part 2).
