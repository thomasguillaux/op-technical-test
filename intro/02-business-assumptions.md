# Business assumptions

Requirements only, never mechanisms. A line belongs here only if it stays true under a completely different architecture.


|                       | Assumption                                                                                                                                                   | Source        |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------- |
| **Scope**             | Analytics only — no decision loop back into bidding. The Prebid stack is in place.                                                                           | Given         |
| **Volume**            | 2B events/day, 1.5 TB/day of raw payload.                                                                                                                    | Given         |
| **Publishers**        | Hundreds of publishers, far more ad units.                                                                                                                   | Given         |
| **Schema**            | **Payloads differ from one source to the next, and making the schemas converge is an objective of the aggregation.** Nobody is going to make the SSPs agree. | **Confirmed** |
| **Payload content**   | **No free text anywhere** — every field is a structured auction attribute: bid value, filled/unfilled, bidders, winner.                                      | **Confirmed** |
| **Auction lifecycle** | First bid to final state: **max 1 hour.**                                                                                                                    | Assumed       |
| **Duplicate arrival** | A retry lands at most **1 hour** after the original.                                                                                                         | Assumed       |
| **Freshness**         | Two Gold aggregations: hourly, to watch a release land; daily, to follow trends. D-1 must always be correct.                                             | **Confirmed** |
| **Retention**         | **Raw logs are kept 7 days. The aggregation anonymises the data.** A ceiling we do not control, binding every copy of the raw record.                        | **Confirmed** |
| **Users**             | 10 people, all seeing all publishers — **no entitlement scoping, so no row-level security to design.**                                                       | Given         |
| **Rhythm**            | Two rhythms, not two resolutions of one need. *Look at yesterday, act today* is trend work. *Ship, then watch* is episodic: nobody stares at an hourly chart, but on a deploy day the closed hour is read within minutes. | Derived       |


**Retention is the assumption that constrains the most decisions downstream.** Raw data is transient, so the durable record is the anonymised event layer, and the error budget is *we must be right inside 7 days, and know it* rather than *we can always rebuild*. See [the anonymisation boundary in 2.1](/part_1/04-medallion-model.md).

---

Next: [**1.1 — Architecture Diagram**](/part_1/01-architecture-diagram.md)