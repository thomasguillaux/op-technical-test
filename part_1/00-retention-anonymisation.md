# Retention & Anonymisation

> *"Raw logs are kept 7 days. Aggregation anonymises the data."*

Not a test bullet — one client rule that reshapes six of the answers below. 7 days is a ceiling, and it binds every *copy* of the raw record rather than the one in BigQuery. Whatever outlives it must be anonymous, and aggregation is named as the anonymising step, so the line between *deletable* and *durable* is a layer in the pipeline rather than a policy document.

**The instinct is that raw is the irreplaceable copy and must be kept longest. Under this rule it is the reverse:** raw is legally transient, so the irreplaceable copy is the first layer *allowed* to persist. **Which means the medallion convention — Bronze is the source of truth — does not hold here.** Silver is the source of truth, anonymous and retained indefinitely; Bronze is a landing and replay buffer whose window is set by law rather than by us.

## The anonymisation boundary is Silver

Bronze is too early: stripping fields there means parsing the payload at ingest, which puts back the processing component bullet 1.2 deletes. Gold is too late: Silver is retained indefinitely, so an identifier that reaches Silver persists indefinitely. That leaves Silver, where the mechanism is that the typed schema does not have those columns — an allowlist, not a filter.

> An SSP starts sending a new user-level identifier in its payload. It lands in Bronze, where everything lands, and it is gone at day 7. It never reaches Silver, because nobody added it to the allowlist — nobody had to notice it, classify it, or update a filter. **An allowlist's worst case is losing a field we wanted. A denylist's worst case is keeping one we were obliged to delete.**

`auction_id` looks like the case that breaks this. It stays in Silver — the five events of one auction cannot be tied together without it — and pseudonymous is not anonymous while a re-linking key exists. But the re-linking key is Bronze, and Bronze expires: on day 8, `auction_id` is a string that groups five rows and joins to nothing. **It does not need to be removed; it needs to stop meaning anything, and the retention rule does that on a schedule.** The quality job asserts that the distinct-`auction_id` count tracks the auction count — a value repeating across auctions would make it a session key, the one way this argument fails.

**The honest cost: a field nobody typed is unrecoverable after a week.** Against an indefinite raw archive that would be a query; here it is a wall, and the strongest attack available on this design.

## Every copy of the raw record, named

The rule binds the record, not the store. Two of these are not layers, and the last one is not ours.

| Copy | Expires by | At |
|---|---|---|
| **Pub/Sub backlog**, and the dead-letter topic with it | subscription retention on both, declared in Terraform — 7 days is also the default, so the control is the review, not the value | 7 days |
| **Bronze table** | `partition_expiration_days` — a table property, not a job that has to run | 7 days |
| **GCS archive** | bucket lifecycle rule, with soft-delete retention set to **0**: the default puts every lifecycle-deleted object in a 7-day holding area behind it | 7 days |
| **Bronze time travel, then fail-safe** | `max_time_travel_hours = 48`, BigQuery's minimum, then a fixed 7-day fail-safe that cannot be configured, queried, or shortened | **day 16** at the earliest |

Three we declare, one we disclose, and beneath the archive one more we switch off — and not one of them a job that has to run. **The answer to an auditor on the last row is that number, not a denial**: a residue no query of ours can read, no process of ours can pause, and no request of ours can extend, expiring on a clock the storage engine runs. Naming it is also the only way to be *sure* it expires — a design that claims day 7 has no reason to check what happens on day 8.

**Cost.** Bronze's 7 days are \~$200/month against \~$2,500 at 90 days. The residue in the last row costs nothing, because Bronze bills logically and logical billing does not charge for time-travel or fail-safe bytes — bullet 2.2 shows why an expiring table takes that setting. The GCS archive holds the same week for \~$210. **The copy nobody chose to keep still has to be disclosed, even when it is free.**

## Rejected — one line each

| Option | Why not |
|---|---|
| **Keep only Gold, drop Silver** | The cheapest answer, and it fixes the analysable dimension combinations at design time — ask Gold for *fill rate by device on one ad unit during a specific incident* and the rows were already collapsed. Silver's are fixed at query time |
| **Silver at 13 months** | A bounded window only works if the layer can be rebuilt, and past day 7 there is nothing to rebuild from |
| **A residual JSON column in Silver** | The residual payload *is* the personal data — keeping it in an indefinitely-retained table means keeping forever the exact bytes the rule requires us to delete in seven days |
| **Backlog retention at Pub/Sub's 31-day maximum** | A deeper buffer is a longer-lived copy of the raw record. Replay past day 7 has nothing to replay *into* — Bronze is gone — so the depth breaches the ceiling and buys nothing |
| **Leaving GCS soft delete at its 7-day default** | Turns a 7-day lifecycle rule into a 14-day one, invisibly, on the copy the rule binds hardest |
| **Time travel at BigQuery's 7-day default** | **Five** extra days of queryable raw payload past expiry — pushing the last row from day 16 to day 21 — to protect a table that is immutable and already archived to GCS |

---

Next: [**1.1 — Architecture Diagram**](/part_1/01-architecture-diagram.md)
