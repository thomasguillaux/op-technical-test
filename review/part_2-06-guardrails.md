# Review — `part_2/06-guardrails.md`

## Summary

This page answers the test's guardrail bullet by reordering it — validation fires first, IAM last — inserting a fourth layer the bullet does not name, and then arguing that the terabyte scan the bullet fears was already unreachable before any of the four existed. The reframe is the right one and it lands, but the artifact that carries it contains one checkable number that contradicts the document's own sizing, and the page's boldest technical claim rests on BigQuery behaviour it admits it has not pinned down.

## Grade

- **Decision quality — A.** All three named guardrails are adopted and one is added, each rejection carries a distinct argument (an LLM reviewing an LLM is *"exactly as uncheckable as the query it reviews"*), the quota layer is tied back to Part 1's billing choice as a precondition rather than a coincidence, and the page names three things the layers do not cover instead of waiting to be asked.
- **Narrative — B.** The punchline — *"the guardrails are what make that failure loud; the grant is what makes it impossible"* — arrives at 40% depth and is then restated almost verbatim in a blockquote at 90%; the last page of the document ends on a rejected-options table with no closing line.
- **Operability instinct — B.** Every layer has an owner and a failure mode, the on-demand-vs-reservation blast-radius argument is genuinely operational thinking, but nothing says what an analyst sees when a layer fires, whether a rejection returns to the model, or what a rising rejection rate would tell anyone.
- **Technical plausibility — B.** Dry-run-is-free, `maximum_bytes_billed`-fails-without-charge and the quoted error string all check out, and `use_query_cache=False` on the dry run is a detail you only write if you have hit the cache-hit gap; but `referencedTables` is credited with a resolution the page cannot commit to, the loop over it fails open, and the byte guards are silent about compute.
- **Signal density — B.** ~1,650 words, of which ~50 lines are code that earns its place (`COUNT(*)` excluded from the star check, CTE names excluded from the allowlist check, `WHERE` searched at any depth) — offset by one full restatement of the scenario walk-through and a layer-1 paragraph that says what the table above and the code below both already say.
- **Overall — B.** The thinking is A-grade and the reframe is the strongest closing move available; a corrected ceiling and one resolved sentence about `referencedTables` move this to an A, and both live in the artifact a CTO reads.

## Top findings

**1. [BLOCKER] `MAX_BYTES = 20 GiB` is not *"orders of magnitude above any legitimate question"* — by this document's own sizing it is about one month of the SSP view.**
- **What:** 3.1 sizes `gold_ssp` at *"ten million"* rows/day; a metric query through `v_ssp_daily` touches roughly `day, ssp_id, bids, no_bids, wins, impressions, gross_revenue` — call it 50–60 bytes/row billed. That puts 20 GiB at ~30–40 days of that view, so *"impressions and eCPM by SSP for publisher X, last 12 months"* — a **trend**, which 1.1 lists as a first-class *what* question the model writes SQL for — is rejected by layer 2 or 3 with `312.0 GiB exceeds the ceiling`. There is no monthly rollup in 2.1 for it to fall back to; the daily view is a `GROUP BY` over the hourly one over the base table.
- **Why it matters to the evaluator:** The ceiling is the one number on the page a reader can check, the comment beside it makes a quantitative claim, and a reviewer who has just read 3.1's row *"ten million on `gold_ssp`"* does the arithmetic in the room — the guardrail that fires on the analyst's ordinary question rather than the model's hallucination is the specific failure mode CTOs have seen kill internal tools.
- **Fix:** Either raise it and price it — 200 GiB is $1.25 at on-demand $6.25/TiB and still four orders of magnitude below the bullet's terabyte scan — or keep 20 GiB and say what it costs ($0.12) and what it rejects, and add the one sentence the page is missing: the rejection message goes back to the model, which retries with a narrower period. Cheapest version: replace the comment with *"~a month of `v_ssp_daily`; longer periods must narrow the filter."*

