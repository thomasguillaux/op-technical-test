# 3.1 — Gold, Through Its Views Only

*Test bullet: on which BigQuery layer (Bronze, Silver, or Gold) should the LLM agent execute its generated SQL queries? Why?*

**Gold.** It is the only layer where a question has an answer, a definition, and a published verdict on whether that answer is trustworthy.

**And not Gold's base tables — the views over them, in their own dataset.** The three-way choice the bullet offers is one level too coarse: `gold_opportunity` and `gold_ssp` are correct tables that a model still composes wrong queries against, for reasons that have nothing to do with which layer they sit in.

## The three layers

**Bronze** is a typed envelope around an opaque JSON payload, and no metric is defined anywhere in it, so every question requires the model to invent the JSON extraction *and* the arithmetic on top of it. It also expires at 7 days, so most questions have no answer there at all.

**Silver** is typed, deduplicated, anonymous and correct — and **the wrong answer for exactly the reason people expect it to be the right one.** It is one row per event with no metric definitions, which is precisely the surface an LLM composes wrong queries against. And nothing in Silver expires: Bronze's worst-case scan is capped by a 7-day window, Silver's is capped by nothing and is larger every day.

**Gold** is aggregated and dimensioned, built from additive measures, and it carries `is_settled` and source coverage as columns rather than leaving them to be inferred by the reader.

## Gold's base tables are still the wrong grant

**`gold_opportunity` and `gold_ssp` carry different denominators under the same metric names.** `gold_opportunity`'s denominator is every auction — *what share of our inventory sold*. `gold_ssp`'s is that SSP's own bids plus no-bids — *of the auctions SSP X was invited to, how often did it respond and how often did it win*. Both tables carry `impressions` and `wins`. A model handed both computes an SSP's fill rate against every auction, and the number it returns is arithmetically clean, about a different question than the one asked, and carries nothing in the result set saying which denominator produced it.

**And the ratios are deliberately not stored** (2.1), so a model on the base tables has to recompute every ratio it uses — which is the failure 2.1 exists to prevent, reintroduced by the choice of object rather than by the choice of layer.

So the grant is on the **semantic dataset**, which contains only views: **the only objects the service account can name are views, and every one of them defines its own arithmetic.**

## The mechanism: authorized datasets

**Querying a view normally requires `roles/bigquery.dataViewer` on the view *and on every table it reads*** — so granting the semantic dataset without granting Gold fails by default, and the obvious fix is to grant Gold as well, which undoes the entire point.

**BigQuery's authorized datasets close it.** The semantic dataset is authorized on the Gold dataset, so the views can read the base tables while the caller cannot. Per Google's documentation: *"to query a view in an authorized dataset, a user needs to have access to the view, but access to the shared dataset is not required."* One configuration covering the whole dataset, rather than authorizing each view individually and remembering to do it again for the next one.

**The grant in full, because it is checkable:** `roles/bigquery.jobUser` on the project — a query job needs `bigquery.jobs.create` wherever the data lives — and `roles/bigquery.dataViewer` on the semantic dataset alone. **No grant on Bronze, Silver or the Gold base tables exists anywhere for this service account.**

The pipeline's quality verdict is published as a view in the same dataset, so `check_quality` reads it under that single grant.

## The same question, priced at three layers

The bullet sits under security *and* cost. On-demand at $6.25/TiB:

| Executed against | What one publisher-slice question scans | Order |
|---|---|---|
| **The semantic views** | One publisher's slice of two daily Gold partitions — a few million rows/day on `gold_opportunity`, ten million on `gold_ssp` | **cents, or fractions of one** |
| **Bronze** | A read across the full 7-day window, ~10.5 TB logical | **~$60** |
| **Silver** | Nothing expires, so this figure has no ceiling — hundreds of TB at five years | **thousands, on a table larger every month** |

The gap between the rows is the argument, not any single figure in it.

**So the layer choice is the largest cost control in Part 2, and it is not a guardrail — it is an IAM grant.** A design that leaves the agent on Silver and defends the bill with query-time limits is paying attention to the query that goes wrong and none to the thousands that go right.

**Cost.** A logical view stores no bytes and adds none to a scan — it is expanded into the referencing query, so the reader pays for the partitions the base table would have charged for anyway.

## Rejected — one line each

| Option | Why not |
|---|---|
| **Silver, for flexibility** | The flexibility is the hazard: one row per event, no metric definitions, and nothing expiring to bound a scan |
| **Bronze** | Opaque JSON with no types and a 7-day life; most questions have no answer there, and every one that does requires the model to invent the extraction and the arithmetic |
| **Gold's base tables** | Two tables with different denominators under the same metric names, and no ratios defined — both failures the semantic layer exists to prevent |
| **A copied read-only dataset for the agent** | A second physical copy of Gold to solve an access problem that a view and an authorized dataset solve with no bytes |
| **Row-level security** | Around ten users, all of whom see every publisher, with no entitlement scoping |

---

Next: [**3.2 — Guardrails**](/part_2/06-guardrails.md)
