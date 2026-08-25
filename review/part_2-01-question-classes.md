# Review — `part_2/01-question-classes.md`

## Summary

This page makes Part 2's boldest call: the model writes SQL for *what* questions and none at all for *why* questions, because an explanation cannot be sanity-checked by the person receiving it — and the test's own example is a *why*. The thesis is genuinely load-bearing rather than a scope reduction dressed up, and the page pre-empts the obvious "so your copilot can't do what was asked" reading with an honest-limit section; it is let down by an arithmetic slip in the worked example that carries the whole analytical argument, and by one bolded mechanism claim that the cited API does not support as stated.

## Grade

- **Decision quality — A.** Catchability is a real axis, not a topic taxonomy; the two obvious alternatives (pure text-to-SQL, routine library) are killed with distinct arguments, the routing objection is raised by the author rather than left for the interviewer, and *"this localises a change; it does not explain it"* is the kind of stated limit that buys trust.
- **Narrative — A.** Thesis → why the naive answer fails on the test's own example → why the opposite extreme fails → the objection → the example end to end → the honest limit. A busy reader arrives somewhere, and the arrival is a concession, which is the strongest place to land.
- **Operability instinct — B.** Quality-gate-before-decomposition and the materiality floor are both instincts you cannot fake, but the flagship interaction has no stated latency and the cost paragraph is the only one in the document that carries no number.
- **Technical plausibility — B.** The rate/mix identity is exact and the decomposition is consistent with `gold_ssp`'s conformed rollup; but the worked example's two scenarios are not the same-sized drop the page says they are, and `mode = ANY` is credited with enforcing a routing decision it cannot make.
- **Signal density — A.** ~1,490 words for the page that sets up all of Part 2, and almost every paragraph turns; the catchability table and the three paragraphs under it are the only real overlap.
- **Overall — B.** The thinking is A-grade and the boldest call is correctly bold; two one-line corrections move this page to an A, and both are in artifacts a CTO checks in the room.

## Top findings

**1. [BLOCKER] The worked example's two scenarios are not the same-sized drop.**
- **What:** The table says mix shift → **$7.00** and rate drop → **$6.80** from a $8.00 baseline, and the prose immediately below calls them *"Same-sized drop, two different causes"* under a heading reading **"same drop, opposite cause."** They are −$1.00 and −$1.20.
- **Why it matters to the evaluator:** This nine-cell table is the page's only proof that rate and mix genuinely need separating, it is the single artifact on the page a reader will actually arithmetic-check, and a claim of "same" contradicted by the numbers beside it undercuts the analytical rigour the whole section is selling.
- **Fix:** Change the mix-shift column to Desktop 36% / Mobile 64% (`0.36×10 + 0.64×5 = $6.80`), so both scenarios land on $6.80 and the −$1.20 is genuinely identical. Or drop desktop to $8.33 in the rate column to make both $7.00.

**2. [BLOCKER] `mode = ANY` cannot enforce the routing decision the page credits it with.**
- **What:** The page concedes *"is this a what or a why?"* is a model judgement, then says **"the routing is enforced by the API, not asked for in the prompt"** and cites `mode = ANY` with `allowed_function_names`. That pair forces *some* function call and constrains the model to a named subset — but nothing on this page or in 1.2 says what narrows the subset, and 1.2's hop 2 sends all four `FunctionDeclaration`s. With four names allowed, the API permits `run_query` on a *why* question exactly as the prompt would.
- **Why it matters to the evaluator:** It is the page's most confident mechanism claim, and 1.2 spends it again to beat the Conversational Analytics API (*"our loop's `mode = ANY` with `allowed_function_names` (1.1) removes the choice"*) — so an interviewer who knows Gemini function calling dismantles a build-vs-buy verdict, not just a sentence.
- **Fix:** Name the narrowing step in one clause — e.g. a first turn classifies, and turn two re-invokes with `allowed_function_names=["diagnose_change"]` so the model cannot revise its own routing mid-answer — or downgrade the claim to what the API actually gives (a tool call rather than free text, plus schema adherence) and let *"misrouting degrades an answer; it does not falsify one"* carry the defence, which it already does well.

**3. [QUESTION] `diagnose_change("ecpm", …)` decomposes the one metric 2.1 says must never be read alone.**
- **What:** Step 2 states *"`ecpm` has no factorisation and goes to step 3"* — true of `gross_revenue / impressions`, but 2.1 defines `rpm = gross_revenue / auctions` and argues at length, with its own incident narrative, that eCPM and fill rate trade against each other and that `rpm` is *"the one number a floor adjustment cannot game."* `rpm = fill_rate × ecpm` is an identity over the stored measures. So a 20% eCPM drop with fill up more is revenue-positive, and this routine will confidently attribute 78% of it to SSP 3.
- **Why it matters to the evaluator:** The page's job is the test's example, the example is an eCPM drop, and the sibling page already published the reason that framing is a trap — a CTO reading both sees the copilot answering the question as asked rather than the question worth asking.
- **Fix:** Add one line to step 2: for `ecpm`, report the movement in `rpm` and `fill_rate` alongside the headline before decomposing, so *"eCPM −20%, rpm flat — floors were lowered, revenue per opportunity is unchanged"* is reachable. It costs one extra measure per pass and closes the whole category.

