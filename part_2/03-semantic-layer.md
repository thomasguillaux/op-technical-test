# 2.1 — Metrics & Business Glossary

*Test bullet: AdTech concepts like eCPM, fill rate, gross margin, or Prebid revenue are based on precise calculation formulas. How do you implement a semantic layer (e.g., dbt Semantic Layer, Cube, or dedicated BigQuery views) to ensure the LLM applies the correct calculation rules instead of reinventing its own SQL aggregations?*

**Dedicated BigQuery views — the test's own third option.** Four of them: `v_opportunity_hourly`, `v_opportunity_daily`, `v_ssp_hourly`, `v_ssp_daily`. Every ratio is computed at read time from summed measures, and no ratio is ever stored. **The layer removes the opportunity to get the arithmetic wrong, not the temptation.**

## The failure it removes

Gold has one row per hour × publisher × ad unit × format × device × channel. Someone asks for publisher X's eCPM last month, and a model composing its own SQL plausibly writes:

```sql
SELECT AVG(ecpm) FROM gold_opportunity WHERE publisher_id = 'X'
```

Wrong, and it looks completely fine. It averages thousands of rows of wildly different sizes — a row with 10 impressions weighs exactly as much as one with 10 million. The correct form is `SUM(gross_revenue) / SUM(impressions) * 1000`.

The view never exposes `ecpm` as a stored column, so there is nothing to average. The model can select the metric, filter it, group by it. It cannot recompute it: the division stays in the view, not in the model's SQL.

## Gold stores only additive measures

`gross_revenue`, `publisher_payout`, `impressions`, `auctions`, `responses`, `wins`. Never `ecpm`, never `fill_rate`, never `gross_margin`. The test for it:

> **If adding two rows together does not produce a meaningful number, it does not belong in the table.**

Revenue adds. Impressions add. eCPM does not. Every ratio is computed by the view at the grain the question asked for. One definition of eCPM is therefore correct at every roll-up — one ad unit, one publisher, the whole business — with nobody re-deriving it per level.

**And additivity over dimensions and additivity over time are the same property**, so each daily view is a `GROUP BY` over its hourly one with the *same* ratio expressions applied to the coarser sums. Those expressions live in one Dataform `includes` file that both views reference: a metric definition existing in two files is precisely the drift this layer exists to prevent.

**The boundary:** `auctions_with_bid` is computed during the Gold build and not in the view, because it needs a per-event test — did this auction draw a bid? — that no combination of the stored sums reproduces. Everywhere else, make it additive and let the view divide.

## The definitions

All money is already in the single reporting currency, converted in Silver. The additive sums pass through both views unchanged — they are Gold's columns, not metrics. What follows is everything the layer actually *defines*.

`v_opportunity_*`, the inventory views. Identical definitions at both grains; only the `GROUP BY` differs.

| Metric | Definition |
|---|---|
| `ecpm` | `gross_revenue / impressions * 1000` |
| `gross_margin` | `(gross_revenue - publisher_payout) / gross_revenue` |
| `fill_rate` | `impressions / auctions` |
| `bid_rate` | `auctions_with_bid / auctions` |
| `clear_rate` | `wins / auctions_with_bid` |
| `render_rate` | `impressions / wins` — **`NULL` where `impression_coverage < 1`**, never a partial figure presented as whole |
| `rpm` | `gross_revenue / auctions * 1000` |

`v_ssp_*`, the demand-partner views. Together they answer *"is SSP X worth keeping"*, which is the only reason `gold_ssp` exists.

| Metric | Definition |
|---|---|
| `response_rate` | `bids / (bids + no_bids)` — how often it prices the opportunity at all |
| `win_rate` | `wins / (bids + no_bids)` — how often being invited turns into a win |
| `ecpm`, `gross_margin` | as above, over the impressions this SSP won |

Two views and not one, because `win_rate` has two legitimate denominators. The denominator is always the opportunity set of whoever is being measured: every auction when the subject is our inventory, that SSP's own bids plus no-bids when the subject is a partner. A single wide view has to pick one denominator for a name that honestly has two, and every consumer then has to remember which one it got.

Prebid revenue is not a metric. It is `gross_revenue` filtered to `channel = 'prebid'` — a slice of revenue by channel, not a separate kind of money. A dedicated column would create a second revenue definition to keep in sync with the first, for no gain: the filter is already a dimension.

Fill rate factors exactly. `fill_rate = bid_rate × clear_rate × render_rate` is an identity, and the three stages have three different owners and three different fixes.

| Stage falls | Cause | Fix |
|---|---|---|
| `bid_rate` | demand is not showing up for this inventory | SSP mix, invite list |
| `clear_rate` | bids arrive and do not clear | floor prices, direct-deal competition |
| `render_rate` | wins do not reach the page | page latency, ad blockers, broken creative |

A fill-rate drop is not actionable. *"Fill fell because render rate fell"* is. That is why the three factors are named metrics and not something a consumer is expected to derive.

`rpm` exists because eCPM and fill rate trade against each other. Raise floors and eCPM rises while fill falls. Both can be moved in the flattering direction at the other's expense, so neither alone says whether a change made money. `gross_revenue / auctions * 1000` is the product of the two, and it is the one number a floor adjustment cannot game.

> **Someone raises floor prices and reports eCPM up 12%.** True, and meaningless: fill rate fell by more, and revenue per opportunity went down. An optimization judged on eCPM alone is judged on a number the change itself manufactured. `rpm` is one line of SQL and it closes the entire category.

## A metric that cannot be computed refuses to render

Every ratio uses `SAFE_DIVIDE`, and that interlocks with the null-never-zero rule upstream. A source that cannot report impressions stores `NULL`, not `0`. `SAFE_DIVIDE` propagates it, so `render_rate` for that slice comes back empty rather than as a catastrophic-looking zero. `impression_coverage` — `sources_reporting_impressions / sources_total` — says why. Below 1, a slice describes fewer sources than it contains and is not comparable with one at 1. Had either half been done differently, the same gap would have produced a plausible zero and someone would have acted on it.

## One definition, three consumers

The copilot's free-form SQL, the `diagnose_change` routine and the BI tool all read the same views. Change what eCPM means and one view changes; all three move together. Without it that definition is copy-pasted into every dashboard and every query, drifting silently. The first symptom is two people quoting different numbers in a meeting.

`diagnose_change` reads the views and not the base tables, deliberately. It is our code and it knows the arithmetic. The routine is a consumer like any other: **the whole argument for a shared layer collapses if the component with the most authority is the one exempted from it.**

The copilot always states the definition it used: *"Publisher X's eCPM was €2.40 (gross revenue per thousand impressions)."* The rule follows from eCPM being gross: gross is the industry default and the publisher-facing number, while net is OptimusAds' own P&L and is exposed as `gross_margin` rather than as a second eCPM. One clause of the answer closes the failure this layer exists to prevent — two numbers under one name.

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