**2. [QUESTION] *"A parser can be wrong about what a query names; the engine cannot"* is asserted one sentence after admitting the page does not know what the engine returns.**
- **What:** Line 18 hedges — *"depending on how the engine expands a view, that list names the view or the Gold table behind it"* — and then bolds the double-check. If `referencedTables` names only the view, layer 2's object check re-reads exactly the string layer 1 parsed and the *"checked twice"* is once. Two further seams: BigQuery documents `referencedTables` as not populated for queries referencing more than 50 tables, so `for t in dry.referenced_tables` **fails open** on an empty list; and the check accepts any object in the whole `gold` dataset, which is looser than the allowlist above it. Note also that the byte half of layer 2 uses the same `MAX_BYTES` constant as layer 3, so object resolution is the *only* thing layer 2 uniquely contributes — which is what makes the unresolved question load-bearing rather than academic.
- **Why it matters to the evaluator:** This is the page's most confident sentence and the justification for adding a layer the bullet did not ask for; a staff engineer who has read job statistics will ask what the author actually observed, and *"depending on"* is the answer of someone who did not run it.
- **Fix:** State the observed behaviour in one clause (*"on an authorized view the job statistics name the view; the Gold branch is there for the day view expansion changes"*), and make the loop fail closed — `if not dry.referenced_tables: raise Rejected(...)` — which is two words of code and converts a silent gap into a stated one.

**3. [QUESTION] Nothing in the four layers bounds compute, and the query that gets through all four is a byte-free one.**
- **What:** `SELECT s.day, COUNT(*) FROM semantic.v_ssp_daily s CROSS JOIN semantic.v_ssp_daily t WHERE s.day >= '2026-08-01' GROUP BY 1` — one `SELECT`, no star in a projection, both objects allowlisted, a date predicate present, and a dry-run estimate that counts only the input scan. It passes static validation, the dry run, the ceiling and IAM, and then joins hundreds of millions of rows to themselves. `FROM v_ssp_daily, UNNEST(GENERATE_ARRAY(1, 1000000000))` is the same attack at zero bytes scanned.
- **Why it matters to the evaluator:** The page invites the test — *"three independent layers, none of which requires the model to have behaved"* — and a defence-in-depth argument is only as strong as the author's willingness to name what still gets through; the answer here is actually favourable to the design and is being left on the table.
- **Fix:** One line in `QueryJobConfig` (`job_timeout_ms=120_000`) and one sentence: under on-demand the bill is bytes, so a compute blowup is a hung request and a timeout, not an invoice — which is the same argument the quota section already makes against a shared reservation.

**4. [QUESTION] The date check tests that a column *name* appears in some `WHERE`, not that the scanned table is pruned.**
- **What:** `WHERE day IS NOT NULL`, `WHERE day = day`, or a date predicate sitting in a correlated subquery over a different object all satisfy `any(c.name in DATE_COLS for w in tree.find_all(exp.Where) ...)` while pruning nothing. Symmetrically, a legitimate query that filters dates in a `JOIN ... ON` clause is rejected, because an `On` is not a `Where`. The comment shows the author reasoned carefully about *where* the predicate sits and not at all about *what* it says.
- **Why it matters to the evaluator:** The table sells layer 1 as stopping *"a missing date predicate"*, and the code is the artifact a reader checks that claim against; the gap is small but it is in the one place the page offers as evidence that validation is structural rather than cosmetic.
- **Fix:** Require a bounded comparison — the date column against a literal or a query parameter under `>=`/`>`/`BETWEEN`/`=` — and say plainly that layer 1 is a cheap shape filter while the dry run is the only honest byte check. That concession costs nothing and pre-empts the whole line of questioning.

**5. [POLISH] Quotas read as declined for twenty lines before the page adopts them, and the document ends on a table.**
- **What:** Line 5 says *"all three"*, but the layer table — the only thing a busy reader reliably reads — omits quotas under a line beginning *"deliberately not in this table"*, and the section that actually adopts them is two screens down. Separately, the last page of an 18-page write-up closes on the Rejected table plus a navigation link, so the document's final sentence is *"depends on someone reading it."* (Minor: *"`QueryUsagePerDay` caps the project, 200 TiB/day by default"* is the other checkable figure here — the long-standing documented position is that no daily query-usage limit exists until you create a custom quota, so either cite the default explicitly or drop the number and keep the mechanism.)
- **Why it matters to the evaluator:** A grader checking three named guardrails against a four-row table sees two of them, and the seconds before the correction lands are the expensive ones; and the last page carries the final impression of the whole document.
- **Fix:** Add a fifth row — *"Custom quota | a day of queries, not one | BigQuery, per user and per project"* — with the *bounds N, not one query* note in the cell, and close the page after the Rejected table with the two sentences the page already owns: the grant made the terabyte scan impossible, the four layers make every attempt at it loud and logged.

