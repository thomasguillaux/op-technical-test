# Methodology

> **Every component in this design survived an argument for deleting it.**
> Several components named in the test did not.

*This repository is public, so the company is called **OptimusAds** here and publisher names and identifiers are anonymised. Nothing else is changed.*

## Requirements are the input; components are the output

Drawing the boxes named in the test and connecting them produces an architecture nobody can defend, because no component ever had to justify itself. I worked the other way round: the requirement first, then the smallest thing that satisfies it, then an argument for deleting that thing. What is in the diagrams is what survived.

That is why most sections end with a **Rejected** table. Where a component named in the test is absent, the table gives the reason it lost *and* the condition that brings it back — the condition is the load-bearing half, because "no Dataflow" is a claim about this volume and this latency, not about Dataflow. The option that lost says more than the option that won, and it is the part a reviewer can test.

## Three rules, applied to every decision

**Map the decisions before making any of them.** I listed the scope as a dozen open questions — retention, the hot/cold line, the Gold grain, the agent's blast radius — before settling one, so that no early convenience quietly decided a later question on its behalf.

**Attack it against sources, not recollection.** Each decision was argued down before it was written up, and the figures behind it checked against primary documentation rather than memory. Every number that carries an argument — the partition-grain delta, the streaming rates, the 7-day retention arithmetic — is one I can source on the spot.

**Record the argument, not the conclusion.** A conclusion alone is worthless the moment it is challenged. Each decision is kept with the requirement it satisfies and the alternative it beats; the Rejected tables are the compressed form of exactly that.

The reward for the three rules is a single sentence that killed six components at once — *a runtime we operate, placed between us and something we could call directly* — Dataflow, Composer and dbt Core in Part 1, Cube, LangChain and a vector database in Part 2. One rule applied six times is a design. Six separate verdicts would be taste.

## What is on these pages, and what is not

The write-up is self-contained: every load-bearing argument is written out here, with no links into working notes. Behind it sits the longer material — one file per decision, reversals included — which stays private on purpose. A reviewer should be reading a design, not its history. Where I changed my mind, the argument that won is here in the present tense; the fact that I once held the other position is not.

Detail that is better handled in conversation is not here either, and costs never run through the prose: each page carries its own marked cost paragraph, and the argument above it stands without the figure.

## How to attack it

Take any component and ask two things: what breaks if it is deleted, and what would have to change — in volume, latency, team size or budget — for the rejected alternative to win instead. Every page is written to answer both, and I would rather be asked.

---

Next: [**Business assumptions**](/intro/02-business-assumptions.md) — what everything else rests on.
