# SYNTHESIS — coherence pass across all 18 page reviews

Source: the 18 per-page reviews in `review/`, read against the extracted brief. The 18 reviewers ran independently and could not read the brief (no poppler on the machine); each reconstructed it from the italic *Test bullet:* line at the top of its page. That reconstruction was accurate per bullet and missed the framing — in particular the **Evaluation Grid**, the *"summary document (or presentation deck)"* format instruction, and the fact that the brief's only two quantities are *"several billion"* events/day and *"hundreds of media publishers"*.

Two grades the launching brief asked me to derive are in fact stated in their reviews: `part_1/02-component-justification` is **B** and `part_2/02-agent-flow` is **A**. Used as stated.

---

## 1. CONTRADICTIONS

Diffed across the 18 claims ledgers. Ordered by what an interviewer catches fastest.

### 1.1 The "one sentence killed six components" tally — four different numbers, one misattribution

The document's signature move, and the one claim checkable in ten seconds.

| Page | Says |
|---|---|
| `intro-01-methodology` | *"a single sentence that killed **six** components at once"* |
| `part1-pipeline` | *"Dataflow, Composer and dbt Core here; Cube, LangChain and a vector database in Part 2"* — six, split 3/3 |
| `part_1-02-component-justification` | *"Six components deleted by one sentence: three here, three in Part 2"* |
| `part_2-02-agent-flow` | attributes the sentence to **four** components |
| `part2-llm-agent` | *"removed Dataflow, Composer, dbt Core **and Cube** from Part 1"* — Cube misfiled, and adds *"agent runtime"* as a **seventh** |

Compounding it, the `intro-01` reviewer shows the rule does not actually hold for two of the six as argued on their own pages: Composer loses on *"right for a mixed DAG; this one has a single system in it"*, and the vector database loses on *"the corpus fits the context window / no free text"* — the runtime rule is cited there only for a hypothetical future.

**Owner: `intro/01-methodology.md`.** It states the rule; it should own the canonical roster and the count. Every other page cites the roster, names no count of its own, and `part2-llm-agent` moves Cube back to Part 2 where `part_2/03` actually rejects it.

### 1.2 `mode = ANY` — a mechanism claim that propagates into a build-vs-buy verdict

`part_2/01-question-classes` concedes *"is this a what or a why?"* is a model judgement, then states **"the routing is enforced by the API, not asked for in the prompt"**, citing `mode = ANY` + `allowed_function_names`.

`part_2/02-agent-flow` hop 2 sends **all four** `FunctionDeclaration`s. With four names allowed, the API permits `run_query` on a *why* question exactly as a prompt instruction would. Neither page names the step that narrows the subset.

Then `part_2/02` **spends the claim again** to beat the Conversational Analytics API: *"our loop's `mode = ANY` with `allowed_function_names` (1.1) removes the choice."* So an interviewer who knows Gemini function calling dismantles not one sentence but the document's build-vs-buy verdict — which `part_2/02`'s own reviewer calls *"the strongest thinking in Part 2"*.

**Owner: `part_2/01`.** Either name the narrowing turn (turn one classifies; turn two re-invokes with `allowed_function_names=["diagnose_change"]`) or downgrade to what the API gives and let *"misrouting degrades an answer; it does not falsify one"* carry the defence — it already does, well. `part_2/02` then inherits the corrected version.

### 1.3 Stateless vs. the clarifying turn

- `part_2-02-agent-flow`, hop 1: *"Stateless — no session store, no state to invalidate"*; hop 9 returns four fields, **none a conversation handle**.
- `part_2-04-glossary-and-entities`: `resolve_entity` returns ranked candidates and *"where more than one scores close, the copilot asks which. **One question costs a turn.**"*
- `part_2-06-guardrails` adds a third reading: it describes *"a model in a retry loop"*, which its own reviewer flags as in tension with `part_2/02`'s *"loop bounded at two"*.

Three pages, three different contracts for the most common real interaction. **Owner: `part_2/02`** — hop 1 is the flow contract; one sentence fixes it (the client echoes prior `contents`, or clarification resolves inside the same request).

### 1.4 Cost figures that contradict Part 1

`part_2-05-query-layer`'s three-layer price table, under a column header promising *"what one publisher-slice question scans"*:

- **Bronze:** *"the full 7-day window, ~10.5 TB"* ≈ $60. But `part_1/05` sets `require_partition_filter = TRUE` — that query **errors, it does not scan** — and clusters `publisher_id` first, which is why `part_1/05` prices the same publisher-filtered read at **"costs cents"**.
- **Silver:** *"no ceiling"*. But Silver is partitioned on `auction_day`, clustered on `publisher_id`, and `part_2/06`'s layer-1 validator **rejects any query without a date predicate**.