**4. [QUESTION] "Exact" is true; "the attribution" is not — the interaction term is silently assigned to rate.**
- **What:** `Σ w₁ᵢ(r₁ᵢ − r₀ᵢ) + Σ r₀ᵢ(w₁ᵢ − w₀ᵢ)` sums to `m₁ − m₀` exactly, but so does the mirror form using `w₀` and `r₁`, and the two split the cross term `Σ(Δwᵢ)(Δrᵢ)` differently. The page's choice puts all of it in the rate effect and then says *"this is an attribution and not a ranking, with no residual to hand-wave."* The worked example, where only one factor ever moves, cannot expose the difference; a real day where both move can.
- **Why it matters to the evaluator:** Exactness and uniqueness are different properties, and conflating them is the specific thing an analytically literate reviewer probes when a page shows a formula — especially when the routine's output is a percentage attributed to a named SSP that someone will act on.
- **Fix:** One clause naming the convention and why: current-period weights on the rate effect, base-period rates on the mix effect, interaction carried by rate because a mix shift the team did not cause should not absorb a rate move it did. (The neighbouring rejection *"2B events/day makes almost everything significant"* has the same shape of problem — 2B is platform-wide, and step 4 itself posits a 200-impression segment; stating that the materiality floor runs first, after which significance is moot, reconciles both in one sentence.)

**5. [QUESTION] The flagship interaction has no latency and the cost paragraph has no number.**
- **What:** One `diagnose_change` is four single-dimension passes over two periods; 1.2 prices a single BigQuery hop at 1–3 s and two model turns at ~1–2 s each. Nothing on either page says whether the passes are concurrent, so the honest read is 4–12 s of query plus narration for the copilot's headline use case. The cost paragraph describes the shape of the work — *"work grows with the number of dimensions, not their product"* — and gives no figure, unlike every other page (2.1's `$450/month`, 1.2's dbt Cloud `$100/user/month`).
- **Why it matters to the evaluator:** The house rule is that each page carries a marked cost paragraph; the one page where the design deliberately does *more* work than a single query is the page where the reader wants the number, and "conversational" tools die on the difference between 3 s and 12 s.
- **Fix:** Say the four passes are issued concurrently and give an end-to-end figure (~4–6 s), plus the per-invocation scan — one publisher's slice of two daily partitions of Gold is small enough that the figure is an argument in your favour.

## Cuts

- **Line 27, the italic *"Give the model freedom precisely where a wrong answer gets caught, and remove it precisely where it does not"* (~25 words).** The page's opening bold already says *"free-form SQL where a wrong answer gets caught, fixed SQL where it does not"*, and the table's **Handled by** column says it a third time. Third statement of a thesis that landed the first time. Nothing lost.
- **The catchability table, lines 18–21 (~65 words) or the two paragraphs at 23–25 — not both.** The table's *"Can the analyst catch a wrong answer?"* column and the paragraphs *"An explanation cannot be sanity-checked"* / *"the uncatchable answer is the one people act on"* carry the same content, and the paragraphs carry it better because they contain the €12,400-vs-SSP-3 contrast. Keep the prose, cut the table to a single line mapping *what → `run_query`* and *why → `diagnose_change`*.
- **The **Rejected** table, rows 4–8 (~55 words).** *Cross-product*, *recursive drill-down*, *rank by metric change* and *a separate hourly routine* are internal implementation choices of `diagnose_change` already argued in steps 3 and 4, not alternatives to the page's thesis, and the first two reject nearly the same thing. Compress to two rows — *"exhaustive or recursive slicing"* and *"ranking instead of decomposing"* — and keep the significance-test row, which is the only one that isn't already on the page above.
- **Line 37, the clause *"And it answers around the named deliverable, a Text-to-SQL + RAG pattern"* (~13 words).** A compliance argument sitting inside a capability argument; it weakens the paragraph by implying the routine library was rejected partly for looking off-brief. The preceding sentence — every new shape becomes a ticket — is the reason and is sufficient.

## Interview questions this page invites

1. **"What actually stops the model calling `run_query` on my why-question?"** — Half-answered. *"Misrouting degrades an answer; it does not falsify one"* is a good answer and is on the page; the `mode = ANY` sentence next to it claims a stronger one the mechanism does not deliver, so the page currently answers the question twice with the weaker answer buried under the wrong one (finding 2).
2. **"eCPM dropped 20% because we lowered floors and fill went up. Does your routine tell me that, or does it hand me an SSP?"** — Not answered. The page says eCPM has no factorisation and goes straight to dimensional decomposition; 2.1's `rpm` argument is the answer and is never reached from here (finding 3).
3. **"Both rate and mix moved. Who gets the interaction, and would the mirror decomposition name a different SSP?"** — Not answered. The page asserts exactness, which is correct, and lets the reader infer uniqueness, which is not (finding 4).

