# Part 2 — LLM Agent Integration (Yield Optimization)

**A copilot for ten Yield analysts, over the Gold layer of the Part 1 pipeline.**

![OptimusAds — Yield copilot: flow, guardrails, blast radius](assets/agent.png)

## The design in five sentences

**One agent, four tools, our code** — a FastAPI loop on Cloud Run, Gemini called through the Google Gen AI SDK, and BigQuery views as the only objects any generated SQL may name.

The split that produces everything else is not *what the question is about* but **whether a wrong answer can be caught by the person receiving it**: a number can be checked against a dashboard, an explanation cannot be checked against anything.

So the model writes SQL for *what* questions and writes none of it for *why* questions — **`diagnose_change` is a fixed decomposition, and the model chooses only what to point it at.**

**Trustworthiness is a property of the pipeline, not of the prompt**: the copilot reads `is_settled` and the quality table rather than judging its own input, because judging whether its input is complete is the thing an LLM is least able to do.

**No component sits between us and something we could call directly** — no LangChain, no vector database, no agent runtime — which is the same sentence that removed Dataflow, Composer, dbt Core and Cube from Part 1.

## Where to go deeper

One page per bullet of the test, in the test's order. Each page stands alone and ends with the options it rejected, one line each.

| Page | The claim it defends |
|---|---|
| [**1.1 — Copilot Scope & Question Classes**](/part_2/01-question-classes.md) | Catchability is a property of the question, not the person — and the uncatchable answer is the one people act on |
| [**1.2 — User → Orchestrator → Model → BigQuery**](/part_2/02-agent-flow.md) | The flow hop by hop, and the one config field that separates a guarded executor from a model calling BigQuery directly |

---

Next: [**1.1 — Copilot Scope & Question Classes**](/part_2/01-question-classes.md)