The table is what the page's memorable thesis rests on (*"the largest cost control in Part 2 is not a guardrail, it is an IAM grant"*), and the author has already refuted it himself two parts earlier.

Second cost contradiction, internal to Part 2: `part_2/06` sets `MAX_BYTES = 20 GiB` and comments that it is *"orders of magnitude above any legitimate question"*. `part_2/05` sizes `gold_ssp` at *"ten million"* rows/day. 20 GiB is roughly **one month** of the SSP view — so *"impressions and eCPM by SSP for publisher X, last 12 months"*, which `part_2/01` lists as a first-class *what* question, is refused by the guardrail. There is no monthly rollup in `part_2/03` to fall back to.

### 1.5 "Nothing of ours can fail" / "nothing before Bronze can be wrong"

- `part1-pipeline`, sentence two: *"no process of ours that can fail between the publisher and the dashboard."* Dataform sits between Bronze and the dashboard, is operated by us, and `part_1/02` says a run can be **skipped silently** — which is why the watermark-age monitor exists.
- `part_1/03-hot-cold-separation`, the page thesis: *"the only failure available before Bronze is not delivering."* `part_1/01` hop 4 documents dead-lettered writes with *"two causes, both silent"* — precisely a plausible-but-false state reported by nobody.
- `part1-pipeline` also says *"Bronze itself validates nothing"*, and `part_1/04` repeats *"Bronze accepts everything, validates nothing"*, while `part_1/01` and `part_1/02` both have the topic schema refusing malformed envelopes **synchronously at publish** and the `JSON` column dead-lettering invalid payloads.

Same claim, three pages, and the counterexample is in the document. **Owner: `part_1/03`** (it is the thesis); `part1-pipeline` inherits the qualified wording.

### 1.6 The reinstate condition — the promise and the delivery

`intro-01-methodology`: *"The table gives the reason it lost **and** the condition that brings it back — the condition is the load-bearing half."*

Across roughly fifty Rejected rows, a reinstate condition appears in **three**: Dataflow and Composer (`part_1/02`) and the vector database (`part_2/04`) — and `part_2/04`'s names a variable that can never fire (a few thousand tokens against a million-token window). `part_2/02`'s build-vs-buy table states **no** reinstate condition at all, which its reviewer flags as the one question the author would have to improvise. The methodology page rests its entire testability argument on a property three rows have.

### 1.7 Same term, two meanings

| Term | Reading A | Reading B |
|---|---|---|
| *hourly* | Bronze partition grain, on the **arrival** clock (`part_1/05`) | Gold row grain, on the **auction** clock (`part_1/04`); also the quality-check cadence — three senses within three sentences on `part1-pipeline` |
| *Silver's grain* | *"one row per `event_id`"* (`part_1/04`, `part_2/03`) | what the `MERGE` actually guarantees is **one row per (`event_id`, `auction_day`)** (`part_1/06`) |
| *anonymous* | `part_1/00`: `auction_id` is anonymous from day 8 — reasoning only about **our** re-linking key | the SSP holds the same `auction_id` beside its own identifiers; GDPR Recital 26 tests *by the controller **or by another person*** |
| *legally transient* | `part1-pipeline` calls the 7-day rule **legal** | `intro/02` marks it Confirmed with the client and never uses the word |
| *Given / Confirmed* | `intro/02` marks 2B/day, 1.5 TB/day, ~10 users **Given** | none of the three appears in the brief; four other lines are Confirmed and the taxonomy is never defined |
| *the quality table* | `part2-llm-agent` calls it a table | it is a view, `v_quality_hour` (`part_2/05`, diagram) |
| *`auctions_with_bid`* | `part_2/03`: a boundary of **additivity** | `part_1/04`: it is fully additive; what fails is **derivability** after aggregation. `part_1/04` is right. |
| *RAG* | brief: *"Text-to-SQL + RAG pattern"* | `part_2/02` redefines it as two mechanisms (whole injection + live lookup); `part_2/04` argues no retrieval index at all. Defensible, but the grader is box-checking. |

### 1.8 Numbers that disagree

