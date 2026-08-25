# Review — `part_2/02-agent-flow.md` (1.2 — User → Orchestrator → Model → BigQuery)

## Summary

This page answers the test's flow bullet as a nine-hop table from analyst to BigQuery and back, then spends its second half on the two questions the bullet implies but does not ask: why our own loop rather than LangChain, and why build at all when Google sells this product. It lands — the API surface is correct where being wrong would have been fatal, and the build-vs-buy argument is the strongest thinking in Part 2 — but the flow contract itself has a hole (statelessness vs. the clarifying turn) and the latency column never prices the test's own example question.

## Grade

- **Decision quality — A.** Steelmans LangChain (`wrap_tool_call` *can* hold the seam; "claiming otherwise is a strawman") and then rejects it on dependency grounds; concedes Conversational Analytics API carries "most of this page" and wins on two *documented* facts rather than opinion.
- **Narrative — B.** The hop table → the one config flag → build-vs-buy has a spine and a closing line worth the price of admission ("they are hiring the engineer"), but the last third is a different essay from the first two-thirds with no sentence connecting them.
- **Operability instinct — B.** Names the operational landmine precisely (`automatic_function_calling` disabled, or the SDK calls BigQuery for you) and treats model-ID churn as an operational fact; no end-to-end latency, no Vertex retry/timeout behaviour, no statement of what the analyst sees when a guardrail or the loop bound fires.
- **Technical plausibility — B.** I checked the Gen AI SDK surface (`genai.Client(vertexai=True)`, `client.models.generate_content`, `GenerateContentConfig(tools=, tool_config=)`, `response.function_calls`, `Part.from_function_response`, `AutomaticFunctionCallingConfig(disable=True)`, `maximum_remote_calls` default 10) and the LangChain v1 claims (1.0 shipped 2025-10-22, `create_agent` on the LangGraph runtime, `AgentExecutor` in `langchain-classic`, `wrap_tool_call` receiving the call pre-execution and short-circuiting by returning a `ToolMessage`) — all correct, as are the `vertexai.generative_models` deprecation and removal dates; the winces are self-reported numbers, not mechanism.
- **Signal density — B.** Very little padding for 1,540 words, but the Conversational Analytics and Looker arguments are made twice, once in prose and once in the Rejected table.
- **Overall — A.** This reads as a strong senior engineer who checked the docs rather than the blog posts; every finding below is a one-to-three-sentence fix, and one of them should be fixed before this is defended live.

## Top findings (max 5)

**1. [BLOCKER] "Stateless — no session store, no state to invalidate" has no room for the clarifying turn that 2.2 promises.**
- What: hop 1 declares one stateless `POST` per question and hop 9 returns four fields — none of them a conversation handle — yet 2.2 says `resolve_entity` returns ranked candidates and "where more than one scores close, the copilot asks which. One question costs a turn."
- Why it matters: the flow contract is this page's actual deliverable, and the first thing a reader tests is the most common real interaction — an ambiguous name, or any follow-up question at all.
- Fix: one sentence at hop 1 — the client echoes the prior `contents` back on the next `POST`, so the conversation is state the caller carries and the service still holds none — or state that clarification resolves inside the same request by re-prompting with the candidate list.

**2. [QUESTION] The latency column prices a `run_query` question and silently omits the test's own example.**
- What: hop 7 is "1–3 s", but 1.1 defines `diagnose_change` as a quality gate plus four independent single-dimension passes over two periods — the *why* path is many jobs, not one, and the page never sums the column into an end-to-end figure.
- Why it matters: a CTO reading a latency column expects a bottom line, and the one question the test actually asked is the one the column does not cost.
- Fix: two figures and a verdict — *what* ≈ 5 s, *why* ≈ 10–15 s because the routine is N sequential passes, acceptable against the analyst's alternative of writing the SQL herself.

**3. [QUESTION] Hop 2 issues a BigQuery metadata query on every request and prices it at "ms".**
- What: 2.2 states the dictionary block is generated from `INFORMATION_SCHEMA.COLUMN_FIELD_PATHS` "at request time"; that is a BigQuery job round-trip on the hot path, not milliseconds, and it is a job the orchestrator issues that 3.2's "every job carries `maximum_bytes_billed`" rule does not visibly cover.
- Why it matters: it is the one hop where the page's own numbers say something a staff engineer knows to be untrue, on a table whose credibility rests on precision.
- Fix: cache the assembled block with a TTL (or build it at deploy, since Dataform publishes on build) and relabel the hop; one clause saying the dictionary refreshes on deploy rather than per request removes the issue entirely.

