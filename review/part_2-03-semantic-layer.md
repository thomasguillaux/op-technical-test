# Review — `part_2/03-semantic-layer.md` (2.1 — Metrics & Business Glossary)

## Summary

The page answers the semantic-layer bullet by picking the test's third option — dedicated BigQuery views — and defends it with one rule: Gold stores only additive measures, every ratio is divided at read time, and no ratio is ever stored. The argument is unusually well-built and the rejected-alternatives table is the strongest in Part 2, but the page's headline claim — that the view "removes the opportunity to get the arithmetic wrong" — does not survive the first query a staff engineer would write against it.

## Grade

| Dimension | Grade | One line |
|---|---|---|
| Decision quality | **A** | Seven rejected options, each killed by a specific mechanism (Cube moves access control out of IAM; Graph measures exist for joins that duplicate rows and this schema has none), not by preference. |
| Narrative | **A** | Opens on a wrong query that looks right, derives one rule from it, and closes by showing the rule is what makes 1.1's freedom safe — it leads somewhere. |
| Operability instinct | **B** | `SAFE_DIVIDE`, coverage gating and "one `includes` file" show real instinct, but the residual failure mode — the model re-dividing over the view's rows — is never named, and the coverage gate is applied to one metric out of seven. |
| Technical plausibility | **B** | Precise and correct almost everywhere (the fill-rate factorisation genuinely is an identity), with one claim a staff engineer will disprove in ten seconds. |
| Signal density | **A** | Almost no padding; two sections overlap and one appeal-to-generality sentence adds nothing. |
| **Overall** | **B** | A-grade thinking with one false headline claim and one internal inconsistency — both one paragraph from being fixed, and fixing them makes this the best page in Part 2. |

All four test-named metrics are present with formulas: `ecpm`, `fill_rate`, `gross_margin` (as a ratio), and Prebid revenue argued as a channel filter rather than a metric. That last move — refusing to define the metric the test names, with a reason — is the right kind of answer and should be defended, not softened.

## Top findings

### 1. [BLOCKER] "There is nothing to average" is false — the view exposes `ecpm` per row at its own grain

- **What:** The page opens on `SELECT AVG(ecpm) FROM gold_opportunity` and claims the view fixes it because "the view never exposes `ecpm` as a stored column, so there is nothing to average" — but `v_opportunity_daily` has one row per day × publisher × ad_unit × format × device × channel, each carrying a computed `ecpm`, so `SELECT AVG(ecpm) FROM v_opportunity_daily WHERE publisher_id='X'` is the identical bug against the semantic layer, and 3.2's validator does not reject it.
- **Why it matters to the evaluator:** It is the page's thesis, stated twice in bold, and it is exactly the claim a skeptical reader tests first; getting caught on it makes the rest of a genuinely strong page read as unexamined. It also happens to be the one capability dbt Semantic Layer and Cube actually buy — they answer a metric request at the caller's grain, so the caller never writes the division — which means the rejected alternatives were beaten on cost while winning on the thing the page cares most about.
- **Fix:** Concede the residual in one sentence — the view fixes *definition* drift absolutely and *re-aggregation* only at its own grain — then close it with machinery already on the page: the ratio column names are a known list of ten, so 3.2's `sqlglot` pass rejects any `exp.AggFunc` over one of them, and 2.2's injected dictionary states the re-aggregation form (`SUM(gross_revenue)/SUM(impressions)*1000`) beside the definition. Optionally add a publisher × day roll-up view so the common question needs no re-aggregation at all.

### 2. [BLOCKER] The coverage gate protects `render_rate` and not `fill_rate`, which has the same numerator

- **What:** `render_rate` returns `NULL` below `impression_coverage < 1` — "never a partial figure presented as whole" — but `fill_rate = impressions / auctions` is published ungated with the same `impressions` numerator and a denominator counted at the wrapper, so a slice missing a source's impression beacon returns an understated fill rate presented as whole; the factorisation `fill = bid × clear × render` then resolves with a `NULL` third factor and a non-`NULL` product.
- **Why it matters to the evaluator:** The page makes the null-never-zero interlock a virtue, so applying it to one of two metrics with identical exposure reads as a rule stated rather than a rule swept.
- **Fix:** Gate every metric that mixes the impression stream with a non-impression denominator (`fill_rate`, `render_rate`), and state in one clause why `ecpm` and `gross_margin` need no gate — revenue lands only on impression rows (2.1), so their numerator and denominator drop together and the ratio stays honest over reporting sources. Say at which grain coverage is evaluated on a multi-hour query, because `SUM(reporting)/SUM(total)` over a month is below 1 almost always and would make `render_rate` permanently empty at the grain people ask at.