- **`no_bid` share.** `intro/02`: `bid` + `no_bid` together are 75-80% of event count. `part_1/05` attributes the whole share to `no_bid` alone — and it is the load-bearing argument for `event_type`'s cluster position.
- **"The five events of one auction"** (`part_1/00`). Five is the count of event *types*; an auction produces 1 + N + 2 events where N is SSPs invited. `part_1/05` uses five correctly, as `event_type` cardinality.
- **25 vs 26 partitions** (`part_1/05`). The page's own two one-hour bounds compose to D+1 02:00 — 26 partitions and ~8% overhead, not 25 and 4%.
- **`is_settled` at +2h** (`part_1/04`) is justified with one hour of lifecycle; the missing second hour is the duplicate-arrival bound the page never names.
- **The 2-minute watermark offset** (`part_1/06`) has no stated source and no detector, on a page that holds itself to *"being wrong must be visible and rerunnable."*
- **`part_2/01`'s worked example**: mix shift −$1.00, rate drop −$1.20, captioned *"Same-sized drop"* under a heading reading *"same drop, opposite cause"*. It is the only artifact on the page a reader arithmetic-checks, and it carries the whole rate/mix argument.
- **Publisher count.** ~300 first appears on `part_1/05`, is used on `part_1/01` (*"all 300 publishers"*) and is load-bearing on `part_2/04` (*"hundreds of publishers"*) — and appears in **no row of `intro/02`'s assumption table**, despite being one of only two quantities the brief states.
- **Dictionary size.** `part_2/02` implies the block sits under 4,096 tokens (caching aside); `part_2/04` says *"a few thousand tokens on every request"*.
- **Two dated product claims to re-verify before defending live**: `part_2/04` gives Data Catalog's discontinuation as 2026-06-01 (its reviewer puts it at 2026-01-30); `part_2/06` gives `QueryUsagePerDay` a 200 TiB/day default (the documented position is that no daily query-usage limit exists until a custom quota is created).

### 1.9 Tech named once and never again

- **Terraform.** Asserted in one table cell of `part_1/00` (*"declared in Terraform"*) and nowhere in the other 17 pages. Retention correctness — the design's compliance claim — rests on it.
- **Cloud Run.** Named on `part2-llm-agent` and `part_2/02`; **argued on neither**, per both ledgers.
- **The GCS archive's write format.** `part_1/03`'s replay path returns rows with their original `publish_time`, which is Bronze's partition key — that only survives the round trip if the export subscription writes Avro or Parquet with message metadata. No page says so. `part_1/01`, `part_1/02` and `part_1/03` each assume another does.
- **The BI tool.** `part_2/03` assumes *"Looker is already in the estate"*; `part_2/02` rejects Looker; `part_1/01`'s diagram draws an undifferentiated BI/copilot node.

---

## 2. REDUNDANCY

Content carried on two or more pages, with the page that should own it and the estimated recoverable words. Cross-page duplication is roughly a third of the total; the rest is within-page restatement flagged independently by 18 reviewers.

| Content | Appears on | Should be owned by | Recoverable |
|---|---|---|---|
| *"A runtime we operate, placed between us and something we could call directly"* + the component roster | `intro/01`, `part1-pipeline`, `part_1/02`, `part2-llm-agent`, `part_2/02` | **`intro/01-methodology.md`** — it is the payoff of the three rules. `part_1/02` keeps one payoff clause because it is where the rule is *earned*; the others cite the roster and name no count. | ~120 |
| House-convention meta: *"each page stands alone and ends with the options it rejected"*, the cost-paragraph rule, the no-reversals rule | `intro/01` (~85w), `part1-pipeline` (2 sentences, ~36w), `part2-llm-agent` (~26w) | **`intro/01`**. A reader who has lived through seven pages of the convention does not need it restated. | ~110 |
| **Rejected tables that restate the prose immediately above them** — flagged independently on 8 pages: `part_1/03` (~35), `part_1/04` (~50), `part_1/05` (~130 incl. Editions row), `part_1/06` (8 rows, ~190), `part_2/01` (~55), `part_2/02` Looker (~90), `part_2/05` (~60), `part_2/06` (~30) | 8 pages | Each page's **prose**. The house rule says the table compresses arguments the prose did not make; running both is the convention working against itself. | **~640** |
| Retention / anonymisation logic | `part_1/00` (3× internally), `part_1/03` line 19, `part_1/04` summary rows | **`part_1/00`** | ~150 |
| The catchability argument | `part_2/01` (thesis + table + italic restatement), `part_2/02` hop 9, `part_2/03` lines 83-85, `part2-llm-agent` | **`part_2/01`** — everyone else arrives having read it | ~185 |
| Conversational Analytics + Looker rejections | `part_2/02` prose **and** `part_2/02` Rejected table | The **table row** (it adds the Open SQL Interface constraints the prose omits) | ~145 |
| The guardrail scenario walkthrough | `part_2/06` prose, then the closing blockquote, then the `execute()` docstring | **The prose.** The blockquote also burns one of the document's ~5-6 blockquote slots on a non-incident. | ~145 |
| The additivity identity (*a day is the exact sum of its 24 hours*) | `part_1/04` line 60, `part_2/03` | **`part_2/03`** — it defines the rule; `part_1/04` keeps one clause | ~30 |
| The view-stores-no-bytes cost paragraph | `part_2/03`, `part_2/05` | **`part_2/05`** — the price table lives there | ~40 |
| Six-service enumeration / Cloud Logging justification | `part1-pipeline` → `part_1/01` (~30), `part_1/01` → `part_1/02` (~18) | The **first** page to say it | ~48 |
| Co-location of synonym and definition (*"the same file"*) | `part_2/04`, 3× on one page | once | ~25 |
| `intro/02` discussing its own labelling scheme, and the rhythm line stated three ways | `intro/02` | one label glossary at the top | ~135 |
| The two-denominator claim (6 statements) and the 26-row Silver column table | `part_1/04` | prose + the exceptions only | ~165 |

