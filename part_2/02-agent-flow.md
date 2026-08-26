# 1.2 — User → Orchestrator → Model → BigQuery

*Test bullet: detail the flow between the user, the orchestrator (e.g., LangChain or FastAPI), the model (Vertex AI / Gemini), and the BigQuery database (Text-to-SQL + RAG pattern).*

**Nine hops, FastAPI to Gemini to BigQuery, with no agent framework between them.** The test names LangChain as an example; a framework whose agent entry point moved packages inside a year is a runtime we operate, in a seam we own either way. `tool_config` on the Vertex call enforces the routing a framework would only ask for, and every job we submit carries its own byte ceiling.

---

![OptimusAds — Yield copilot: flow, guardrails, blast radius](../assets/agent.png)

## The flow, hop by hop

| # | Hop | Mechanism | Latency |
|---|---|---|---|
| 1 | Analyst → FastAPI on Cloud Run | One `POST` per question, stateless — no session store, no state to invalidate | — |
| 2 | FastAPI assembles context | The metric dictionary, generated from `INFORMATION_SCHEMA` and injected whole, plus four `FunctionDeclaration`s and a `tool_config` | ms |
| 3 | FastAPI → Gemini on Vertex AI | `client.models.generate_content(model=…, contents=…, config=GenerateContentConfig(tools=[…], tool_config=…))` | ~1–2 s |
| 4 | Gemini → tool call | A name and arguments on `response.function_calls` — the model chooses *what* to ask, and writes no SQL on three of the four tools | — |
| 5 | Validator | `run_query` only: parse, single `SELECT`, allowlist, mandatory date predicate — our code, ahead of the client | ms |
| 6 | Dry run | `run_query` only: bytes-to-be-scanned returned by the engine without executing | < 1 s |
| 7 | Execute against the semantic views | **Every** job carries `maximum_bytes_billed`, the fixed routines included — they take model-chosen arguments even though we wrote their SQL; the service account holds `SELECT` on the semantic-layer dataset alone | 1–3 s |
| 8 | Result → model | `Part.from_function_response(...)` appended to `contents`; the loop returns to hop 3 | ms |
| 9 | Narration → FastAPI → analyst | Four fields on the same `POST`: the prose, the executed SQL, the rows, and the period's quality verdict | ~1–2 s |

**The objection is a dependency one.** We own the seam either way. One of the two ways is a framework whose agent entry point moved packages inside a year. `AgentExecutor` now ships in a separate `langchain-classic` package. `create_agent` is the supported path. This is the argument that removed Dataflow, Composer and dbt Core in Part 1, and Cube and a vector database alongside LangChain in Part 2: *a runtime we operate, placed between us and something we could call directly.*

**Cost.** BigQuery bytes dominate per question, not tokens, and the ceiling at hop 7 bounds the worst case, not the average. Context caching is not a lever: the minimum cacheable prefix for the Gemini 3 family is 4,096 tokens, below which the dictionary block sits.

## Rejected — one line each

| Option | Why not |
|---|---|
| **Vertex AI Agent Runtime** (ex Agent Engine) | Managed hosting, sessions and memory for a stateless single-turn call with four tools; also pins the service to Python |
| **Google ADK** | The same objection one layer closer to Google: a framework above a call we make in one line |
| **Looker + LookML**, even already in place | Its agent is documented as not supporting correlation questions — the test's own example. And reaching LookML from our loop means the Open SQL Interface: `SELECT` only, no `JOIN`, and the job runs on Looker's connection, leaving nothing of ours to carry the dry run, the ceiling or the grant |
| **Streaming model tokens to the user** | The answer is checkable only once the SQL and numbers arrive with it; a streamed narration is read before either exists |
| **A custom web UI for the ten analysts** | A fifth component in a four-participant flow, serving a cross-check the four response fields already carry |

---

Next: [**2.1 — Metrics & Business Glossary**](/part_2/03-semantic-layer.md)
