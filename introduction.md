# Introduction

A programmatic-advertising analytics platform — anonymised throughout as **OptimusAds** — takes \~2B bid-stream events/day, \~23,000/second, \~1.5 TB/day, from hundreds of publishers, and serves a 10-person Yield team. Part 1 designs the GCP pipeline from ingestion to BI; Part 2 puts an LLM copilot on top of it.

One client rule reshapes both halves: **raw data is kept 7 days.** The durable record is therefore the anonymised event layer, not the raw one, and the error budget moves from *we can always rebuild* to *we must be right inside 7 days, and know it*.

## The eight arguments this design rests on

Everything else on these pages is detail, cost, or a rejected alternative. These are the claims worth attacking.

### Part 1 — the pipeline

**1. No component sits between us and something we could call directly.** One sentence removes Dataflow, Composer and dbt Core here, and Cube, LangChain and a vector database in Part 2. One rule applied six times is a design; six separate verdicts would be taste. Argued in [1.2](/part_1/02-component-justification.md).

**2. The hot path can fail but cannot be wrong.** That is where the hot/cold line goes — at Bronze. Receive, check the envelope, buffer durably, land. Every judgement that could be wrong happens downstream, where being wrong costs a rerun instead of a redeploy. Argued in [1.3](/part_1/03-hot-cold-separation.md).

**3. The window function makes the `MERGE` legal; the `MERGE` makes the dedup correct across runs.** The test asks for dedup SQL, and `ROW_NUMBER` over `event_id` answers it. But re-reading the same Bronze rows is the normal case here — late data and reruns both replay the same window — and a query alone re-inserts duplicates the second time. Argued in [2.3](/part_1/06-dedup-sql.md).

**4. Two fact tables, not one, because there are two denominators.** `auctions` for sell-through; `bids + no_bids` for whether an SSP is worth keeping. One table keyed by SSP cannot hold the first: an auction opens before any SSP is involved. Argued in [2.1](/part_1/04-medallion-model.md).

**8. An allowlist fails closed where a stripping filter fails open.** Silver's typed schema *is* the anonymisation boundary — the mechanism is that the columns do not exist, not that a job removes them. A new identifier nobody noticed never arrives. Argued in [2.1](/part_1/04-medallion-model.md).

### Part 2 — the copilot

**5. The split is whether a wrong answer can be caught by the person receiving it.** The model writes SQL for *what* — a number, a ranking, a trend — and none for *why*. A cause is not in the result set; a model asked for one infers from how ad tech usually behaves and presents that as a finding. Argued in [1.1](/part_2/01-question-classes.md).

**6. The largest cost control in Part 2 is an IAM grant, not a guardrail.** Guardrails bound the bad case. The grant — `dataViewer` on the semantic dataset alone — bounds the normal one, which is the one that runs thousands of times. Argued in [3.1](/part_2/05-query-layer.md).

**7. Trustworthiness is a property of the pipeline, not of the prompt.** The copilot reads `is_settled` and the published quality verdict rather than judging its own input. The pipeline says whether an hour is complete; the model is never asked to guess. Argued in [1.1](/part_2/01-question-classes.md) and [2.1](/part_1/04-medallion-model.md).

## Before the bullets

- [**Methodology**](/intro/01-methodology.md) — why every section ends with a **Rejected** table
- [**Business assumptions**](/intro/02-business-assumptions.md) — requirements only, never mechanisms

Everything after these two pages follows the test's own bullets, in the test's order. Each page opens with its claim, then the argument, then the options it beat.

---

Next: [**Methodology**](/intro/01-methodology.md)
