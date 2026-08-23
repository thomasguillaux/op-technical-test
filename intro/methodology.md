# Methodology

> **Every component in this design survived an argument for its own deletion.**
> Several the test names did not.

*The company is referred to as **OptimusAds** throughout, and publisher names and identifiers are anonymized on the same basis, because this write-up lives in a public repository. Nothing else is altered.*

## Requirements are the input; components are the output

Drawing the five boxes the test names and connecting them produces an architecture nobody can defend, because nothing was ever asked to justify itself. Where a named component is missing, the reason it lost and the condition that would bring it back are recorded — which is why most sections carry a **Rejected** table. The alternative that lost is more informative than the option that won, and it is the part a reviewer can actually test.

## How it was built

Built with Claude Code (Opus and Sonnet), driven by Matt Pocock's skills:

- **`wayfinder`** — map the whole scope as decisions before making any of them.
- **`grill-with-docs`** — attack each decision, then record it with the argument that survived.
- **`domain-modeling`** — keep the vocabulary honest as it moves.

**The model's job was to argue; mine was to decide.** Several choices here went against its recommendation.

---

Next: [**Business assumptions**](/intro/business-assumptions.md) — what everything else rests on.
