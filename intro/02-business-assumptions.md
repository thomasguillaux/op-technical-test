# Business assumptions

Requirements only, never mechanisms. A line belongs here only if it stays true under a completely different architecture.

|                       | Assumption                                                                                                                             | Source                                                              |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| **Scope**             | Analytics only — no decision loop back into bidding. The Prebid stack is in place.                           | Given                                                               |
| **Volume**            | 2B events/day, \~1.5 TB/day of raw payload.            | Given                                                               |
| **Publishers**        | **Hundreds of publishers, far more ad units.**                                          | Given                                                               |
| **Mix**               | `bid` + `no_bid` are 75-80% of the count. They grow with the number of SSPs invited per auction; every other type happens once per opportunity.               | Derived                                                             |
| **Schema**            | **Payloads differ from one source to the next, and making the schemas converge is an objective of the aggregation.** Nobody is going to make the SSPs agree.        | **Confirmed**                                                       |
| **Payload content**   | **No free text anywhere** — every field is a structured auction attribute: bid value, filled/unfilled, bidders, winner.                | **Confirmed**                                                       |
| **Auction lifecycle** | First bid to final state: **max 1 hour.**                                                                                              | Assumed                                                             |
| **Duplicate arrival** | A retry lands at most **1 hour** after the original. | Assumed                                                             |
| **Freshness**         | Bronze continuous. Silver ≤30 min stale. **Two Gold aggregations: hourly, to watch a release land; daily, to follow trends.** D-1 must always be correct.                     | **Confirmed**                                                       |
| **Retention**         | **Raw logs are kept 7 days. The aggregation anonymises the data.** A ceiling we do not control, binding every copy of the raw record.                                                                  | **Confirmed** |
| **Users**             | \~10 people, all seeing all publishers — **no entitlement scoping, so no row-level security to design.**                                | Given                                                               |
| **Rhythm**            | Two rhythms, not two resolutions of one need. *Look at yesterday, act today* is trend work. *Ship, then watch* is episodic: nobody stares at an hourly chart, but on a deploy day the closed hour is read within minutes.                                         | Derived                                                               |

**The retention answer is the one that reaches furthest.** Raw data is transient, so the durable record is the anonymised event layer — and the error budget moved from *we can always rebuild* to *we must be right inside 7 days, and know it*. That is [the first page of Part 1](/part_1/00-retention-anonymisation.md).

**The two timing bounds still come from a conversation, not a measurement.** Every window in the design derives from that 1-hour figure, so the pipeline measures it, per hour and per publisher. The answer to *"what if lateness is worse than you assumed?"* is **"we would know, and here is the metric."**

---

Next: [**Part 1 — High-Volume Data Pipeline (GCP)**](/part1-pipeline.md)