**Total recoverable: ~2,700-3,000 words, roughly 13% of 21,600** — with **no argument removed**. Six reviewers used the same phrase independently: *"this is a dense page; there is no padding to find, only restatement."* That is the accurate diagnosis. The document's problem is not fluff, it is that arguments are stated once in prose and again in a table, and cross-part arguments are owned by two pages at once.

---

## 3. GAPS BETWEEN PAGES

Things every page assumes another explains, that no page does. These are worth more than any within-page finding, because each one is a question the whole document invites and nobody answers.

**3.1 Peak traffic. Nobody owns it — and it is a rubric line.**
`intro/02` gives a daily average (2B/day). `part_1/02`, `part_1/03`, `part_1/05` and `part_1/01` all spend `2B ÷ 86,400 ≈ 23k/s` as a **capacity** figure — sizing dedup state (~10 GB), alert thresholds, and the $5,100/month partition-grain delta. Ad traffic is diurnal. No page states a peak-to-average ratio, a growth rate, or headroom. The Evaluation Grid's first line reads *"understanding of scale constraints (billions of rows)"*; a grader reads 23k/s and asks for the peak. **Owner: `intro/02`.** One row, marked Assumed like the timing bounds, and a note that every per-second figure downstream is the peak.

**3.2 Cardinality. Two load-bearing numbers, neither in the assumptions table.**
Publisher count (~300) appears first on `part_1/05` and is used on `part_1/01` and `part_2/04`. **Ad-unit cardinality appears nowhere at all** — and `part_1/04` shows Gold's row count turns entirely on it, since `gold_ssp` is keyed on `ad_unit_id`. `part_2/05` then asserts a Gold scan is *"two to three orders of magnitude below the event layers"*, and `part_2/06` sets a byte ceiling against that assumption. **Part 2's entire cost story rests on a number the document never states.** The brief supplies half of it — *"hundreds of media publishers"* — which makes the omission stranger. **Owner: `intro/02`**; consequence lands on `part_1/04` and `part_2/05`.

**3.3 What the design costs in year three.**
Every page prices exactly the decision it argues (Bronze grain ~$5,100, storage class ~3×, GCS ~$210, Gold rebuild ~$450). The one line item that grows **without bound** — Silver, ~26 columns × 2B rows/day, retained forever, with columns deliberately added that no metric uses — is priced on no page. `part_1/04` prices the rebuild cadence instead. The only Silver storage figure in the document is `part_2/05`'s *"hundreds of TB at five years → thousands of dollars"*, which sits in Part 2, in the table §1.4 shows is wrong. The no-TCO rule is defensible; the absence of any figure for the only unbounded line is not. **Owner: `part_1/04`.**

**3.4 Model drift. A named rubric line with a zero.**
The brief: *"design a secure RAG/Text-to-SQL pipeline **without unnecessarily exposing the infrastructure to model drift**."* `part_2/02` deliberately pins **no model ID** and treats model churn as an operational fact. `part_2/06` concedes narration is unguarded and assigns correctness to `part_2/01`. `part_2/01` concedes it *"localises a change; it does not explain it"*. `part2-llm-agent` argues trust is structural — and structure does not degrade when a model changes, but narration does. **The word "drift" does not appear in the document**, and no page describes logging answers, a golden question set, or a regression run on model change. Three reviewers reached this independently from three different directions. **Owner: `part_2/02`** — it owns the model-selection decision.

**3.5 What the analyst sees when something fails.**
`part_2/06` names no rejection path. `part_2/02` hop 9 returns four fields, none of them an error. Whether a rejection returns to the model for a narrower retry is unstated on both, and `part_2/06`'s *"a model in a retry loop"* contradicts `part_2/02`'s bounded loop. With the 20 GiB ceiling firing on ordinary twelve-month questions (§1.4), this is not hypothetical: the failure UX is the common path. **Owner: `part_2/02`.**