## Cuts

- **The closing blockquote, lines 106 (~85 words).** It walks the same statement through the same four layers in the same order as lines 28–30 and reaches the same conclusion, one screen after the *"three code layers turn a hallucination into a rejection with a reason we can log"* paragraph already made it. It is also not an incident narrative — no one is on call in it, nothing happens on a Friday — so it spends one of the document's ~5–6 blockquote slots on a restatement. Delete entirely; nothing is lost.
- **Line 16, the layer-1 paragraph (~35 words).** *"Parsed, not pattern-matched"* is the only content, and the Rejected table says it again under **Regex-only validation** while the code demonstrates it. Keep the bold header, fold the parse-not-regex clause into the table row, drop *"Four checks on the shape of a statement, all decidable before a client call"* — the four checks are enumerated in the table cell above and implemented twenty lines below.
- **The `execute()` docstring comment, lines 77–78 (~25 words).** *"Every job the orchestrator issues lands here — free SQL and the fixed routines alike, because a routine we wrote still takes a period the model chose"* is line 22's paragraph compressed, three screens after it. The code needs the fact; it does not need the argument twice. Cut to `# every job, fixed routines included`.
- **Rejected rows 3 and 4 (~30 words).** *Per-query human approval* and *a cost estimate shown to the user, no hard ceiling* are the same rejection — a human in the loop of a decision they are not equipped to make — with the second being the weaker case. Merge into one row and keep *"moves the decision to whoever is least equipped to judge it."*

## Interview questions this page invites

1. **"Write me a query that gets through all four layers."** — Not answered. The page runs the bullet's own `SELECT * FROM bronze_events` through the stack, which dies three times at layer 1, and never attempts a survivor; a self-cross-join or an `UNNEST(GENERATE_ARRAY(...))` passes every layer because all four guard bytes and none guards work (finding 3).
2. **"On a query against an authorized view, does `referencedTables` come back with the view or with `gold_ssp`? Which did you see?"** — Explicitly not answered; the page hedges across both branches, and in one of them its bolded *"checked twice"* is a single check (finding 2).
3. **"Twenty gigabytes. What does a twelve-month SSP trend scan, and what does the analyst see when it is refused?"** — Not answered. The ceiling's justification is a code comment, the scan is roughly an order of magnitude above it by 3.1's own numbers, and no rejection path back to the model or to the user exists anywhere in this page or in 1.2's nine hops (finding 1).

## Claims ledger

