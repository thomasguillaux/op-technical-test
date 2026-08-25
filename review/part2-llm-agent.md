# Review — `part2-llm-agent.md`

## Summary

A 510-word executive summary for Part 2: six sentences that build the copilot from one idea (can the reader catch a wrong answer?) down to its blast radius, plus a claim-led routing table into the six bullet pages. It lands — a CTO who stops here has the right mental model of what the thing does and what it can reach — but it carries no number, no stated limit, and no answer to the first question any CTO asks about an LLM feature in 2026: why not buy it.

## Grade

- **Decision quality — B.** Every sentence is a decision paired with the reason for it, which is rare discipline at summary length; the soft spot is that the biggest rejected alternative in Part 2 (Google's GA Conversational Analytics API) appears neither in the sentences nor in the routing table.
- **Narrative — A.** Sentences 2→6 are a chain, not a list: the catchability split produces the tool design, which produces the trust model, which produces the grant, which produces the no-framework rule — and the routing rows are claims rather than descriptions.
- **Operability instinct — B.** "Guardrails bound the bad case, the grant bounds the normal one" is a genuinely operational insight and the diagram renders blast radius explicitly, but there is no cost magnitude, no latency, and nothing about how anyone would learn the copilot had stopped being right.
- **Technical plausibility — A.** FastAPI on Cloud Run, `google-genai`, views in a dataset authorized over Gold — nothing here a staff engineer would wince at, and every claim is supported by the pages beneath it.
- **Signal density — A.** 510 words with zero throat-clearing; the only slack is one SDK name, one clause said twice, and one row that repeats a sentence verbatim (~50 words total, all identified in Cuts).
- **Overall — A.** It passes its own test — the reader leaves with the copilot and its blast radius correctly modelled and knows which page to open — and the misses are one-line hoists from pages already written, not gaps in thinking.

## Top findings

**1. [QUESTION] Build-vs-buy is invisible, so sentence 6 reads as reflex.**
- **What:** "No component sits between us and something we could call directly — no LangChain, no vector database, no agent runtime" is the page's closing note, and nothing on the page acknowledges that Google shipped a GA product that does most of this.
- **Why it matters to the evaluator:** A CTO's first question about an LLM feature is "why are we building this?", and a summary that lists three things it refused to adopt without naming the product it competes with reads as not-invented-here — which is exactly the read `1.2` demolishes, one click away, with two documented facts.
- **Fix:** One clause in sentence 6 or one routing row: "Conversational Analytics API went GA for BigQuery in June and carries most of this page — it loses on two documented facts, both in 1.2." Turns a reflex into a verdict at a cost of ~20 words.

**2. [QUESTION] Not a single number on the page.**
- **What:** No cost, no latency, no scale; "the largest cost control in Part 2" is asserted twice with no magnitude, and unlike its twin `part1-pipeline.md` this page carries no marked **Cost** paragraph.
- **Why it matters to the evaluator:** Part 1's summary opens with 2B events/day and names a $5,100/month lever, so the asymmetry is visible; and "cost control" without an order of magnitude is the one kind of claim a CTO cannot act on.
- **Fix:** Free the words in Cuts 1 and 3 and spend them on the two figures that already exist downstream — `3.1`'s priced comparison (cents on the views, ~$60 on Bronze, unbounded on Silver) and `1.2`'s end-to-end latency (~4–8 s per question).

**3. [QUESTION] The summary implies the *why* class has been de-risked; the pages below concede it has been bounded.**
- **What:** Sentences 3 and 4 say the model writes none of the *why* SQL and does not judge its own input — but `1.1` states the honest limit ("this localises a change; it does not explain it") and `3.2` states that the narration is unguarded, and neither concession reaches this page.
- **Why it matters to the evaluator:** The concessions are the highest-trust sentences in Part 2; leaving them downstream means the summary makes the stronger claim and the correction only arrives for a reader who keeps going.
- **Fix:** Add the seventh sentence, from `1.1` verbatim: "It localises a change; it does not explain it — a locus is checkable, a story is not." That single line converts the page from a capability claim into a calibrated one.

**4. [QUESTION] Nothing says how anyone finds out the copilot has got worse.**
- **What:** The page's trust argument is entirely structural (fixed SQL, quality verdict, IAM), with no mention of evaluating answers — and `1.2` deliberately pins no model ID, so the model underneath will change without a deploy.
- **Why it matters to the evaluator:** "You've told me what it can't reach; you haven't told me how you'd know it started answering badly" is the obvious follow-up to an unpinned model, and as far as I can see no page in Part 2 answers it.
- **Fix:** One clause here and a short paragraph on `1.2`: the four response fields are logged, and a fixed set of questions with known answers is re-run on model change — the cheapest possible version, sized for ten users.

**5. [POLISH] Cube is attributed to Part 1, and the two summary pages disagree on the roster.**
- **What:** Sentence 6 says the rule "removed Dataflow, Composer, dbt Core and Cube from Part 1", but Cube is rejected in `2.1` — and `part1-pipeline.md` says so explicitly ("Dataflow, Composer and dbt Core here; Cube, LangChain and a vector database in Part 2"). The two pages also disagree on the count: Part 1 says six components, this page adds "agent runtime" as a seventh.
- **Why it matters to the evaluator:** The shared rule is the document's signature move, sold on "one rule applied six times is a design"; mis-stating which part removed which component is the one place where that claim can be checked in ten seconds and fails.
- **Fix:** "…the same sentence that removed Dataflow, Composer and dbt Core in Part 1, and Cube here." Then reconcile the tally with `part1-pipeline.md` — either the roster is six and Agent Runtime folds into "agent runtime", or both pages say seven.

## Cuts

**1. Routing row 3.1, second clause (~14 words).** "and the largest cost control in Part 2 is not a guardrail, it is an IAM grant" is a verbatim repeat of sentence 5, fourteen lines above it. Nothing is lost by deleting it, and the row's unique offer — the same question priced at three layers — is what should sit there instead. This cut and its replacement close finding 2 at zero net cost.

**2. "called through the Google Gen AI SDK" (~6 words).** Which SDK is an implementation detail with a real argument behind it (`1.2`: the Vertex AI SDK was removed in June 2026), and that argument cannot fit here. "Gemini on Vertex AI" carries everything a CTO needs at this altitude; the SDK earns its paragraph one page later.

**3. Sentence 1's "and BigQuery views as the only objects any generated SQL may name" (~12 words).** Sentence 5 says the same thing properly — with the mechanism (a dataset authorized over Gold) and the consequence (it is the cost control). Saying it first without either spoils the payoff and buys nothing.

**4. "Where to go deeper" preamble, ~26 words → ~14.** "One page per bullet of the test, in the test's order. Each page stands alone and ends with the options it rejected, one line each" is word-for-word `part1-pipeline.md`. On second encounter it is a document convention the reader has already lived through for seven pages. Keep "One page per test bullet, in the test's order; each ends with what it rejected." **~12 words saved**, nothing lost but the restated promise.

**5. Flagged, not recommended: "because judging whether its input is complete is the thing an LLM is least able to do" (~17 words).** The first half of the sentence already carries the decision; the superlative invites "says who?" from the one reader who wants to argue. Real tradeoff — it is also the most quotable clause on the page. Keep it if the rhetoric is wanted, but know it is the only unsupported assertion here.

Total recoverable: **~45 words**, roughly 9% of the page, which is more than enough for the priced comparison, the build-vs-buy clause, and the honest limit.

## Interview questions this page invites

1. **"Conversational Analytics API is GA on BigQuery. Why are you building an agent?"** *Not answered here, or anywhere in the summary layer* — not in the six sentences, not in the six routing rows. `1.2` answers it very well (the routine cannot be forced; table selection is documented as not a security control), which makes the omission pure lost value.
2. **"You don't pin a model ID. How do you find out the day the new Gemini starts explaining things worse?"** *Not answered*, here or on the pages below. The design's answer to correctness is structural — fixed SQL, quality verdict — and structure does not degrade when a model changes, but narration does, and `3.2` concedes narration is unguarded.
3. **"What does one question cost, and how long does an analyst wait?"** *Not answered here.* `1.2` has the per-hop latency and `3.1` has the three-layer price comparison; both are one hoist away, and until one arrives, "the largest cost control in Part 2" is an unfalsifiable claim.

## Claims ledger

**DECISIONS**
- One agent, four tools, code we own — rejects LangChain, vector database, agent runtime under one rule: *a runtime we operate, placed between us and something we could call directly*.
- FastAPI on Cloud Run as the orchestrator — LangChain named as the rejected alternative; **Cloud Run itself is asserted, never argued, on this page or on `1.2`**.
- Gemini called through the Google Gen AI SDK — alternative (Vertex AI SDK) not stated here; argued on `1.2`.
- Question classes split by *catchability*, not topic — no alternative split stated here.
- Model writes SQL for *what*, none for *why*; `diagnose_change` is fixed and the model chooses only its arguments — alternatives (pure text-to-SQL, routine library) not named here.
- Trust is read from the pipeline (`is_settled`, the quality table), not judged by the model.
- Query surface is views only, in a dataset authorized over Gold — Bronze/Silver/Gold base tables not named as the rejected options here.
- The IAM grant, not any guardrail, is the primary cost control; guardrails bound the bad case.
- **Absent by omission (recorded for cross-page coherence):** build-vs-buy against Conversational Analytics API and Looker; any cost, latency or evaluation claim.

**TECH**
Prose: FastAPI, Cloud Run, Gemini, Google Gen AI SDK, BigQuery, BigQuery views, authorized dataset (implied by "authorized over Gold"), IAM/service account, LangChain (rejected), vector database (rejected), agent runtime (rejected), Dataflow / Composer / dbt Core / Cube (cited as removed elsewhere).
Diagram only: Vertex AI, `run_query`, `diagnose_change`, `resolve_entity`, `INFORMATION_SCHEMA`, `maximum_bytes_billed`, dry run, static validation, `v_opportunity_hourly`/`_daily`, `v_ssp_hourly`/`_daily`, `v_quality_hour`, `bronze_events`, `silver_events`, gold base tables.

**TERMS**
- *Copilot* — an agent for ten Yield analysts reading Gold only.
- *Catchability* — whether the person receiving an answer can tell it is wrong; used as a property of the question, not the person.
- *what* vs *why* question — number/ranking/trend vs cause/attribution.
- *`diagnose_change`* — a fixed decomposition the model points at but does not write.
- *`is_settled`* — used bare, defined in Part 1 (`04-medallion-model`).
- *"the quality table"* — in fact a view (`v_quality_hour`), per `3.1` and the diagram.
- *Blast radius* — appears only in the diagram title, never in the prose.
- *guardrail vs grant* — guardrails bound the bad case, the grant bounds the normal one.
- *"the same sentence"* — the shared rejection rule spanning both parts.

**NUMBERS**
- Ten Yield analysts. Four tools. Six sentences. One agent.
- Diagram only: four numbered guardrail layers; "20%" inside the example question.
- **No cost, latency, throughput or SLA figure appears on this page** — the only summary page in the document with none, and the only one without a marked **Cost** paragraph.

**ASSUMES**
- Part 1's Gold layer exists, stores additive measures, and publishes `is_settled` plus a quality verdict.
- ~10 users, all seeing all publishers (`intro/02-business-assumptions.md`).
- Part 1 removed Dataflow, Composer, dbt Core **and Cube** — *contradicted* by `part1-pipeline.md` and `2.1`, which place Cube in Part 2.
- The authorized-dataset mechanism and the exact grant are argued on `3.1`.
- The four guardrail layers are carried by the diagram; the prose never enumerates them.
- Three of the four tools are named only in the diagram; the prose names `diagnose_change` alone.
- The reader knows the adtech vocabulary (eCPM, Yield) without introduction.