### 3. [QUESTION] dbt Semantic Layer and Cube are rejected on price and runtime footprint, never on capability

- **What:** The rejections are real arguments — dbt Cloud's served layer is paid and metered per queried metric, Cube moves access control out of IAM and collides with 3.2's whole guardrail story — but neither row names what those products do that four views do not: resolve a metric at an arbitrary requested grain without the caller composing a ratio.
- **Why it matters to the evaluator:** An interviewer who knows these products will read the omission as not knowing what they are for, and the omission is load-bearing because that capability is precisely finding 1.
- **Fix:** Add a clause to the two rows: "buys query-time aggregation at an arbitrary grain, which the views buy only at their own — closed by the validator rule above, at a fraction of the operational cost." That converts the weakest leg of the rejection into the strongest.

### 4. [QUESTION] `auctions_with_bid` is described as a boundary of additivity when it is a boundary of derivability

- **What:** The page says "any count requiring per-event evaluation is destroyed by the aggregation", but `auctions_with_bid` is fully additive — an auction belongs to exactly one hour and one dimension cell, so it sums correctly over both time and dimensions; what cannot be done is *derive* it from the other stored columns after aggregation.
- **Why it matters to the evaluator:** As written the page's centrepiece rule appears to have an exception, which is weaker than the truth: the rule is exact, and what varies is where the measure is computed.
- **Fix:** Reframe in one sentence — "stored measures must be additive; not every additive measure is derivable from the others, so distinct counts are computed in the Gold build and then roll up like any sum." The rejected row in Part 1's medallion page ("Deriving `auctions_with_bid` in the view") already says this correctly.

### 5. [POLISH] Net revenue is the one number the layer does not name

- **What:** `gross_margin` is exposed as a ratio and nothing exposes `gross_revenue - publisher_payout` as a named measure, even though it is perfectly additive and 2.2's flagship informal question — *"how much does site Y make **us**?"* — reads literally as exactly that figure in euros.
- **Why it matters to the evaluator:** The page's own cross-reference asks for a number the definitions table cannot serve by name, so the model composes it, which is the small version of the failure the layer exists to prevent.
- **Fix:** Add `net_revenue` as a passthrough additive measure and define `gross_margin` as `net_revenue / gross_revenue`; one row in the table.

## Cuts

1. **Lines 83–85, the 1.1 interlock's first paragraph (~55 words → ~25).** It restates 1.1's catchability argument before adding its own point. Keep only the new claim: "1.1's cross-check only works if the dashboard and the copilot compute eCPM the same way; different definitions give the analyst two numbers and no way to choose." Nothing is lost — the reader arrived here from 1.1.
2. **Line 79's second half, "Without it that definition is copy-pasted… different numbers in a meeting" (~35 words).** The drift argument is already made sharper at line 27 ("a metric definition existing in two files is precisely the drift this layer exists to prevent"). Delete; the `diagnose_change` paragraph that follows is the one carrying new weight.
3. **Line 17, "Averaging an average is the most common mistake in analytics and humans make it constantly" (~20 words).** A generality appended to a concrete demonstration that already landed. Delete the sentence, keep the clause about the model being unable to recompute — assuming finding 1 rewrites it.
4. **Line 44's `render_rate` note and the section at line 75 (~15 words of overlap).** The table row states the `NULL` rule and the section restates it with the mechanism. Let the table row read `impressions / wins` plain and carry the rule once, where `SAFE_DIVIDE` and `impression_coverage` are explained.

## Interview questions this page invites

