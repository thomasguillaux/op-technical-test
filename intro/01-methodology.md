# Methodology

> **Every component in this design survived an argument for deleting it.**
> Several components named in the test did not.

*This repository is public, so the company is called **OptimusAds** here and publisher names and identifiers are anonymized. Nothing else is changed.*

## Requirements are the input; components are the output

Drawing the five boxes named in the test and connecting them gives an architecture nobody can defend: no component ever had to justify itself. So most sections end with a **Rejected** table. Where a named component is missing, that table gives the reason it lost and the condition that would bring it back. The option that lost says more than the option that won, and it is the part a reviewer can test.

## How it was built

Built with Claude Code (Opus and Sonnet), driven by Matt Pocock's skills:

- **`wayfinder`** — map the whole scope as decisions before making any of them.
- **`grill-with-docs`** — attack each decision, then record it with the argument that survived.
- **`domain-modeling`** — keep the vocabulary honest as it moves.

**The model's job was to argue; mine was to decide.** Several choices here went against its recommendation.

---

Next: [**Business assumptions**](/intro/02-business-assumptions.md) — what everything else rests on.
