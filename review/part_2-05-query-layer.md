# Review — `part_2/05-query-layer.md`

## Summary

This page answers the easiest bullet in the test — *which layer?* — and refuses the free answer, arguing that the three-way choice is one level too coarse and that the real grant is on a views-only dataset authorized over Gold. The refinement is genuine insight and the page is right-sized at 995 words; the cost table underneath it is the weak part, because it prices Bronze and Silver in a way Part 1's own DDL forbids.

## Grade

| Dimension | Grade | One line |
|---|---|---|
| Decision quality | **A** | The move from *"Gold"* to *"Gold's views, and never its base tables"* is argued from a concrete failure — two tables carrying `impressions` and `wins` under different denominators — and five alternatives are rejected on named grounds, including two (a copied read-only dataset, RLS) that most candidates would not think to raise. |
| Narrative | **A** | Answer, refinement, mechanism, price, thesis — and the thesis (*"the largest cost control in Part 2 is not a guardrail, it is an IAM grant"*) reframes the page that follows rather than summarising the one that ends. |
| Operability instinct | **B** | The grant is written out in full *because it is checkable*, and `check_quality` is deliberately pulled under the same single grant — but nothing says who can create views in the dataset that authorization blesses, and nothing says what happens to a question Gold's grain cannot answer. |
| Technical plausibility | **C** | The authorized-dataset mechanism is correct and correctly directed, but the price table contradicts Part 1: Bronze carries `require_partition_filter = TRUE` and clusters on `publisher_id`, so the ~10.5 TB / ~$60 scan is a query the design makes *fail*, and 2.2 already prices the publisher-filtered version at "cents". |
| Signal density | **B** | Almost no fat, but on the shortest page in the document three passages are duplicates: two Rejected rows restate two body paragraphs nearly verbatim, and the cost paragraph restates 2.1's. |
| **Overall** | **B** | One A-grade idea, undercut by the one table the closing thesis rests on; the repair is a repricing, not a rethink. |

## Top findings

**1. [BLOCKER] The three-layer price table prices queries Part 1's own DDL forbids, and its Bronze row contradicts 2.2 directly.**
- **What:** The column header promises *"what one publisher-slice question scans"*, then rows 2 and 3 silently switch to unfiltered worst cases — Bronze at "the full 7-day window, ~10.5 TB" when `bronze_events` sets `require_partition_filter = TRUE` (that query does not scan 10.5 TB, it errors) and clusters `publisher_id` first, which is why 2.2 prices the same publisher-filtered read at **"costs cents"**; Silver at "no ceiling" when it is partitioned on `auction_day`, clustered on `publisher_id`, and 3.2's layer-1 validator *rejects any query without a date predicate*.
- **Why it matters to the evaluator:** This is the table the page's strongest claim rests on — *"the layer choice is the largest cost control in Part 2"* — and a staff engineer who read Part 1 forty minutes earlier catches the contradiction in one glance, which converts the page's most memorable line into a number the author has already refuted himself.
- **Fix:** Reprice all three rows for the *same* question under each layer's actual DDL: Gold, fractions of a cent; Silver, one publisher's slice of *N* day-partitions of event-grain rows — still two to three orders up, and growing with history rather than bounded by it; Bronze, the question mostly has no answer at all, and the one it has costs a JSON extraction the model has to invent. The gap survives honest numbers; state it as "the same question, two to three orders apart, with only one of the three bounded by anything".

**2. [QUESTION] The page says the bullet sits under security, then argues security purely as scoping — never mentioning that Bronze is the only layer holding personal data.**
- **What:** Part 1's retention page establishes that Bronze is the sole layer carrying personal data and that Silver is the anonymisation boundary; this page rejects Bronze on JSON opacity, expiry and cost, and says nothing about pointing a narrating LLM at the one table with PII in it.
- **Why it matters to the evaluator:** It is a free point already paid for two parts earlier, and its absence makes the security half of the answer look like an access-control exercise rather than a data-sensitivity judgement — the reading a CTO applies to an LLM that pastes its output into Slack.
- **Fix:** One clause in the Bronze paragraph: Bronze is the only layer holding personal data, so an agent that narrates what it reads is a privacy decision before it is a cost one — and the grant, not a prompt rule, is what settles it.