**4. [QUESTION] The RAG half of the named pattern rests on "because it fits", with no number on the page.**
- What: the page locates retrieval correctly (hop 2 for the dictionary, a live tool call for entities) but the justification for injecting whole is a two-word assertion, deferred to 2.2 — and the only sizing evidence here is a cost aside implying the block sits under 4,096 tokens, which sits awkwardly beside 2.2's "a few thousand tokens on every request".
- Why it matters: a grader checking the box marked "RAG" reads "injected whole" and "not an index" and needs the size argument in the same paragraph, not one page later; the house rule is that a linked argument is an absent one.
- Fix: carry one clause from 2.2 — a few dozen definitions, a few thousand tokens against a million-token window — plus the reinstate condition (`VECTOR_SEARCH` in BigQuery if the corpus outgrows the window), and reconcile it with the 4,096-token caching claim.

**5. [POLISH] The diagram shows three tools; hop 2 says four `FunctionDeclaration`s.**
- What: `assets/agent.png` renders `diagnose_change` and `resolve_entity` as boxes and represents `check_quality` only as an "is the period settled?" edge off the byte-ceiling diamond, which reads as a step inside execution rather than the fourth tool; `diagnose_change(grain)` also shortens 1.1's five-argument signature, and the "Gemini on Vertex AI — selects a tool" label is partly overrun by an arrow in the render.
- Why it matters: the diagram is the first thing read on two pages, and "four tools" is a load-bearing count in the prose.
- Fix: add a `check_quality` box on the same tier as the other two and nudge the Gemini label clear of the edge. (The diagram is right on the subtlest point — the fixed-SQL paths bypass validation and dry run but still pass the ceiling — which is worth preserving.)

## Cuts

1. **Hop 9's scope paragraph (line 23) — ~95 words down to ~30.** The Rejected table already carries "A custom web UI for the ten analysts", and the second half of the paragraph restates 1.1's catchability argument in full. Keep "Hop 9 is a contract, not a page" plus the four fields; drop the re-derivation. Lost: nothing the reader has not read on the previous page.
2. **The Looker prose paragraph (line 63) or the Looker Rejected row (line 73) — pick one, save ~90 words.** They make the same two arguments; the table row is the better version because it adds the Open SQL Interface constraints the prose omits. Move the "*a tool already paid for is still not a tool that answers the question*" line into the row and delete the paragraph. Lost: a good closing cadence, recoverable in the row.
3. **The Conversational Analytics feature enumeration (line 55) — ~55 words down to ~20.** Nine named features is conceding at length; "it now carries most of this page — byte ceilings, IAM scoping, a glossary, registered routines, generated SQL shown" is the same concession at half the price. Lost: nothing; the argument is the two survivors, not the list.
4. **The Cloud Next '26 rename parenthetical (line 41) — ~25 words.** It changes no decision, and it is the only sentence on the page that is pure currency signalling. Every other date earns its place by killing an option. Lost: a small "I read the release notes" signal that the surrounding paragraph already delivers.

Total: ~250 words, roughly 16% of the page, none of it argument.

## Interview questions this page invites

1. **"An analyst types 'why did site Y drop', `resolve_entity` returns three candidates, the copilot asks which — where does that conversation live if every `POST` is stateless?"** Not answered. This is finding 1, and it is the first question anyone asks a flow diagram.
2. **"How long does your own example question take, start to finish, and did you ask the ten analysts whether that is acceptable?"** Not answered — per-hop latencies only, and the `diagnose_change` path is not costed at all.
3. **"You concede the Conversational Analytics API already carries most of this page. If Google documents a way to force a routine next quarter, do you delete your loop — and what did the fifty lines buy in the meantime?"** Half answered: the two surviving objections are precise and documented, but unlike Part 1's rejections this table states no reinstate condition, so the answer to "what would change your mind" has to be improvised.

## Claims ledger