**DECISIONS**
- All three guardrails the bullet names are adopted; execution order is the reverse of the bullet's (validation → dry run → ceiling → IAM)
- A fourth layer added: the dry run — rationale: puts the engine, not the model, in charge of the byte estimate
- Query quotas kept but held out of the per-query layer table — rationale: they bound a day of queries, not one query
- Static validation by AST parse (`sqlglot`) — rejected: regex/pattern matching (comments, string literals, nested subqueries defeat it)
- Four shape checks: exactly one statement and it is a `SELECT`; no star projection at any depth; every object on the allowlist (CTE names excluded); a date column named in some `WHERE`
- Layers 1–2 apply to `run_query` only; `diagnose_change` and `resolve_entity` skip them — rationale: our own SQL, re-parsing it tests nothing a unit test does not
- Layer 3 (`maximum_bytes_billed`) applies to **every** job including the fixed routines — rationale: their scope is model-chosen (`period`, `filters`)
- Dry run issued with `use_query_cache=False`
- `referencedTables` validated against the allowlist **or** the whole `gold` dataset, to cover either view-expansion behaviour
- `MAX_BYTES` set at 20 GiB, asserted as orders of magnitude above any legitimate question
- On-demand pricing is a precondition for custom quotas — rejected: shared BigQuery Editions reservation (a heavy query takes slots from the pipeline and starves Silver's 30-minute cadence; blast radius becomes a freshness incident rather than a bill)
- Custom quotas classified as a spend bound, not an accounting control (Google documents them as approximate)
- Prompt injection declared to have no surface — rationale: no free text in the data, ten known users
- Narration declared unguarded; mitigation deferred to 1.2 (executed SQL + rows returned alongside the prose)
- Correctness declared out of scope for guardrails and assigned to 1.1's question-class split
- Rejected: an LLM reviewing the LLM's SQL; regex-only validation; per-query human approval; a cost estimate shown to the user with no hard ceiling

**TECH**
- BigQuery: dry run, `maximum_bytes_billed`, job statistics `referencedTables` / `total_bytes_processed`, `use_query_cache`, custom quotas `QueryUsagePerDay` and `QueryUsagePerUserPerDay`, authorized datasets (via 3.1), BigQuery Editions reservations (rejected)
- `sqlglot` with `read="bigquery"`: `exp.Select`, `exp.Star`, `exp.Column`, `exp.Table`, `exp.CTE`, `exp.Where`
- `google-cloud-bigquery`: `bigquery.Client`, `QueryJobConfig(dry_run=…, maximum_bytes_billed=…, query_parameters=…)`
- IAM (grant argued in 3.1)
- Objects named: project `optimusads-analytics`, datasets `semantic` and `gold`, table `bronze_events`, tools `run_query` / `diagnose_change` / `resolve_entity`

**TERMS**
- **Static validation** — parse-time checks on statement shape, before any BigQuery client call
- **Dry run** — bytes-to-be-scanned plus the engine's resolved object list, returned without executing
- **Ceiling** — `maximum_bytes_billed`, a per-job byte limit the model cannot raise
- **Guarded execution path** — the `validate` → dry run → `execute` sequence every orchestrator job passes through
- **Allowlist** — the fully-qualified objects a generated statement may name
- `DATE_COLS` — `{auction_hour, day}`, the partitioning column at either grain
- `Rejected` — the exception every layer raises
- **Proactive** (of quotas) — a query that would exceed the remaining allowance does not run
- **Spend bound vs accounting control** — the page's own classification of custom quotas
- **Blast radius** — what the layers bound, as opposed to truth
- **Narration** — the model's prose over a returned result set; explicitly unguarded

**NUMBERS**
- `MAX_BYTES` = 20 × 1024³ = **20 GiB** per job
- `QueryUsagePerDay` default given as **200 TiB/day** per project
- Illustrative overrun: **a hundred** queries each individually under the ceiling
- **Four** layers; **four** static checks; **three** independent code layers over **one** IAM layer
- Silver's **30-minute** cadence (from Part 1) as the thing a reservation would starve
- **Ten** employees as the whole untrusted-input surface
- Quoted BigQuery error: `Query exceeded limit for bytes billed: … or higher required.`
- Cost paragraph carries **no figure** — the only quantities are the ceiling and the quota

**ASSUMES (taken as given from elsewhere)**
- 3.1 — `roles/bigquery.dataViewer` on the semantic dataset alone, authorized over `gold`; no grant on Bronze, Silver or the Gold base tables; the layer choice, not this page, is what moves the monthly bill
- 2.1 — four semantic views over Gold, ratios computed at read time, no monthly rollup object
- 1.1 — the four tools, and that correctness of *what* answers rests on catchability rather than on guardrails
- 1.2 — hops 5–7 hold these layers; the executed SQL and rows return to the user; the loop runs at most twice (which is in tension with this page's *"a model in a retry loop"*)
- Part 1 — on-demand billing rather than a reservation (05-bronze-partitioning names ~450 TiB/month as the revisit threshold; the page does not say whether the ceiling survives that switch, only that quotas do not)
- Intro — *"pas de texte libre, que des données liées aux enchères"*; ~10 users
- Unstated but load-bearing: what `referencedTables` returns for an authorized view; what happens to a rejected query (user message, model retry, or neither); whether rejections are monitored