1. **"Write me the SQL for 'publisher X's eCPM last month' against `v_opportunity_daily`. What stops the model writing `AVG(ecpm)` over 720 rows?"** — Not answered; the page asserts the situation cannot arise, and 3.2's validator has no rule against it.
2. **"At what grain is `impression_coverage` evaluated on a month-long query, and why is `render_rate` the only metric it gates when `fill_rate` shares its numerator?"** — Not answered. The rule is stated once, applied once, and its roll-up semantics are unstated.
3. **"Cube and dbt SL resolve a metric at whatever grain the caller asks for without the caller writing a ratio. Did you reject that capability, or only its bill?"** — Partly answered: the Cube row's IAM argument is a genuine capability-level objection, but the aggregation capability itself is never named, so the answer currently reads as cost-only.

## Claims ledger

**DECISIONS**
- Semantic layer = 4 dedicated BigQuery views (`v_opportunity_hourly|daily`, `v_ssp_hourly|daily`) — rejected: dbt Semantic Layer, Cube, BigQuery Graph measures (preview), Looker + LookML
- No ratio stored in Gold; only additive measures stored — rejected: storing ratios in Gold
- Two view families, not one wide view — rejected: one wide view (`win_rate` has two legitimate denominators; merging forces a rename or fans auctions across SSPs)
- Separate hourly and daily views; daily = `GROUP BY` over hourly, same ratio expressions — rejected: a single view with a grain parameter (that is a table function; BI cannot browse it)
- Ratio expressions live in one Dataform `includes` file referenced by both grains
- `auctions_with_bid` computed in the Gold build, not in the view (stated as the boundary of the additive rule)
- Prebid revenue is not a metric: `gross_revenue` filtered to `channel = 'prebid'` — rejected: a dedicated column
- eCPM defined **gross**; net exposed as `gross_margin`, never as a second eCPM
- The copilot always states the definition it used in the answer text
- `rpm` published as a named metric because eCPM and fill rate trade against each other
- `bid_rate`, `clear_rate`, `render_rate` published as named metrics (fill-rate factorisation), not left to consumers to derive
- `render_rate` returns `NULL` where `impression_coverage < 1`
- All ratios use `SAFE_DIVIDE`; nulls propagate rather than becoming zero
- `diagnose_change` reads the views, not the base tables — no consumer exempted
- One layer, three consumers: model-generated SQL, `diagnose_change`, the BI tool

**TECH**
BigQuery (logical views, `SAFE_DIVIDE`); Dataform (`includes`); dbt Semantic Layer / MetricFlow / dbt Cloud; Cube (Core Apache 2.0, Cube Cloud); BigQuery Graph measures — `PROPERTIES`, `GRAPH_EXPAND`, `AGG` (preview); Looker + LookML + Open SQL Interface; IAM.

**TERMS**
Additive measure; the additivity test ("if adding two rows together does not produce a meaningful number, it does not belong in the table"); opportunity views vs demand-partner views; `ecpm`; `fill_rate`; `gross_margin`; `bid_rate`; `clear_rate`; `render_rate`; `rpm` (revenue per opportunity); `response_rate`; `win_rate`; `impression_coverage`; Prebid revenue (a channel slice, not a metric); gross vs net; opportunity set / denominator of the subject being measured.

**NUMBERS**
4 views; `ecpm` and `rpm` scaled ×1000; dbt Cloud Starter $100 per user per month; dbt SL metering ~$0.075 per queried metric; `impression_coverage < 1` as the gate; narrative figures — eCPM up 12%, publisher X eCPM €2.40; Gold scan "two to three orders of magnitude below the event layers"; view storage and maintenance cost = zero.

**ASSUMES** (taken as given from elsewhere)
- Gold's grain and measure list, and the two fact tables with two denominators (Part 1, 2.1)
- `auctions_with_bid`, `sources_total`, `sources_reporting_impressions` and `is_settled` are built in Gold (Part 1, 2.1)
- Null-never-zero and FX conversion in Silver, so all money is already in one reporting currency
- Revenue lands only on impression rows (Part 1, 2.1) — relied on implicitly, never stated here
- Dataform is the transform tool and dbt's runtime was removed in Part 1
- The single-dataset IAM grant and the four guardrail layers (3.1, 3.2), including the per-layer scan pricing
- 1.1's catchability rule and the existence of `diagnose_change`
- A BI tool exists and reads the same views; Looker is already in the estate
- `channel` is a dimension of every event, so `auctions` is attributable to a single channel
