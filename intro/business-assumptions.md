# Business assumptions

Requirements only, never mechanisms: a line qualifies only if it would still be true under a completely different architecture.

|                       | Assumption                                                                                                                             | Source                                                              |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| **Scope**             | Analytics only — no decisioning loop back into bidding. The Prebid stack exists; payloads are heterogeneous.                           | Given                                                               |
| **Volume**            | 2B events/day, ~800 B each — ~1.5 TB/day, ~40 TB per 90-day window.                                                                    | Given                                                               |
| **Mix**               | `bid` + `no_bid` are 75-80% of count: they scale with SSPs invited per auction, every other type is one per opportunity.               | Derived                                                             |
| **Auction lifecycle** | First bid to final state: **max 1 hour.**                                                                                              | Assumed                                                             |
| **Duplicate arrival** | A retry lands at most **1 hour** after the original — deliberately the same bound, since both answer *"how far back must a run look"*. | Assumed                                                             |
| **Freshness**         | Bronze continuous. Silver ≤30 min stale. Gold has **no intraday requirement**, but **D-1 must always be correct.**                     | Given                                                               |
| **Retention**         | Bronze 90 days · Silver ~13 months · Gold and raw archive indefinite.                                                                  | **Assumed** — no requirement stated, no regulatory constraint known |
| **Users**             | ~10 people, all seeing all publishers — **no entitlement scoping, so no row-level security to design.**                                | Given                                                               |
| **Rhythm**            | *Look at yesterday, act today.* Dashboards are D-1; nobody watches the current day accumulate.                                         | Given                                                               |

**The two bounds everything rests on came from a conversation, not a measurement.** Every window in the design descends from that 1-hour figure, so the pipeline measures it — per day and per publisher. The answer to *"what if lateness is worse than you assumed?"* is **"we would know, and here is the metric."**

---

Next: [**Part 1 — High-Volume Data Pipeline (GCP)**](/part1-pipeline.md)
