# Methodology

## Requirements are the input; components are the output

Each decision starts from a requirement and takes the smallest component that satisfies it. The question each component has to survive is *could we meet every requirement without it* — if we could, it does not go in. It is asked before anything is wired together, because a component already in place always looks load-bearing. Components named in the test are not assumed: drawing the boxes the test lists and connecting them would produce an architecture in which no component ever had to justify itself.

That is why most sections end with a **Rejected** table. Where a component named in the test is absent, the table gives the reason it lost *and* the condition that brings it back — the condition is the load-bearing half, because "no Dataflow" is a claim about this volume and this latency, not about Dataflow.

## Three rules, applied to every decision

**Map the decisions before making any of them.** I listed the scope as a dozen open questions — retention, the hot/cold line, the Gold grain, the agent's blast radius — before settling any of them, so that no early choice silently decided a later one.

**Check the figures against primary sources.** Every number that carries an argument — the partition-grain delta, the streaming rates, the 7-day retention arithmetic — comes from vendor documentation rather than recollection.

**Record the argument, not the conclusion.** A conclusion alone cannot be defended when challenged. Each decision is kept with the requirement it satisfies and the alternative it beats; the Rejected tables are the compressed form of exactly that.

## What is on these pages, and what is not

Every page opens with its claim in one bold sentence, then a rule, then the argument. The openers alone state the design.

Costs never run through the prose: each page carries its own marked cost paragraph, and the argument above it stands without the figure.

---

Next: [**Business assumptions**](/intro/02-business-assumptions.md) — what everything else rests on.