## Claims ledger

**DECISIONS**
- One agent, four tools, own code, reading Gold only — rejected: pure text-to-SQL (one query cannot support a causal claim), pure routine library (only anticipated shapes)
- Route by *catchability* — whether the recipient can catch a wrong answer — not by topic; asserted as a property of the question type, not the person
- Model writes SQL for *what* questions (`run_query`); writes none for *why* questions (`diagnose_change` is pre-written)
- Model chooses `diagnose_change`'s arguments (metric, filters, grain, period, comparison) but not its dimensions — rejected: let the model choose the dimensions
- One routine, not a library
- Routing enforced via `tool_config.function_calling_config.mode = ANY` + `allowed_function_names` rather than prompt instruction (narrowing step unspecified)
- Quality gate runs first, before any decomposition — rationale: likeliest cause of a sudden drop and the only one not in the data
- Structural factorisation before dimensional decomposition where the metric has one (`fill_rate`); `ecpm` declared to have none
- Rate/mix split with current-period weights on rate and base-period rates on mix (convention not named) — rejected: ranking segments by metric change
- One dimension at a time — rejected: cross-product of all dimensions, recursive drill-down
- Segments below 1% of the period's denominator collapsed into `other`, not dropped — rejected: a significance test per segment
- Same routine at both grains — rejected: a separate hourly routine
- Scope limit accepted and stated: localises a change, does not explain it
- Conversational Analytics API rejected here on forcing grounds, argued in 1.2

**TECH**
- BigQuery (Gold, semantic-layer views `v_ssp_*`, `v_opportunity_*`)
- Gemini function calling: `tool_config.function_calling_config.mode = ANY`, `allowed_function_names`, Google's *"Forced function calling"* docs section
- Google Conversational Analytics API (rejected, deferred to 1.2)

**TERMS**
- **Catchability** — whether the recipient of an answer can detect that it is wrong; property of the question type
- ***What*** question — a number, ranking or trend; catchable
- ***Why*** question — a cause or attribution; uncatchable
- `run_query(sql)` — model-generated SQL against semantic views, behind validator + dry run + byte ceiling
- `diagnose_change(metric, filters, grain, period, comparison)` — fixed pre-written decomposition
- `resolve_entity(name)` — fuzzy lookup of spoken name → `publisher_id` / `ad_unit_id`
- `check_quality(grain, period)` — the pipeline's published verdict on a period
- **Rate effect** — `Σ w₁ᵢ(r₁ᵢ − r₀ᵢ)`; **mix effect** — `Σ r₀ᵢ(w₁ᵢ − w₀ᵢ)`
- **Materiality floor** — 1% of the period's denominator; below it, collapse into `other`
- **Structural factorisation** — a metric identity (`fill_rate = bid_rate × clear_rate × render_rate`)
- **Settled / unsettled / partial** period — the quality verdict read before answering
- **Locus vs story** — *"a locus is checkable; a story is not"*
- **Blast radius** — used of the uncatchable answer class

**NUMBERS**
- Test example: eCPM down **20%**, publisher X, video, yesterday
- **4** tools; **4** decomposition dimensions (`ssp_id`, `ad_unit_id`, `device`, `channel`); **2** periods per invocation
- Text-to-SQL alternative would need **"four or five queries and a judgement"**
- Materiality floor: **1%** of the period's denominator
- Illustrative noise segment: **200 impressions**, **300%** eCPM swing
- Worked example: Desktop **60% @ $10**, Mobile **40% @ $5**, blended **$8.00**; mix shift → **$7.00**; rate drop (Desktop @ $8) → **$6.80** — labelled "same-sized drop" (−$1.00 vs −$1.20)
- Illustrative output: **78%** of the drop from SSP 3 on video, all rate effect
- Rejection of significance testing invokes **2B events/day**
- Incident: **three** evening hours never arrived
- Example date argument: **2026-08-22**
- Cost paragraph: no figure

**ASSUMES (taken as given from elsewhere)**
- 2.1 — the semantic views exist, expose `ecpm`, `fill_rate`, `bid_rate`, `clear_rate`, `render_rate`, and compute every ratio at read time (also `rpm`, which this page does not use)
- Part 1 — a published quality verdict per period (`is_settled`, `quality_hour`) readable by the copilot
- Part 1 — `gold_ssp` sums over `ssp_id` back to `gold_opportunity`'s measures, which is what makes the per-SSP eCPM decomposition sum correctly
- 1.2 — the agent loop, the `tool_config` assembly at hop 2, and the Conversational Analytics / Looker rejections
- 2.2 — entity resolution mechanism behind `resolve_entity`
- 3.1 / 3.2 — Gold-views-only access and the four guardrail layers; this page explicitly defers security to them
- Intro — 2B events/day; ten analysts, all seeing all publishers
- Unstated but load-bearing: which turn narrows `allowed_function_names`; whether the four passes run concurrently; that `format` is a filter here and never a decomposition dimension, though Gold carries it
