# DEPENDENCIES

Built from the **ASSUMES** and **DECISIONS** ledgers in the 18 per-page reviews, cross-checked against `SYNTHESIS.md`.

Purpose: after editing a page, know which other pages just became wrong. Each section lists what a page *supplies* to the rest of the document and which page consumes which claim. Backlog IDs in brackets are the edits that would change the claim.

Two structural facts worth holding:

- **`intro/02-business-assumptions.md` is the root.** Eleven pages spend its numbers. It is also client-given and not to be re-litigated — which means the safe edits there are labels (R-04), a reinstate clause (R-05), and rows for numbers already used downstream (M-05, A-01, A-02).
- **`part_1/04-medallion-model.md` is the hinge between the parts.** Every Part 2 page depends on it and it depends on nothing in Part 2. Edit it last in Part 1 and re-check all six Part 2 pages after.

---

## `introduction.md`

**Supplies:** nothing load-bearing. Two routing claims, both verified accurate.

**Depends on:** `intro/01` and `intro/02` containing what its bullets say [R-01 adds a thesis naming kept and deleted components — must match M-01's roster]; `intro/02`'s Source column [M-07 renames "allowed to assume" to "confirmed / assumed", which asserts the label taxonomy R-04 is currently fixing — **land R-04 before M-07**].

**Depended on by:** nothing.

---

## `intro/01-methodology.md`

**Supplies:**

| Claim | Consumed by |
|---|---|
| *"A runtime we operate, placed between us and something we could call directly"* — the rejection rule | `part1-pipeline` · `part_1/02` (Dataflow, Composer, dbt Core) · `part2-llm-agent` · `part_2/02` (LangChain, Agent Runtime, ADK) · `part_2/03` (Cube) · `part_2/04` (vector DB) |
| The component roster and its count | the same five pages, all currently disagreeing — four different numbers [M-01, R-02] |
| *"The table gives the reason it lost **and** the condition that brings it back"* | `part_1/02` (2 of 8 rows deliver it) · `part_2/04` (1 row, unfireable) · `part_2/02` (0 rows) [R-03, R-13, R-32, A-03] |
| The cost-paragraph convention (no total anywhere) | every page's marked Cost paragraph; restated on `part1-pipeline` [MC-2, C-03] |
| Present tense, no reversals | all 18 pages |
| The boundary of the rule (*"a build step is not a runtime"*) — **currently stated on `part1-pipeline`, not here** | `part_1/02` (Dataform templating) · `part_1/06` (compile-time macro) [MC-5, R-02] |

**Depends on:** the brief's list of candidate components; `intro/02` holding the requirements; `part_1/02`, `part_2/02`, `part_2/03`, `part_2/04` delivering the rejections it promises.

**Re-check after editing:** R-02 changes the count on five pages at once. R-03 changes what `part_1/02`'s and `part_2/04`'s Rejected tables are promised to contain.

---

## `intro/02-business-assumptions.md`

**Supplies — the widest blast radius in the document:**

| Claim | Consumed by |
|---|---|
| 2B events/day, ~1.5 TB/day | `part1-pipeline` (23k/s) · `part_1/01` (23k/s, alert thresholds) · `part_1/02` (23k/s, 10.5 TB, the $140 vs $105/TiB comparison) · `part_1/03` (~10 GB dedup state) · `part_1/05` (~62 GB partitions, ~$6,100 vs ~$1,000, the $5,100 delta) · `part_1/06` (batch sizing) · `part_2/01` (the significance-test rejection) [R-04 re-marks provenance; A-01 makes every per-second figure a peak] |
| 1-hour auction lifecycle **and** 1-hour duplicate-arrival bound | `part_1/04` (`is_settled` at +2h) · `part_1/05` (25 vs 26 partitions, 4% vs 8%) · `part_1/06` (watermark, lookback, day-scoped dedup) · `part_1/03` (rejected streaming TTL) [M-02 touches two of these] |
| 7-day raw retention, Confirmed as a ceiling | `part_1/00` (the whole page) · `part_1/02` (GCS class arithmetic) · `part_1/03` (compliance boundary) · `part_1/05` (`partition_expiration_days`, LOGICAL billing) · `part_2/05` (Bronze rejected partly on expiry) [M-10 removes "legally transient" from `part1-pipeline`] |
| ~10 users, all seeing all publishers, no RLS | `part_2/05` (RLS as a rejected alternative) · `part_2/06` (*"ten known users"* is the **whole** prompt-injection defence) · `part_1/04` (no access-control reason for dimension tables) [R-05 attaches the reinstate condition; if accepted, both Part 2 pages inherit] |
| No free text in payloads | `part_1/00` (allowlist is sufficient) · `part_2/04` (no semantic search to do) · `part_2/06` (no injection surface) [R-32 makes this the vector DB's reinstate condition, raising its load] |
| Two Gold grains (hourly, daily) | `part_1/04` · `part_2/03` (two view families) |
| Schema divergence across sources | `part_1/06` (per-source `CASE`) · `part_1/02` (SSPs will not converge) |
| The rhythm line (*look at yesterday, act today*) | `part_1/03` (*"the only intraday consumer is our own team"* — the lambda rejection) |
| bid + no_bid = 75-80% of event count | `part_1/05` (mis-stated as `no_bid` alone, and load-bearing for cluster position 3) [M-02] |

**Used downstream but absent from this page — the gaps:** publisher count ~300 (first stated on `part_1/05`, spent on `part_1/01` and `part_2/04`) [M-05] · ad-unit cardinality (spent implicitly by `part_1/04`, `part_2/05`, `part_2/06`; stated nowhere) [A-02] · peak-to-average, growth rate, SSPs invited per auction, fill rate [A-01].

**Depends on:** the brief; the client conversation; `CONTEXT.md`. Forward-references `part_1/00`.

**Re-check after editing:** any change here re-checks eleven pages. R-04 in particular re-marks numbers that seven pages cite as Given.

---

## `part1-pipeline.md` (summary)

**Supplies:** the ten-sentence model and the routing table. Nothing beneath depends on it — it is a consumer, and this is why every error here is inherited rather than propagated.

**Depends on:** `intro/02` (volume) · `part_1/00` (Silver as source of truth) · `part_1/01` (six services, monitoring) · `part_1/02` (the roster, Dataform over Composer) · `part_1/03` (*"the hot path can fail but cannot be wrong"* — quoted verbatim, so R-06 changes both pages) · `part_1/04` (two fact tables, two denominators) · `part_1/05` (the $5,100 delta, Bronze DDL) · `part_1/06` (window function + `MERGE`) · `assets/architecture.png` for the cadences the prose omits [M-08 states them in prose, which is what makes D-01 optional].

**Re-check after editing:** M-08 (latency contract), M-10 ("legally transient"), M-20 (routing table) and C-05 all touch the same ten sentences. Do them in one pass.

---

## `part_1/00-retention-anonymisation.md`

**Supplies:**

| Claim | Consumed by |
|---|---|
| **Silver is the source of truth; Bronze is a landing and replay buffer** — the inversion | `part1-pipeline` · `part_1/03` · `part_1/04` (Silver typed wide, retained forever) · `part_1/05` · `part_2/05` |
| Anonymisation boundary = Silver's typed allowlist | `part_1/04` (no identifier columns in the ~26) · `part_2/05` (Silver is anonymous) · `part_1/03` (hot/cold line doubles as compliance boundary) [R-07 may narrow "anonymous" to "unlinkable by us" — if so, sweep all four] |
| Bronze expiry as a table property, not a job | `part_1/05` (`partition_expiration_days = 7`) · `part_1/03` |
| The day-16 residue arithmetic, `max_time_travel_hours = 48` | `part_1/05` (reused in the LOGICAL/PHYSICAL break-even) |
| *"Declared in Terraform"* — asserted in one cell, nowhere else in 18 pages | the design's whole compliance claim; §3.7's deployment-model gap [R-37 supplies the Part 2 half] |

**Depends on:** `intro/02` (the ceiling, no free text) · `part_1/02` (no parse at ingest) · `part_1/04` (Silver's ~26 columns carry no identifiers) · `part_1/01` (dead-letter topic, GCS archive) · `part_1/05` (LOGICAL billing).

**Re-check after editing:** R-07 is the highest-fanout edit in Part 1 — it sits under the claim that licenses indefinite Silver retention, which five pages assume.

---

## `part_1/01-architecture-diagram.md`

**Supplies:**

| Claim | Consumed by |
|---|---|
| Two export subscriptions from one topic; the GCS archive holds messages BigQuery declined | `part_1/03` (replay, trigger 4) · `part_1/02` (the second export fee) · `part_1/00` (the archive copy) [R-10 states the write format all three assume] |
| Dead-letter topic and depth monitor | `part_1/03` (the counterexample R-06 has to absorb) · `part_1/00` |
| Watermark-age monitor over `pipeline_state` | `part_1/02` (*"a skip emits no failure log, which is why the monitor exists"*) · `part_1/06` (`pipeline_state` is also the dedup watermark) [R-09] |
| Assertions gate Gold, never Silver | `part_1/04` · `part1-pipeline` |
| The `publisher_payout` null assertion | `part_1/04` (nullable-by-design) · `part_1/06` (FX null at merge time) [R-08 and R-21 must be decided together — one gates Gold, the other explains why the null exists] |
| Semantic views are the interface for BI and the Part 2 agent | `part_2/05` (the grant) · `part_2/03` (three consumers, one layer) [D-02 fixes the diagram edge that contradicts this] |
| Envelope split enforced at publish | `part_1/02` (the Dataflow rejection) · `part_1/03` · `part_1/05` (cluster keys) |
| `assets/architecture.png` | embedded on `part1-pipeline.md` **and** this page [D-01, D-02] |

**Depends on:** `part_1/00`, `part_1/02`, `part_1/04` (`quality_hour`, revenue-share join, 3-day window), `part_1/05` (Bronze DDL), `part_1/06` (`pipeline_state.last_success`), `intro/02` (1-hour bound), Part 2 3.1 (the agent reads views only).

---

## `part_1/02-component-justification.md`

**Supplies:**

| Claim | Consumed by |
|---|---|
| Dataflow rejected; the producer supplies the five-field split | `part_1/01` (hop 1) · `part_1/03` (the split is quiet work moved upstream) · `part_1/05` (cluster keys depend on the split existing) [R-12 names the third option and makes `part_1/05` explicitly load-bearing here] |
| Dataform over Composer, with its three product gaps | `part_1/01` (the skip that emits no failure log) · `part_1/06` (native incremental rejected) · `part_1/04` (implied runtime) [R-13] |
| GCS Standard, 7 days, the archive is the recovery path | `part_1/00` (~$210) · `part_1/03` (replay source) · `part_1/05` |
| Pub/Sub retention rejected — **conceded as cheaper, and it is not** | nothing downstream depends on it; the damage is local and on the page that just proved it checks unit economics [R-11] |
| 23k/s as a capacity figure | quoted on four pages [A-01 makes it a peak] |

**Depends on:** `intro/02` (volume, SSP divergence) · `part_1/00` (7-day ceiling) · `part_1/01` (topic schema, dead-letter, watermark monitor) · `part_1/04` (reference tables) · `part_1/05` (Bronze cluster keys — *never stated here, though it is the reason the split must precede Bronze*) · `part_1/06` (`CASE` mapping).

---

## `part_1/03-hot-cold-separation.md`

**Supplies:**

| Claim | Consumed by |
|---|---|
| *"Everything before Bronze can fail, nothing before it can be wrong"* | `part1-pipeline` quotes it as the design's summary [R-06 changes both] |
| Four repair triggers, one code path | `part_1/06` (the watermark that trigger 4 needs) [M-04] · `part_1/04` (the 3-day window) · `part_1/01` (the out-of-window alert) |
| Replay via BigLake `INSERT … SELECT` into Bronze | `part_1/02` (why no Dataflow for replay) · `part_1/01` (diagram node) · depends on R-10's write format |
| Lambda and continuous-maintenance rejections | nothing downstream; self-contained |

**Depends on:** `intro/02` (the rhythm line, the bounds) · `part_1/00` · `part_1/01` (the archive holds declined messages) · `part_1/04` (3-day window, revenue-share versioning) · `part_1/05` (Bronze partitioning) · `part_1/06` (settable watermark — the dependency M-04 makes visible).

**Note:** M-13 (move the table above the reframe) is a repo-rule fix — *lead with their construct, then extend it* — and changes no claim.

---

## `part_1/04-medallion-model.md` — the hinge

**Supplies (six Part 2 pages consume this page):**

| Claim | Consumed by |
|---|---|
| Silver ~26 typed columns, everything payload-derived nullable | `part_1/00` (no identifiers) · `part_1/06` (`SAFE_CAST`, rejects boundary) · `part_2/05` (`country`, `bid_floor`, `deal_id`, `placement_position` typed wide and *not* in Gold — the §3.6 gap R-36 closes) |
| Silver's grain, stated as one row per `event_id` | `part_2/03` repeats it; `part_1/06` actually guarantees one row per (`event_id`, `auction_day`) [R-19 corrects all three] |
| Two Gold fact tables, two denominators | `part_2/03` (two view families) · `part_2/05` (why the grant is on views, not base tables) · `part_2/01` (the conformed rollup that makes per-SSP decomposition sum) |
| `gold_ssp`'s grain, including `ad_unit_id` | `part_2/05` (*"two to three orders below the event layers"*) · `part_2/06` (the 20 GiB ceiling is set against this) [A-02, R-35, R-39 all resolve to this one number] |
| Every stored measure is additive; ratios never stored | `part_2/03` (the page's central rule) · `part_2/01` (decomposition arithmetic) |
| `auctions_with_bid` computed in the Gold build | `part_2/03` (mis-framed there as a boundary of additivity) [M-09, R-15] |
| `is_settled`, `quality_hour`, `sources_reporting_impressions` | `part_2/01` (`check_quality` runs first) · `part_2/03` (the coverage gate) · `part_2/05` (quality published as a view) · `part2-llm-agent` [R-29 changes which metrics the gate covers] |
| `ref_fx_rate` / `ref_revenue_share` as external tables with no loader, no schedule | `part_1/06` (joined at merge time, within 30 min of the auction) · `part_1/01` (the null assertion that blocks Gold) — **the three compose into a blocked daily Gold build** [R-21] |
| Trailing 3-day rebuild window, change-detected on `job_update_timestamp` | `part_1/03` · `part_1/06` · `part_1/01` |
| No dimension tables; `publisher_id`/`ad_unit_id` are flat strings | `part_2/04` (`resolve_entity` reads live dimension values from views, and assumes those strings are the spoken names) |

**Depends on:** `intro/02` (bounds, two grains, ~10 users) · `part_1/00` (day-8 unlinkability) · `part_1/06` (`MERGE`, watermark, `CASE`) · `part_1/05` (on-demand $6.25/TiB) · Part 2 `2.1`'s additivity rule (forward reference, restated inline so the page stays self-contained).

**Re-check after editing:** R-14 (Silver's price) must agree with R-35's Silver row. R-19 (the grain) propagates to `part_2/03`. A-02's answer propagates to `part_2/05` and `part_2/06`.

---

## `part_1/05-bronze-partitioning.md`

**Supplies:**

| Claim | Consumed by |
|---|---|
| Bronze DDL: hourly partition on `publish_time`, `require_partition_filter = TRUE`, cluster `publisher_id, ssp_id, event_type` | `part_1/06` (pruning, the watermark read) · `part_1/01` · `part_1/03` · **`part_2/05` — which prices a Bronze scan this DDL makes fail** [R-35] |
| ~300 publishers — first appearance in the document, unsourced | `part_1/01` (*"all 300 publishers"*) · `part_2/04` (*"hundreds of publishers"*, load-bearing for entity resolution) [M-05 moves it to `intro/02`] |
| On-demand $6.25/TiB | `part_1/04` (~$450/month) · `part_2/05` (the price table) · `part_2/06` (the ceiling's cost) |
| LOGICAL vs PHYSICAL billing, and the ~450 TiB/month reservation threshold | `part_1/00` (billing mode asserted there, argued here) · `part_2/06` (on-demand is a precondition for custom quotas) |
| ~3.4:1 compression — unsourced, load-bearing for the storage-billing argument | local only |
| The asserted Silver PHYSICAL clause | a claim about another table, on a page about Bronze [C-11 drops it] |

**Depends on:** `intro/02` (volume, both 1-hour bounds) · `part_1/06` (Silver's 30-min watermark read is the "dominant query" the grain argument rests on) · `part_1/00` (7-day ceiling) · `part_1/01` (topic schema promotes the envelope) · `part_1/03` (GCS archive as the recovery path).

**Re-check after editing:** R-17 changes the cluster order argument, which `part_1/02`'s R-12 clause would then cite.

---

## `part_1/06-dedup-sql.md`

**Supplies:**

| Claim | Consumed by |
|---|---|
| `MERGE ON event_id`; watermark as a settable row in `pipeline_state` | `part_1/03` (trigger 4 needs the rewind) [M-04] · `part_1/01` (the watermark-age monitor reads the same table) · `part_1/05` (the watermark read is the dominant Bronze query) |
| Silver's real invariant: one row per (`event_id`, `auction_day`) | `part_1/04` and `part_2/03` both state one row per `event_id` [R-19] |
| Per-source `CASE` mapping compiled from a declarative Dataform block | `part_1/02` (the third option R-12 names) · `part_1/04` (paths differ per source) |
| `gross_revenue` computed once, at merge time, against `ref_fx_rate` | `part_1/04` (money in Silver) · `part_1/01` (the null assertion) [R-21] |
| The 2-minute watermark offset | nothing cites it, but `part_1/01`'s *"the backlog drains, Silver reads the rows it never saw"* depends on it holding [R-18] |
| `require_partition_filter = TRUE` on Silver | `part_1/05` (asserted there for Bronze, here for Silver) [R-20] |

**Depends on:** `intro/02` (both bounds, schema divergence) · `part_1/05` (Bronze DDL and its scan figures, which already assume this page's single-pass temp table) · `part_1/04` (Silver's columns, nullability, `auction_timestamp`, `quality_hour`) · `part_1/02` (Dataform is both runtime and compile step).

---

## `part2-llm-agent.md` (summary)

**Supplies:** nothing. Pure consumer — which is why M-19's hoists are safe and why every error on it is inherited.

**Depends on:** all six Part 2 pages, `intro/02` (~10 users), Part 1's Gold layer, and `assets/agent.png` for the four guardrail layers and three of the four tools the prose never names [D-03]. Its Cube misattribution comes from `intro/01`'s roster [M-01]. Its proposed price hoist depends on `part_2/05`'s table, which is wrong until R-35 lands — **do not hoist before R-35.**

---

## `part_2/01-question-classes.md`

**Supplies:**

| Claim | Consumed by |
|---|---|
| The catchability split and the four tools | `part_2/02` (hop 2 declares four) · `part_2/03` (`diagnose_change` reads views, no consumer exempted) · `part_2/04` (`resolve_entity`) · `part_2/05` (`check_quality` needs no second grant) · `part_2/06` (layers 1-2 apply to `run_query` only) · `part2-llm-agent` |
| Routing enforced by `mode = ANY` + `allowed_function_names` | `part_2/02` **spends the claim a second time** to beat the Conversational Analytics API — so a correction here reaches a build-vs-buy verdict, not just a sentence [R-22] |
| `diagnose_change` = quality gate + four single-dimension passes over two periods | `part_2/02` (latency) · `part_2/06` (the ceiling applies to the routine's model-chosen period) [R-24] |
| The honest limit (*"it localises a change; it does not explain it"*) | `part2-llm-agent` should carry it and does not [M-19] |
| The materiality floor and the worked example | local; the example is the one artifact readers arithmetic-check [M-03] |

**Depends on:** `part_2/03` (the views, and `rpm` — which this page does not use and R-23 says it should) · `part_1/04` (conformed rollup, `is_settled`, `quality_hour`) · `part_2/02` (the loop and `tool_config`) · `part_2/04` (entity resolution) · `part_2/05` and `part_2/06` (security, explicitly deferred) · `intro/02` (2B/day, ten analysts).

---

## `part_2/02-agent-flow.md`

**Supplies:**

| Claim | Consumed by |
|---|---|
| Stateless `POST`, no session store, loop bounded at two | `part_2/04` (*"the copilot asks which. One question costs a turn"*) · `part_2/06` (*"a model in a retry loop"*) — three contracts for the same interaction [R-25] |
| Hops 5-7 are where the guardrail seam sits | `part_2/06` (the four layers live in those hops) · `part_2/01` |
| Dictionary assembled at hop 2 from `INFORMATION_SCHEMA` at request time | `part_2/04` (the prompt block) [R-27] |
| No model ID pinned; model churn treated as an operational fact | nothing — which is the §3.4 gap [R-26] |
| The Conversational Analytics and Looker rejections | `part_2/01` (defers the CA argument here) · `part_2/03` (assumes *"Looker is already in the estate"*, which this page rejects) [M-17] |
| `assets/agent.png` | embedded on `part2-llm-agent.md` **and** this page [D-03] |

**Depends on:** `part_2/01` (four tools, `mode = ANY`, the catchability split) · `part_2/03` (views carry their own arithmetic) · `part_2/04` (dictionary and entity mechanisms) · `part_2/05` (the grant) · `part_2/06` (the layers and the `execute()` wrapper) · `part_1/04` (Gold, `is_settled`) · `part_1/05` (on-demand pricing).

---

## `part_2/03-semantic-layer.md`

**Supplies:**

| Claim | Consumed by |
|---|---|
| Four views over Gold; every ratio computed at read time; no ratio stored | `part_2/05` (the grant's object) · `part_2/06` (the allowlist and `DATE_COLS`) · `part_2/04` (descriptions declared on these views) · `part_2/01` (the metrics it decomposes) |
| Ratio expressions in one Dataform `includes` file shared by four views | `part_2/04`'s bolded no-drift guarantee collides with this structure [R-31] |
| No monthly rollup object exists | `part_2/06` — there is nothing for a twelve-month question to fall back to under the ceiling [R-39] |
| `rpm` published because eCPM and fill rate trade against each other | `part_2/01` should use it and does not [R-23] |
| The coverage gate (`render_rate` NULL below `impression_coverage < 1`) | `part_1/04` supplies the counters; `part_2/01` reads the verdict [R-29] |
| *"Looker is already in the estate"* | contradicts `part_2/02`'s Looker rejection and `part_1/01`'s undifferentiated BI node [M-17, D-02] |

**Depends on:** `part_1/04` (Gold's grain, measures, two denominators, `auctions_with_bid`, `is_settled`) · `part_1/06` (money in Silver, one currency) · `part_2/05` and `part_2/06` (grant and layers) · `part_2/01` (catchability, `diagnose_change`).

**Re-check after editing:** R-28 adds a rule to `part_2/06`'s validator — that page inherits a fifth static check. R-30 depends on R-28 being accepted first.

---

## `part_2/04-glossary-and-entities.md`

**Supplies:**

| Claim | Consumed by |
|---|---|
| Dictionary = Dataform column descriptions, injected whole | `part_2/02` (hop 2's cost and latency) · the brief's RAG box [A-05] |
| Entities resolved live by SQL fuzzy match, no index | `part_2/01` (`resolve_entity`) · `part_2/02` (the second RAG mechanism) |
| The vector DB's reinstate condition | `intro/01`'s reinstate promise — one of only three in ~50 rows, and the one that can never fire [R-03, R-32] |
| *"Hundreds of publishers"* used as a load-bearing cardinality figure | absent from `intro/02` [M-05] |
| The clarifying turn (*"One question costs a turn"*) | `part_2/02`'s stateless contract has no room for it [R-25] |

**Depends on:** `part_2/03` (four views, the stated-definition rule, the `includes` structure) · `part_2/05` (the grant forces the lookup to read a view) · `part_1/04` (no dimension tables; `publisher_id` holds spoken names) · `intro/02` (no free text) · `part_2/02` (hop 2 assembly).

---

## `part_2/05-query-layer.md`

**Supplies:**

| Claim | Consumed by |
|---|---|
| The grant: `jobUser` on the project + `dataViewer` on `semantic` only | `part_2/06` (layer 4, and *"even if every line of our code is wrong"*) · `part_2/02` · `part_2/04` (why entity lookup reads a view) · `part2-llm-agent` |
| The quality verdict published as a view in `semantic` | `part_2/01` (`check_quality` needs no second grant) |
| `gold_ssp` at ten million rows/day | `part_2/06` — this is the number the 20 GiB ceiling is checked against [A-02, R-39] |
| The three-layer price table | `part2-llm-agent`'s proposed hoist [M-19] — **blocked until R-35** |
| *"The largest cost control in Part 2 is not a guardrail, it is an IAM grant"* | `part_2/06`'s closing reframe rests on it |
| Who can write to `semantic` — **unstated** | the whole grant's integrity; §3.7 [R-37] |

**Depends on:** `part_1/04` (two fact tables, two denominators, out-of-grain columns) · `part_1/05` (Bronze DDL — *ignored by the price table, which is finding 1*) · `part_1/00` (Silver anonymous and never expires; Bronze holds the personal data, unmentioned here) [R-38] · `part_2/03` (ratios at read time) · `intro/02` (~10 users, no RLS).

---

## `part_2/06-guardrails.md`

**Supplies:**

| Claim | Consumed by |
|---|---|
| Four layers, fired in reverse of the bullet's order | `part_2/01` (defers security here) · `part_2/02` (hops 5-7) · `part_2/03` (the validator that R-28 would extend) |
| Layer 1's date-predicate check | `part_2/05`'s Silver "no ceiling" row is refuted by it [R-35, R-42] |
| `MAX_BYTES = 20 GiB` | contradicts `part_2/05`'s own sizing of `gold_ssp` [R-39] |
| On-demand pricing as a precondition for custom quotas | `part_1/05` (the ~450 TiB/month reservation threshold — the page does not say whether the ceiling survives that switch) |
| *"Ten known users"* as the entire prompt-injection defence | `intro/02`'s ~10 users, the one deleted requirement with no reinstate condition [R-05] |
| The rejection path — **unstated on this page and on `part_2/02`** | the analyst's common path once the ceiling fires [R-41] |

**Depends on:** `part_2/05` (the grant) · `part_2/03` (four views, no monthly rollup) · `part_2/01` (four tools, correctness assigned there) · `part_2/02` (the loop bound, which its *"model in a retry loop"* contradicts) · `part_1/05` (on-demand billing) · `intro/02` (no free text, ten users).

---

## Edit-order constraints

Derived from the above. Violating these creates work rather than saving it.

1. **R-04 before M-07** — the introduction's wording asserts the label taxonomy that R-04 is fixing.
2. **A-02 before R-35, R-39 and R-14** — three price and ceiling items all resolve to one cardinality number.
3. **R-35 before M-19** — do not hoist a price table into the summary while it contradicts Part 1.
4. **R-28 before R-30** — the Cube/dbt concession is only safe once the validator rule that closes it exists.
5. **R-33 before (or with) R-27** — a deploy-time dictionary is only safe if a build fails on a missing description.
6. **R-08 and R-21 together** — one decides whether a null gates Gold; the other decides why the null exists.
7. **R-19 then `part_1/04` and `part_2/03`** — the Silver grain correction propagates to two pages that quote it.
8. **R-02 and M-01 in one pass** — the roster and the count are the same five-page edit.
9. **R-07 last in Part 1** — if it narrows "anonymous" to "unlinkable by us", four pages need the word swept.
10. **All seven mutual cuts before any CUT item** — this is the only ordering constraint that prevents silent content loss.