**3.6 Questions outside Gold's grain.**
`part_1/04` types `country`, `bid_floor`, `deal_id` and `placement_position` wide into Silver **deliberately**. None is in Gold's grain. `part_2/05` claims Gold is *"the only layer where a question has an answer"* and narrows the grant to views over it. So *"how did Germany do last week?"* has no answer, and no page says what the copilot replies or what stops the fix being a wider grant — which is the one control in the design that must not bend. `part_1/04` creates the columns, `part_2/05` closes the door, neither names the escape hatch.

**3.7 Who deploys, and who can write where.**
Terraform is one table cell (§1.9). `part_2/05` never says who can create views in `semantic` — and the authorized dataset blesses **every** view in it, present and future, so `CREATE VIEW v_raw AS SELECT * FROM gold_opportunity` hands the agent base-table grain with both denominators back in play. `part_1/00`'s allowlist has the mirror-image hole: nothing stops an engineer adding an identifier column to a table with no expiry except a code review the page does not name. `part_2/03` and `part_2/04` both assume Dataform publishes their objects. **No page owns the deployment and write-permission model**, and it is load-bearing for both the privacy claim and the agent's blast radius.

**3.8 Part 2 has no operational spine at all.**
The Evaluation Grid's fourth line: *"data quality, production alerts, and daily maintenance."* Part 1 answers it better than most submissions will — five signals that fire while every job reports success, assertions gating Gold and never Silver, four repair triggers, a watermark-age monitor. Part 2 has **none of it**: no alert on rejection rate, no detector for a column shipped without a description (`part_2/04` finding 3 — the likeliest failure in practice, and the only mechanism on that page with no named failure mode), no answer-quality signal, no on-call story. Nobody owns "who is paged when the copilot is wrong."

**3.9 Two Part 1 repair paths that each assume the other page closed them.**
- **The watermark rewind.** `part_1/03` trigger 4 says replayed rows mean *"everything downstream then reruns unchanged."* They land with their original `publish_time`, **behind** Silver's watermark, so the next run never sees them. `part_1/06` makes the watermark settable and never connects it to trigger 4. The page's payoff line — *"one code path covers all four repairs"* — is carried by the one trigger that is actually a runbook.
- **Reference-data timing.** `part_1/06` computes `gross_revenue` at merge time against `ref_fx_rate` keyed on the auction's day, within 30 minutes of the auction. `part_1/04` declares FX an external table owned by finance with no loader and no schedule. `part_1/01` blocks the Gold rebuild on a null `publisher_payout`. Composed, **the design's normal daily state is a blocked Gold build**, and no page states the FX table's own convention or the repair path for already-merged nulls.

**3.10 The one deleted requirement with no reinstate condition.**
`intro/02` removes an entire security surface — *"~10 people, all seeing all publishers, so no row-level security to design"* — in a business the brief describes as serving *hundreds of media publishers*. `part_2/05` inherits it as a rejected alternative; `part_2/06` uses *"ten known users"* as the **whole** untrusted-input surface justifying the prompt-injection dismissal. In a document whose signature move is the reinstate condition, the decision that deletes the most work is the only one without one — and "publishers get a login" is the most predictable roadmap item in adtech. The user count itself is marked **Given** and appears nowhere in the brief.

---

## 4. GRADE CALIBRATION

### Re-ranked on one scale, strongest to weakest