**3. [QUESTION] Nothing says what happens when a question falls outside Gold's grain.**
- **What:** `country`, `bid_floor`, `deal_id` and `placement_position` are typed wide in Silver *deliberately* and are not in Gold's grain, so *"how did Germany do last week?"* has no answer in the semantic dataset — and the page's own opening claims Gold is "the only layer where a question has an answer".
- **Why it matters to the evaluator:** It is the first thing an interviewer probes on a page whose whole argument is a narrow grant: the pressure to widen the grant arrives the week a question misses, and a design that has not named its escape hatch tends to reach for IAM.
- **Fix:** Two sentences: an out-of-grain question is a Dataform change — a dimension added to Gold and surfaced in the view, shipped like any model change — and never a temporary grant, because the grant is the one control in this design that does not bend. Add "a question outside Gold's grain" as a named limit, the way 1.1 names its honest limit.

**4. [QUESTION] The authorized dataset blesses *every* view in `semantic`, present and future, so "every one of them defines its own arithmetic" is deployment discipline, not IAM.**
- **What:** The page's guarantee is that the only nameable objects are views that own their arithmetic, but the mechanism it cites grants read-through to whatever view exists in that dataset — `CREATE VIEW v_raw AS SELECT * FROM gold_opportunity` would hand the agent base-table grain with both denominators back in play, and the page never says who holds write access there.
- **Why it matters to the evaluator:** The page sells the grant as the layer that holds *"even if every line of our code is wrong"* (3.2's framing); a staff engineer will test whether it also holds against a careless pull request, and the answer is currently unwritten.
- **Fix:** One clause: the agent's service account holds `dataViewer` and therefore cannot create anything; `dataEditor` on `semantic` belongs to the Dataform deploy account alone, so a new view is a reviewed diff in the same repo as the metric definitions.

**5. [POLISH] The quoted documentation line supports the half of the claim that was never in doubt.**
- **What:** *"to query a view in an authorized dataset, a user needs to have access to the view, but access to the shared dataset is not required"* establishes that the caller needs no Gold access; the next sentence's load-bearing claim — one configuration covering views added later — is not what the quote says. (The mechanism itself is right: the access entry is configured on the *shared* Gold dataset, naming `semantic` with view target types, and newly created views in it are covered without re-authorizing.)
- **Why it matters to the evaluator:** The page quotes documentation precisely because it is checkable; a quote that proves the adjacent claim is the one detail a pedantic reader will pull on.
- **Fix:** Either quote the sentence that covers future views, or drop the quote and state the mechanism in your own words in one line — the argument does not need the citation.

## Cuts

1. **Rejected rows 1 and 2** (`Silver, for flexibility` / `Bronze`, ~60 words). Near-verbatim restatements of the body's own Bronze and Silver paragraphs, on the shortest page in the document. Keep the body versions — *"the wrong answer for exactly the reason people expect it to be the right one"* is the sharper sentence — and start the table at `Gold's base tables`. Nothing is lost but house-format symmetry.
2. **Line 15, the Gold paragraph** (~35 words → ~12). "Aggregated and dimensioned, built from additive measures, and it carries `is_settled` and source coverage as columns" is the medallion table and 2.1 restated; the page's argument starts in the section below it. Compress to one clause.
3. **Line 45** — "The gap between the rows is the argument, not any single figure in it." (~14 words). Defensive hedging that pre-excuses the figures; with finding 1 fixed, the figures need no excuse, and with it unfixed the sentence does not save them.
4. **Line 49, the Cost paragraph** (~40 words). 2.1's cost paragraph already says a logical view stores nothing and forward-references "priced per layer in 3.1"; this one says it back. One of the two should carry it, and the price table is here.
5. **Line 21, trailing clause** — "reintroduced by the choice of object rather than by the choice of layer" (~13 words). Restates the section heading two lines above it.

Total ~160 words, ~16% of the page — all of it duplication, none of it argument.

## Interview questions this page invites

1. **"Your Bronze table has `require_partition_filter` and clusters on `publisher_id`, and 2.2 prices that publisher-filtered read at cents. Where does $60 come from?"** — *Not answered; actively contradicted.* See finding 1.
2. **"Someone asks about Germany, or about bid floors. Gold has neither. What does the copilot say, and what stops the fix being a wider grant?"** — *Not answered anywhere in Part 2.* See finding 3.
3. **"Authorizing the dataset authorizes every view in it, including the one someone adds next quarter. Who can create objects in `semantic`, and what stops a passthrough view from becoming the agent's window onto base grain?"** — *Half answered:* the service account holds `dataViewer` only and so cannot create views, but the page never says who can. See finding 4.

## Claims ledger

**DECISIONS**
- Execution layer = **Gold**. Rejected: *Silver* ("the flexibility is the hazard" — event grain, no metric definitions, nothing expires); *Bronze* (opaque JSON, no types, 7-day life, model must invent extraction *and* arithmetic).
- Grant is on the **semantic views dataset**, not Gold's base tables. Rejected: *Gold base tables* — `gold_opportunity` and `gold_ssp` carry `impressions`/`wins` under different denominators, and no ratios are stored (2.1), so a model recomputes them.
- Access mechanism = **BigQuery authorized dataset**: `semantic` authorized on `gold`. Rejected: *granting Gold as well* (undoes the point); *authorizing each view individually* (must be repeated for every new view); *a copied read-only dataset for the agent* (a second physical copy of Gold for an access problem a view solves with no bytes).
- Grant in full = `roles/bigquery.jobUser` on the project + `roles/bigquery.dataViewer` on the semantic dataset **only**; no grant on Bronze, Silver or Gold base tables for this service account.
- The pipeline's **quality verdict is published as a view in the semantic dataset**, so `check_quality` needs no second grant.
- **No row-level security.** Rejected: ~10 users, all see every publisher, no entitlement scoping.
- Framing: **the layer choice is the largest cost control in Part 2, and it is an IAM grant, not a guardrail** — guardrails bound the query that goes wrong, the grant bounds the thousands that go right.

**TECH**
BigQuery (logical views, authorized datasets, on-demand pricing, dataset-scoped IAM); datasets `bronze` / `silver` / `gold` / `semantic`; tables `gold_opportunity`, `gold_ssp`; IAM `roles/bigquery.jobUser`, `roles/bigquery.dataViewer`, permission `bigquery.jobs.create`; BigQuery row-level security (rejected); Google Cloud documentation (quoted once).

**TERMS**
semantic dataset; shared dataset; authorized dataset; base tables vs views; *the grant*; denominator (per-table, under a shared metric name); publisher-slice question; logical view (stores no bytes, expanded into the referencing query); `is_settled`; source coverage.

**NUMBERS**
on-demand $6.25/TiB · Bronze full 7-day window ~10.5 TB logical ≈ ~$60 · Silver "hundreds of TB at five years" → thousands of dollars · Gold: a few million rows/day on `gold_opportunity`, ten million on `gold_ssp` · one question = one publisher's slice of **two** daily Gold partitions → cents or fractions of one · Bronze expiry 7 days · ~10 users.

**ASSUMES**
- Gold's two fact tables, their grains and their two denominators (Part 1 2.1).
- Ratios are never stored; the views compute them at read time (Part 2 2.1).
- Bronze is a typed envelope + opaque JSON with a 7-day partition expiry (Part 1 2.2 / 00) — but *not* its `require_partition_filter` or `publisher_id` clustering, which the price table ignores.
- Silver never expires and is typed, deduplicated and anonymous (Part 1 00 / 2.1).
- The quality table lives in Gold (Part 1 2.1) and `check_quality` is one of the four tools (Part 2 1.1).
- On-demand billing rather than a reservation (Part 1 2.2), which is what makes $/TiB the unit here.
- ~10 users with no entitlement scoping (`intro/02`).
- Something builds and deploys the views (Dataform, per 2.1/2.2) — never stated here, which is why finding 4 is open.
