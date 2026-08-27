# 1.1 — Copilot Scope & Question Classes

*Test bullet: we want to deploy a copilot capable of answering business questions such as: "Why did the eCPM of publisher X drop by 20% yesterday on the video format?"*

**The split is whether the person receiving a wrong answer can catch it.** *What* — a number, a ranking, a trend — the model writes the SQL, because a wrong figure looks wrong to someone who sees it daily. *Why* — a cause, an attribution — runs a decomposition we wrote, because nothing in a result set tells a model the cause, and an invented cause reads exactly like a correct one.

---

| Tool | What it does |
|---|---|
| `run_query(sql)` | Model-generated SQL against the semantic-layer views only, behind a validator, a dry run and a byte ceiling |
| `diagnose_change(metric, filters, grain, period, comparison)` | A fixed, pre-written decomposition: check both periods are settled, split the change into rate and mix effect one dimension at a time, attribute it |
| `resolve_entity(name)` | Fuzzy lookup of a spoken name ("site Y") against live dimension values, returning `publisher_id` / `ad_unit_id` |
| `check_quality(grain, period)` | The pipeline's published verdict on a period, read before any answer about it |

<details>
<summary><b>What each tool receives and returns</b> — one example apiece</summary>

The model authors the arguments in all four. It authors the SQL in exactly one.

### `resolve_entity`

```json
→ { "name": "resolve_entity", "args": { "name": "Nortline" } }

← { "candidates": [ { "publisher_id": "northline", "distance": 1 } ] }
```

Candidates, never a pick: two plausible matches come back as two, and the model asks.

### `check_quality`

```json
→ { "name": "check_quality", "args": { "grain": "day", "period": "2026-08-26" } }

← { "verdict": "settled", "hours_present": 24, "hours_unsettled": 0,
    "min_impression_coverage": 1.0, "late_share": 0.004 }
```

`verdict` is computed from those counts in our code. The model reads a verdict, it does not form one.

### `diagnose_change`

```json
→ { "name": "diagnose_change",
    "args": { "metric": "ecpm",
              "filters": { "publisher_id": "northline", "format": "video" },
              "grain": "day", "period": "2026-08-26", "comparison": "prior_period" } }

← { "quality":  { "current": "settled", "baseline": "settled" },
    "headline": { "baseline": 4.98, "current": 3.89, "change_pct": -22.0 },
    "best_dimension": "ssp_id",
    "split":    { "rate_effect": -1.050, "mix_effect": -0.048 },
    "segments": [ { "segment": "ssp_3", "r0": 6.40, "r1": 3.80,
                    "rate_effect": -1.014, "mix_effect": -0.128,
                    "contribution": -1.142 },
                  { "segment": "ssp_1", "contribution":  0.004 },
                  { "segment": "ssp_7", "contribution":  0.040 } ] }
```

The contributions sum to −1.098, which *is* the change. One segment exceeds 100% of it because the other two moved the other way — a ranking never sums to anything, so it cannot show that.

### `run_query`

```json
→ { "name": "run_query", "args": { "sql": "…" } }
```

The `sql` value, the only SQL in the system the model wrote:

```sql
SELECT day, SUM(gross_revenue) AS gross_revenue
FROM `optimusads-analytics.semantic.v_ssp_daily`
WHERE day BETWEEN '2026-08-25' AND '2026-08-26'
  AND publisher_id = 'northline' AND ssp_id = 'ssp_3'
GROUP BY day
```

```json
← { "rows": [ { "day": "2026-08-25", "gross_revenue": 26240.0 },
              { "day": "2026-08-26", "gross_revenue": 14820.0 } ],
    "bytes_scanned": 412000000 }
```

A rejection returns the same shape — `{ "error": "SELECT * is not allowed" }` — so the model corrects and retries rather than narrating around a failure it cannot see.

</details>

## Catchability, and the rule it produces

*Can the person receiving the answer catch it when it is wrong?* Catchability is a property of the question type, not the person. **What** goes to `run_query`, and the model writes the SQL. **Why** goes to `diagnose_change`, whose SQL we wrote.

## One generated query cannot answer the test's example

A text-to-SQL agent writes one query, gets one number, and narrates a cause — but nothing in the result set told it the cause. It infers from how ad tech usually behaves and presents that as a finding: the failure mode nobody catches, on the exact question the test asked.

## Nor does a routine library

Routines only answer questions someone anticipated. *"Which ad units on mobile lost fill rate after we dropped SSP X"* is a shape nobody scripted, and an ordinary Yield question. Every new shape becomes a ticket. And it answers around the named deliverable, a Text-to-SQL + RAG pattern. One routine, not a library.

