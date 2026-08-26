# 2.1 — Metrics & Business Glossary

*Test bullet: AdTech concepts like eCPM, fill rate, gross margin, or Prebid revenue are based on precise calculation formulas. How do you implement a semantic layer (e.g., dbt Semantic Layer, Cube, or dedicated BigQuery views) to ensure the LLM applies the correct calculation rules instead of reinventing its own SQL aggregations?*

**Dedicated BigQuery views — the test's own third option.** Four of them: `v_opportunity_hourly`, `v_opportunity_daily`, `v_ssp_hourly`, `v_ssp_daily`. **Every ratio is computed at read time from summed measures and none is stored, so there is no metric column for a model to recompute or average.** dbt's Semantic Layer and Cube lose the same way: a service to operate, where a view is an object BigQuery already resolves.

---

## The failure it removes

Gold has one row per hour × publisher × ad unit × format × device × channel. Someone asks for publisher X's eCPM last month, and a model composing its own SQL plausibly writes:

```sql
SELECT AVG(ecpm) FROM gold_opportunity WHERE publisher_id = 'X'
```

Wrong, and nothing about the result looks wrong. It averages thousands of rows of wildly different sizes — a row with 10 impressions weighs exactly as much as one with 10 million. The correct form is `SUM(gross_revenue) / SUM(impressions) * 1000`.

The view never exposes `ecpm` as a stored column, so there is nothing to average. The model can select the metric, filter it, group by it. It cannot recompute it: the division stays in the view, not in the model's SQL.

`v_opportunity_*`:

| Metric | Definition |
|---|---|
| `ecpm` | `gross_revenue / impressions * 1000` |
| `gross_margin` | `(gross_revenue - publisher_payout) / gross_revenue` |
| `fill_rate` | `impressions / auctions` |
| `bid_rate` | `auctions_with_bid / auctions` |
| `clear_rate` | `wins / auctions_with_bid` |
| `render_rate` | `impressions / wins` — **`NULL` where `impression_coverage < 1`**, never a partial figure presented as whole |
| `rpm` | `gross_revenue / auctions * 1000` |

`v_ssp_*`, adding:

| Metric | Definition |
|---|---|
| `response_rate` | `bids / (bids + no_bids)` — how often it prices the opportunity at all |
| `win_rate` | `wins / (bids + no_bids)` — how often being invited turns into a win |
| `ecpm`, `gross_margin` | as above, over the impressions this SSP won |

> **Someone raises floor prices and reports eCPM up 12%.** True, and meaningless: fill rate fell by more, and revenue per opportunity went down. An optimization judged on eCPM alone is judged on a number the change itself manufactured. `rpm` — revenue per opportunity — is in the view for that reason.

**Cost.** A logical view stores nothing and costs nothing to maintain; what a question pays for is the scan of Gold underneath it, two to three orders of magnitude below the event layers and priced per layer in 3.1. The alternative that costs money is recomputing metrics from the event grain, not a different semantic layer.

## Rejected — one line each

| Option | Why not |
|---|---|
| **dbt Semantic Layer** | MetricFlow's definitions are open source; the *served* layer downstream tools query is paid dbt Cloud — $100 per user per month at Starter, metering ~$0.075 per queried metric, on a copilot whose entire job is querying metrics. Part 1 already removed the dbt runtime |
| **Cube** | Core is Apache 2.0, Cloud operates it — either way a service to run, with its own API, cache and **access-control layer**. That last one is the cost: access control moves out of IAM, and the guardrail in section 3 is *"the service account holds `SELECT` on one dataset"* |
| **BigQuery Graph measures** (preview) | A native semantic object does now exist — measures declared in a node or edge table's `PROPERTIES`, read back through `GRAPH_EXPAND` and `AGG`. **A measure exists to aggregate correctly across a join that duplicates rows, and this schema has none**: two flat fact tables, no star schema |
| **Looker + LookML**, even already in place | Reaching LookML from the copilot means the Open SQL Interface — `SELECT` only, no `JOIN`, and the query runs on Looker's connection rather than as a job of ours. The semantic layer would be bought at the price of every guardrail in section 3, all of which are fields on a job we submit |
| **Storing ratios in Gold** | A stored `ecpm` is only correct at the grain it was computed at, and it is the exact column a model would average |
| **One wide view across both fact tables** | `win_rate` has two legitimate denominators; merging forces a rename or fans auctions out across SSPs |
| **A view with a grain parameter** | That is a table function: the BI tool cannot browse it, and a metric name becomes a call. Two views is more objects and less to explain |

---

Next: [**2.2 — Synonym & Metadata Management**](/part_2/04-glossary-and-entities.md)