| # | Page | Raw | Mine | Note |
|---|---|---|---|---|
| 1 | `part_1/06-dedup-sql` | A | **A** | Answers the mandated artifact in seven lines, then earns 2,000 more. Zero blockers; three technical soft spots, all one-line. The page to open an interview on. |
| 2 | `part_1/04-medallion-model` | A | **A** | Zero blockers, twelve decisions each with the alternative it beat, arithmetic that checks. Only gap is the unpriced unbounded line. |
| 3 | `part_1/05-bronze-partitioning` | A | **A** | Zero blockers, every figure independently verified, one genuine unreconciled criterion (cluster position 1). |
| 4 | `part_2/02-agent-flow` | A | **A−** | The highest verified-accuracy density in the document — the reviewer checked the whole Gen AI SDK surface and the LangChain v1 claims and found them all correct. One blocker (statelessness), and the build-vs-buy verdict currently leans on §1.2. |
| 5 | `part_1/00-retention-anonymisation` | A | **A−** | Every platform fact checks. One blocker, but it sits on the claim that licenses the entire Silver-is-durable inversion. |
| 6 | `part_2/03-semantic-layer` | B | **A−** | **Graded too harshly.** The reviewer wrote *"A-grade thinking"* and *"the strongest rejected-alternatives table in Part 2"* in the same block as a B. Two blockers, both one paragraph from fixed. |
| 7 | `part_1/01-architecture-diagram` | A | **B+** | **Graded too generously.** Half the page is excellent monitoring, but the deliverable the brief names first — *"propose a GCP architecture diagram"* — is 3464×1312 with three-line DDL labels and is unreadable at docsify width; and the `publisher_payout` assertion hands an SSP a kill switch on Gold for all publishers. |
| 8 | `part_1/03-hot-cold-separation` | A | **B+** | Slightly generous. The reframe is the best thinking in Part 1, but the thesis has a counterexample two pages earlier, and the page **violates the repo's own rule** by negating both halves of the test's phrase before answering either. |
| 9 | `part_1/02-component-justification` | B | **B+** | Correctly graded, arguably a touch harsh — eight rejections with reasons, two with conditions, and cost explicitly disqualified as the decider is what a senior engineer does. Held down by one cost concession that runs backwards. |
| 10 | `part_2/01-question-classes` | B | **B+** | **Slightly harsh.** The boldest and best-argued call in Part 2, held down by an arithmetic slip in a nine-cell table and one mechanism claim. Both are 30-minute fixes. |
| 11 | `part_2/06-guardrails` | B | **B** | Correct. The reframe (validation first, IAM last, and the terabyte scan was already unreachable) is the right closing move; the artifact carries a ceiling that fires on ordinary questions and a loop that fails open. |
| 12 | `part_2/04-glossary-and-entities` | A | **B** | **The most generous grade in the set.** Zero blockers recorded, but the page's bolded headline guarantee is false against `part_2/03`'s own file structure, its reinstate condition can never fire, and the likeliest real failure (a column shipped without a description) has no detector. The reviewer's own prose — *"what wobbles is the page's own headline guarantee"* — is B-shaped. |
| 13 | `part1-pipeline` | A | **B** | Generous. Excellent compression and a claims-not-labels routing table, but sentence two contradicts the pages beneath it, the pipeline's latency contract is never stated, and the best material in Part 1 (monitoring) is a subordinate clause. |
| 14 | `part_2/05-query-layer` | B | **B−** | Correct. One A-grade idea (*Gold's views, never its base tables*) sitting on a price table that contradicts Part 1 and a mechanism whose write-permission model is unwritten. |
| 15 | `part2-llm-agent` | A | **B−** | **Much too generous.** The only summary page in the document with **no number of any kind** and no marked Cost paragraph; misfiles Cube to Part 1; and omits the build-vs-buy verdict a CTO asks first. Its twin `part1-pipeline` opens with 2B/day and a $5,100 lever — the asymmetry is visible in one click. |
| 16 | `intro/01-methodology` | B | **B−** | Correct, and the two blockers matter more than B suggests: on a page whose subject is rigour, both checkable claims about the downstream pages are inflated (§1.1, §1.6). |
| 17 | `intro/02-business-assumptions` | B | **C+** | **Too generous, now confirmed against the primary source.** The foundation page marks 2B/day, 1.5 TB/day and ~10 users as **Given** when none appears in the brief; the brief's one stated quantity (*several billion*) is rounded **down to its floor** and relabelled as handed over; *hundreds of publishers* — the brief's other quantity — is missing entirely while being load-bearing on three pages. The four-way provenance taxonomy is the page's rigour signal and it is decoration as written. |
| 18 | `introduction` | B | **C+** | Correct letter, worse in context. The brief asks for *"a summary document"*; the document's first screen announces a delay and states no thesis. 66 words that score zero against the rubric's first line. |

### Is the Part 1 A / Part 2 B split real, or reviewer severity?

**Roughly 70% severity, 30% real — and the real 30% is exactly one thing.**

Evidence it is severity:
- Two Part 2 reviewers wrote *"A-grade thinking"* (`part_2/03`) and *"the thinking is A-grade"* (`part_2/01`) **inside a B grade block**. No Part 1 reviewer did the inverse.
- The blocker counts run **against** the letters. Part 1: 4 blockers over 7 pages, all of them **prose overclaims** (*"no process of ours can fail"*, *"nothing before Bronze can be wrong"*, an anonymity argument stopped one clause early). Part 2: 7 blockers over 6 pages, mostly **artifact errors** (a −$1.00 labelled identical to −$1.20, a 20 GiB constant, a $60 price row). Artifact errors are trivially caught and cheap to fix; prose overclaims are the ones that cost you in the room. The severity gradient is inverted relative to the letters.
- Praise language is symmetric: *"the strongest thinking in Part 1"* (`part_1/04`, `part_1/06`) against *"the strongest thinking in Part 2"* (`part_2/02`'s build-vs-buy) and *"an insight most submissions will not have"* (`part_2/04`).

Evidence of a real gap — and it is a single, nameable one:
- **Part 2 has no operability spine** (§3.8). Part 1's monitoring is the document's differentiator; Part 2 has no alerts, no evaluation, no failure UX, no on-call. That is a real deficit and it is one of the four rubric lines.
- **Part 2's numbers do not reconcile with Part 1's.** Part 1's figures cross-check across seven pages (the $5,100 delta, the 3.1× storage inversion, the $140/TiB vs $105/TiB comparison all verified independently). Part 2's central price table contradicts Part 1 outright, and its byte ceiling contradicts its own sibling.

Conclusion: Part 2's **design** reasoning sits level with Part 1's. Its **artifacts** and its **operational coverage** do not. Fix the four numbers in §1.4 and §1.8, add one monitoring paragraph, and Part 2 grades level. Do not restructure Part 2 on the strength of the letters.

---

## 5. THE DOCUMENT AS A WHOLE

**Does the page order tell a story?** Partly. Ordering by the test's bullets is correct and free — the grader checks boxes in their sequence. The single insertion, `part_1/00-retention-anonymisation` ahead of bullet 1.1, is the best structural decision in the document: it establishes the inversion (raw is transient, so **Silver** is the source of truth) that reshapes six later pages, and it earns its position.

The problem is the entrance. The chain runs `introduction` (70 words, a routing stub with no thesis) → `intro/01-methodology` (573 words about method) → `intro/02-business-assumptions` (520 words of requirements) → and only then, at 1,163 words in, the first architecture. The brief's expected format is *"a summary document (or presentation deck for discussion)"*. The reader's first screen says *"two pages before the answers"*.

**Is the strongest material buried?** Yes, systematically.

- `part_1/06-dedup-sql` — the strongest page, and the one containing the test's only mandated artifact — is **page 11 of 18**.
- `part_1/04-medallion-model` is page 9.
- `part_2/02`'s build-vs-buy against Conversational Analytics API — *"the strongest thinking in Part 2"* — is in the **last third of page 14**, after a nine-row hop table, with no sentence connecting the two halves.
- Part 1's monitoring spine — *"the alerts worth having are the ones that fire while every job reports success"* — is the material that separates this from a competent generic answer, and it appears in the Part 1 summary as a **subordinate clause in a routing table**.
- The document's single most quotable sentence (*"Every component in this design survived an argument for deleting it. Several components named in the test did not."*) sits on page 2, one click behind a page that spends its 70 words announcing a delay.
- The document's **last sentence** is *"depends on someone reading it"*, inside a Rejected table.

**What a CTO who reads only the first two pages concludes.** They read `introduction.md` and `intro/01-methodology.md` — 643 words. They conclude: *this candidate has a method, will not be rushed, deleted some components on a rule, and has not yet told me what they built.* They have seen **no GCP service name, no number, and no architecture.** They have been told there is a longer, better document with the reversals in it that they are not being shown. Measured against the rubric's first line — *"Relevance of GCP component breakdown and understanding of scale constraints"* — the first two pages score zero. The fix is about twenty words of thesis on page one; that is the highest leverage available anywhere in the document.

**Against the Evaluation Grid, which no page addresses directly.**

| Rubric line | Verdict |
|---|---|
| **Architecture & Scalability** — component breakdown, scale constraints (billions of rows) | Breakdown: **excellent**, and the deletion-with-reinstate-condition device is the differentiator. Scale: **the weakest of the four.** Every per-second figure is a daily mean with no peak, no growth, no headroom (§3.1), and 2B/day is the **floor** of the brief's *several billion* while being marked **Given**. A grader holding the brief finds this in ten seconds. |
| **BigQuery Expertise** — partitioning, clustering, deduplication, cost reduction | **Comprehensively answered; the document's strongest suit.** `part_1/05` and `part_1/06` carry this line by themselves, with verified arithmetic and the right instinct (lead with the window function the bullet asked for, then the `MERGE` that makes it correct). If only one rubric row scores well, it is this one. |
| **AI & Software Vision** — secure RAG/Text-to-SQL **without unnecessarily exposing the infrastructure to model drift** | Secure: **answered well** (`part_2/05`'s grant + `part_2/06`'s four layers). RAG: answered by **refusing an index** — defensible and well argued, but the size justification is on a different page from the claim, and the grader is box-checking. **Model drift: not addressed anywhere** (§3.4). A named rubric line with a zero. |
| **Operational Pragmatism** — data quality, production alerts, daily maintenance | Part 1 answers this **better than most submissions will**. Part 2 answers none of it (§3.8). And the half that is answered is **invisible in the summary layer**. Half a line scored, and the scored half is buried. |

Two rubric lines answered strongly, one half-answered and buried, one at zero — and the two weakest are precisely the two a summary layer would have to carry.

**Is ~21,600 words across 18 pages the right artifact for the ask? Plainly: not on its own.** It is 8-10× a summary document. But the repo's working rules say the output is defended live in a ~1h presentation, which makes the write-up the reference and the defence the deck — a coherent choice the document never signals. There is no fast path, no *"if you read three pages"*, and the summary layer that could serve as the deliverable is 70 + 764 + 510 = **1,344 words**, with the 70-word one as the entry point. The answer is **not to cut 20,000 words to a summary.** It is to make those three top-level pages *be* the summary document the brief asked for — a thesis on `introduction.md`, a fast path, the latency contract on `part1-pipeline`, and the two missing numbers plus the build-vs-buy verdict on `part2-llm-agent` — so a reader who stops at 1,400 words has read the deliverable and everything beneath it is annex. That is roughly 150 words of new writing across three pages.

One last note in the document's favour that no reviewer could see: the brief's example question — *"**Why** did the eCPM of publisher X drop by 20% yesterday on the video format?"* — is a *why* question, and `part_2/01` builds the entire Part 2 design around the observation that a *why* answer cannot be sanity-checked by its recipient. That is the sharpest read of the brief anywhere in the document, it is a direct answer to the brief's headline, and it appears in the summary layer nowhere.

---

## 6. ACTION LIST

1. **Hoist a thesis and a three-page fast path onto `introduction.md`** — name the components kept and deleted in one line, then *"if you read three pages: the retention ceiling, the component verdicts, the guardrails."* The first screen currently scores zero on the rubric's first line. — **30min**
2. **Reprice `part_2/05`'s three-layer table under Part 1's actual DDL and reconcile `part_2/06`'s 20 GiB ceiling against `gold_ssp`'s sizing** — the two numbers that contradict Part 1 and each other, both inside the artifacts Part 2's closing theses rest on. — **2h**
3. **Fix `intro/02-business-assumptions.md` against the brief** — define the four provenance labels in one line; re-mark 2B/day, 1.5 TB/day and ~10 users as Confirmed or Assumed, stating 2B as the floor of *several billion*; add rows for peak-to-average, growth, publisher cardinality and ad-unit cardinality; attach the reinstate condition to the no-row-level-security line. — **2h**
4. **Add a model-drift and answer-quality paragraph to `part_2/02-agent-flow.md`** — what is logged, the fixed question set re-run when the unpinned model changes, who sees a rising rejection rate. Closes the one rubric line currently at zero. — **2h**
5. **Canonicalise the component roster on `intro/01-methodology.md`** — one count, one list, Cube returned to Part 2 on `part2-llm-agent`; and narrow the reinstate-condition promise to what three tables actually deliver. Five pages currently disagree in a claim checkable in ten seconds. — **30min**
6. **Re-render `assets/architecture.png` legible at docsify content width** — DDL text off the nodes (2.2 owns it), `quality_hour` routed through the semantic-layer cluster rather than straight to the BI/copilot node, dotted DLQ → Monitoring edge. It is the brief's first named deliverable. — **2h**
7. **Numeric-consistency sweep** — `part_2/01`'s worked example (make both scenarios −$1.20), `no_bid` 75-80% → `bid + no_bid`, *"five events"* → *"the cluster of events"*, 25 → 26 partitions, `is_settled`'s second hour named, plus re-verify the Data Catalog date and the `QueryUsagePerDay` default before either is defended live. — **2h**
8. **Close the statelessness / clarifying-turn contradiction and write the rejection path into `part_2/02`'s hop table** — one sentence at hop 1, one at hop 9 covering what the analyst sees when a guardrail fires and whether it returns to the model. — **30min**
9. **Qualify the two Part 1 absolutes and close the two repair-path seams** — scope *"no process of ours can fail"* and *"nothing before Bronze can be wrong"* against the dead-letter path 1.1 already documents; add the watermark rewind to `part_1/03`'s trigger 4; state the GCS archive's write format once; scope `part_1/01`'s `publisher_payout` assertion so a third party cannot block Gold. — **2h**
10. **Deletion-only pass over every Rejected table across all 18 pages** — cut rows that restate the prose immediately above them (~640 words), then the cross-page duplicates in §2. Brief the pass as deletion-only: nothing may be added. — **half-day**