## The routing objection — enforced by the API, not the prompt

**The routing is enforced by the API, not asked for in the prompt.** `tool_config.function_calling_config.mode = ANY` with `allowed_function_names` — the section Google's docs title *"Forced function calling"* — constrains the model to a named subset. A turn narrowed to `diagnose_change` cannot come back as free SQL.

It does not constrain argument values: schema adherence, not semantics. A wrong `metric` gives a visibly wrong headline.

## The test's example, end to end

```
diagnose_change("ecpm", {publisher_id: "X", format: "video"}, "day", "2026-08-22", "prior_period")
```

The model chose those arguments and writes none of the SQL that runs next.

**1 — Quality gate.** `check_quality` on both periods; if either is unsettled or incomplete the routine says so and stops. First, because it is the likeliest explanation of a sudden drop and the only one not in the data.

**2 — Structural factorisation, where the metric has one.** `fill_rate = bid_rate × clear_rate × render_rate` is an identity, so a fill-rate drop resolves to *nobody bid* / *bids did not clear* / *wins did not render* before any dimension is touched — three findings for three teams. `ecpm` has no factorisation and goes to step 3.

**3 — Rate effect against mix effect.** A ratio moves for two structurally different reasons — rate and mix. *"Desktop eCPM fell"* and *"traffic moved to mobile"* have different fixes, and a ranking by metric change cannot tell them apart. For `m = Σᵢ wᵢ·rᵢ`, with `wᵢ` segment *i*'s denominator share and `rᵢ` its rate:

```
m₁ - m₀  =  Σᵢ w₁ᵢ·(r₁ᵢ - r₀ᵢ)     ← rate effect
         +  Σᵢ r₀ᵢ·(w₁ᵢ - w₀ᵢ)     ← mix effect
```

<table>
<tr><td>

**Worked example — same drop, opposite cause.** Desktop 60% of traffic @ $10 eCPM, mobile 40% @ $5: blended eCPM $8.00.

| | Day 0 | Day 1, mix shift | Day 1, rate drop |
|---|---|---|---|
| Desktop | 60% @ $10 | 36% @ $10 | 60% @ $8 |
| Mobile | 40% @ $5 | 64% @ $5 | 40% @ $5 |
| Blended eCPM | $8.00 | **$6.80** | **$6.80** |

Same drop, two different causes: shares moved and no rate changed (mix), or shares held and desktop's own rate fell (rate). A ranking by "eCPM down $X" cannot tell these apart — only the split can.

</td></tr>
</table>

**Exact.** The contributions sum to the total change, so this is an attribution and not a ranking, with no residual to hand-wave. It runs one dimension at a time, never a cross product: `ssp_id`, `ad_unit_id`, `device`, `channel`, in `v_ssp_*` and `v_opportunity_*`. It reports the one whose top contributors explain the most of the change.

**4 — Materiality floor.** A segment with 200 impressions can show a 300% eCPM swing and top the ranking. Segments below 1% of the period's denominator are collapsed into `other`, not dropped — so the contributions still sum to the total.

The model receives a structured result: quality verdict, baseline used, headline, the factorisation, per-segment rate and mix. It writes the prose around those numbers, and none of the SQL that produced them.

## The honest limit

**This localises a change; it does not explain it.** *"SSP 3 on video accounts for 78% of the drop, all of it rate effect"* says where the money went, not why SSP 3 changed its bidding — which lives in that SSP's systems.

> *"Publisher X's eCPM dropped 20% yesterday — why?"* The routine calls `check_quality` before decomposing anything, and yesterday is flagged partial: three evening hours never arrived. There is no drop to explain. Had it skipped that step, the breakdown would have run happily and blamed whichever SSP is busiest in the evening — specific, fluent, entirely wrong.

**Cost.** One invocation is four independent single-dimension passes over the Gold-grain semantic views for two periods — never a cross product, so work grows with the number of dimensions, not their product. Each pass reads one publisher's slice of two partitions.

## Rejected — one line each

| Option | Why not |
|---|---|
| **Let the model choose the dimensions** | The one judgement not checkable from the output, on the class not checkable at all |
| **Recursive drill-down** | Unbounded runtime and cost, for slices the materiality floor discards anyway |
| **A significance test per segment** | 2B events/day makes almost everything significant; materiality is what matters |
| **A separate hourly routine** | Identical arithmetic at both grains — two copies, one drift |
| **Conversational Analytics API** | No documented mechanism forces a *why* to the fixed routine, and its own Known limitations list correlation and anomaly detection as unsupported |

---

Next: [**1.2 — User → Orchestrator → Model → BigQuery**](/part_2/02-agent-flow.md)