**DECISIONS**
- Own loop inside FastAPI (hops 3–8, ~50 lines) — rejects LangChain v1/LangGraph inside FastAPI; explicitly *not* a capability argument (`wrap_tool_call` can hold the seam), a dependency one.
- Google Gen AI SDK (`google-genai`) — rejects Vertex AI SDK (`vertexai.generative_models`), removed 2026-06-24.
- Tools declared as `FunctionDeclaration`s with `AutomaticFunctionCallingConfig(disable=True)` — rejects passing Python callables (SDK executes them itself; no seam for hops 5–7).
- No model ID pinned; selection criteria are Flash tier, function calling, 12-month availability class.
- Build, not buy — rejects Conversational Analytics API on two documented facts: routine use is advisory ("if they're needed"), and "table selection isn't a security setting".
- Rejects Looker + LookML / Conversational Analytics in Looker even where already in place — no correlation/forecasting support; Open SQL Interface is `SELECT`-only, no `JOIN`, runs on Looker's connection.
- Rejects Vertex AI Agent Runtime (ex Agent Engine) — sessions/memory for a stateless single-turn call; pins the service to Python.
- Rejects Google ADK — framework above a one-line call.
- Rejects streaming model tokens — the answer is checkable only when SQL and rows arrive with it.
- Rejects a custom web UI — hop 9 is a contract; the client is out of scope.
- Stateless `POST` per question, no session store; loop bounded at two.
- Validator (hop 5) and dry run (hop 6) apply to `run_query` only; `maximum_bytes_billed` (hop 7) applies to every job including the fixed routines.
- Retrieval: dictionary injected whole at hop 2; entities resolved by live tool call, not an index.
- Context caching not used.

**TECH** — FastAPI; Cloud Run; Vertex AI; Gemini (Flash tier); `google-genai` / `genai.Client(vertexai=True, project, location)`; `client.models.generate_content`; `GenerateContentConfig`; `tools`; `tool_config`; `FunctionDeclaration`; `response.function_calls`; `Part.from_function_response`; `AutomaticFunctionCallingConfig(disable=True)`; `maximum_remote_calls`; `maximum_bytes_billed`; BigQuery; `INFORMATION_SCHEMA`; semantic views; `run_query`; `diagnose_change`; `resolve_entity`; LangChain v1; `create_agent`; LangGraph; `wrap_tool_call`; `ToolMessage`; `AgentExecutor`; `langchain-classic`; `vertexai.generative_models`; Vertex AI Agent Runtime / Agent Engine; Google ADK; Conversational Analytics API; `big_query_max_billed_bytes`; Knowledge Catalog; `user_functions.bqRoutines`; Looker; LookML; Open SQL Interface; IAM service account; `gemini-2.5-flash`; Gemini 3 family; Gemini Enterprise Agent Platform.

**TERMS** — *hop* (numbered 1–9, referenced by number from 2.2 and 3.2); *the guardrail seam* (the point between model output and BigQuery); *automatic function calling* (SDK-side execution, disabled); *parallel function calling* (several calls per turn, no disable flag); *the four response fields* (prose, executed SQL, rows, quality verdict); *Text-to-SQL* = hop 4 into hops 5–7; *RAG* = two mechanisms (whole injection + live entity lookup); *"a runtime we operate, placed between us and something we could call directly"* — the recurring rejection sentence.

**NUMBERS** — loop runs at most twice; hop 2 "ms"; hop 3 ~1–2 s; hop 5 "ms"; hop 6 <1 s; hop 7 1–3 s; hop 8 "ms"; hop 9 ~1–2 s; ~50 lines of loop; four tools / four `FunctionDeclaration`s; four response fields; four guardrail layers; `maximum_remote_calls` default 10; LangChain v1 shipped 2025-10-22; `vertexai.generative_models` deprecated 2025-06-24, removed 2026-06-24; `gemini-2.5-flash` retires 2026-10-20; 12-month availability class; minimum cacheable prefix 4,096 tokens (Gemini 3 family); Conversational Analytics API GA for BigQuery 2026-06-23; Cloud Next '26 rename; ten analysts.

**ASSUMES** — from 1.1: four tools, the catchability split, `mode = ANY` with `allowed_function_names`, `diagnose_change` as fixed decomposition, and that the test's example is an investigation. From 2.1/3.1: semantic-layer views exist over Gold and carry their own arithmetic; a quality view publishes the period verdict. From 2.2: the dictionary is Dataform column descriptions surfaced through `INFORMATION_SCHEMA`, and neither retrieval mechanism needs a vector store. From 3.1: the service account holds `SELECT` on the semantic dataset alone, via an authorized dataset over Gold. From 3.2: the four guardrail layers and the `execute()` wrapper that applies the ceiling to every job. From Part 1: a Gold layer, `is_settled`, and on-demand BigQuery pricing. From the client: ten analysts, no free text in the data. Cost premise: BigQuery bytes dominate per question, not tokens.
