# Retention & Anonymisation

> *"Raw logs are kept 7 days. Aggregation anonymises the data."*

Two sentences, two obligations:

1. **7 days is a ceiling on raw, not a budget we chose.** It cannot be extended by paying more, and it binds *every* copy of the raw record — not only the one in BigQuery.
2. **Whatever survives past day 7 must be anonymous.** The aggregation is named as the anonymising step, so the boundary between *raw and deletable* and *durable and anonymous* is a layer in the pipeline, not a policy document.

## One principle, four figures

> **Pay indefinitely for the copy that cannot be recreated. Pay the shortest useful window for every copy that can.**

| Layer | Retention | Recreatable from | Why that figure |
|---|---|---|---|
| **GCS raw archive** | **7 days** | nothing | Ceiling. The rule binds the record, not the store |
| **Bronze** | **7 days** | nothing, past day 7 | Ceiling — and the reprocessing window, now the same number by force |
| **Silver** | **Indefinite** | nothing, past day 7 | Anonymous, therefore allowed to persist. The only remaining record at event grain |
| **Gold** | **Indefinite** | Silver | Aggregated and small, so retention is not a cost question |

**The instinct is that raw is the irreplaceable copy and must therefore be kept longest. Under this rule it is the reverse.** Raw is legally transient, so the irreplaceable copy is the first layer that is *allowed* to persist. Every figure in the table falls out of that one sentence rather than being tuned line by line.

**Why Silver and not Gold**, since Gold is anonymous, aggregated and far smaller:

> **Gold's dimension combinations are fixed at design time. Silver's are not fixed until query time.**

Gold answers *revenue by publisher by hour* because someone chose those dimensions. Ask it for *fill rate by device on one ad unit during a specific incident* and the answer does not exist and cannot be derived — the rows were already collapsed.

## The anonymisation boundary is Silver

Three places could hold it. **Bronze is too early**: Bronze exists to reject nothing and inspect nothing, and stripping fields there means parsing the payload at ingest, which puts back the processing component bullet 1.2 deletes. **Gold is too late**: Silver is retained indefinitely, so an identifier that reaches Silver persists indefinitely.

So the boundary is Silver, and the mechanism is that **the typed schema simply does not have those columns.**

> **A typed schema is an allowlist. A residual payload with PII stripped out is a denylist. Under a deletion obligation, the two failure modes are not comparable.**

An allowlist fails **closed**: a new identifier an SSP starts sending next quarter is not in the mapping, so it is never typed, so it never reaches Silver — and it disappears from Bronze in 7 days. A denylist fails **open**: the same field lands in the residual column, is retained forever, and stays invisible until an audit.

> **An SSP starts sending a new user-level identifier in its payload.** It lands in Bronze, where everything lands, and it is gone at day 7. It never reaches Silver, because nobody added it to the allowlist. **Nobody had to notice it, nobody had to classify it, no filter had to be updated.** An allowlist's worst case is losing a field we wanted. A denylist's worst case is keeping one we were obliged to delete.

**`auction_id` is the case that looks like it breaks this.** It stays in Silver — the five events of one auction cannot be tied together without it — and pseudonymous is not anonymous while a re-linking key exists. **But the re-linking key is Bronze, and it expires.** `auction_id` can point back at a person only while the raw payload holding the identifiers is still there; on day 8 it is a string that groups five rows and joins to nothing. **It does not need to be removed; it needs to stop meaning anything, and the retention rule does that on a schedule.** It is checkable too: the quality job asserts that the distinct-`auction_id` count tracks the auction count, because a value repeating across auctions would make it a session key — the one way this argument fails.

## What we permanently lose

**A field nobody typed is unrecoverable after a week.** Against an indefinite raw archive that would be a query; here it is a wall, and it is the strongest attack available on this design.

It is answered, not waved away. Silver is typed **wide** — every structured non-PII field gets a column whether a metric uses it today or not — and the quality job reports payload keys with no entry in the mapping, so the gap between an SSP sending something new and us typing it is measured in days rather than quarters. *The mitigation is not a mechanism, it is a shorter gap.*

## The consequence that runs through the rest of Part 1

The usual defence of every layer below raw is *"it is recreatable from raw."* Here that sentence is true for seven days and false afterwards.

> **The error budget moved from *we can always rebuild* to *we must be right inside 7 days, and know it*.**

This is why data quality is load-bearing here rather than hygiene, and why the checks run hourly. A check that surfaces a problem on day 3 is a repair; the same check running weekly is an obituary.

**Cost.** Bronze storage at a 7-day window is ~$140/month, against ~$1,600 at 90 days — the constraint that removes the safety net pays for most of the layer kept forever. The GCS archive holds 7 days for ~$210/month, and Silver, indefinite and typed wide, is ~$3,000–4,400/month at five years. **Storage went down and compute went up**; presenting only the saving would be dishonest by omission.

## Rejected — one line each

| Option | Why not |
|---|---|
| **Keep only Gold, drop Silver** | The cheapest answer, and it fixes the analysable dimension combinations at design time. Silver's are fixed at query time |
| **Silver at 13 months** | A bounded window only works if the layer can be rebuilt, and past day 7 there is nothing to rebuild from |
| **A residual JSON column in Silver** | The residual payload *is* the personal data. Keeping it in an indefinitely-retained table is a decision to keep forever the exact bytes the rule requires us to delete in seven days |
| **Strip PII at ingest, in a stream processor** | A denylist enforced by a running process rather than by a table definition — and irreversible in the wrong direction, since a bug destroys data on the only copy |
| **Per-layer retention tuned independently** | Four numbers, four separate justifications, no logic connecting them — exactly the shape a reviewer picks apart |
| **A scheduled purge job** | Partition expiration does the same with no code and no schedule. Under a legal obligation, a deletion that is a table property cannot be quietly paused |

---

Next: [**1.1 — Architecture Diagram**](/part_1/01-architecture-diagram.md)
