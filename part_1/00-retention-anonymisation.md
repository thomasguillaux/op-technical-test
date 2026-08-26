


**Raw is transient; the irreplaceable copy is the first layer *allowed* to persist.** The instinct runs the other way: raw as the irreplaceable copy, kept longest.

Silver is the source of truth, anonymous and retained indefinitely. Bronze is a landing and replay buffer whose window we do not control.

## The anonymisation boundary is Silver


Bronze is too early: stripping fields there means parsing the payload at ingest, which puts back the processing component bullet 1.2 deletes. Gold is too late: Silver is retained indefinitely, so an identifier that reaches Silver persists indefinitely. That leaves Silver, where the mechanism is that the typed schema does not have those columns — an allowlist, not a filter.

> An SSP starts sending a new user-level identifier in its payload. It lands in Bronze, where everything lands, and it is gone at day 7. It never reaches Silver, because nobody added it to the allowlist — nobody had to notice it, classify it, or update a filter. **An allowlist's worst case is losing a field we wanted. A denylist's worst case is keeping one we were obliged to delete.**

`auction_id` looks like the case that breaks this. It stays in Silver: the events of one auction cannot be tied together without it. Pseudonymous is not anonymous while a re-linking key exists — but the re-linking key is Bronze, and Bronze expires. On day 8, `auction_id` is a string that groups one auction's rows and joins to nothing. **It does not need to be removed; it needs to stop meaning anything, and the retention rule does that on a schedule.** The quality job asserts that the distinct-`auction_id` count tracks the auction count — a value repeating across auctions would make it a session key, the one way this argument fails.

**The honest cost: a field nobody typed is unrecoverable after a week.** With an indefinite raw archive, recovering it would be a query. Here it is unrecoverable. That is the strongest attack available on this design.

## Every copy of the raw record, named


| Copy | Expires by | At |
|---|---|---|
| **Pub/Sub backlog**, and the dead-letter topic with it | subscription retention on both, declared in Terraform — 7 days is also the default, so the control is the review, not the value | 7 days |
| **Bronze table** | `partition_expiration_days` — a table property, not a job that has to run | 7 days |
| **GCS archive** | bucket lifecycle rule, with soft-delete retention set to **0**: the default puts every lifecycle-deleted object in a 7-day holding area behind it | 7 days |
| **Bronze time travel, then fail-safe** | `max_time_travel_hours = 48`, BigQuery's minimum, then a fixed 7-day fail-safe that cannot be configured, queried, or shortened | **day 16** at the earliest |

Three we declare, one we disclose, and beneath the archive one more we switch off. None of the four is a job that has to run.

**The answer to an auditor on the last row is that number, not a denial.** No query of ours can read that residue, no process of ours can pause it, and no request of ours can extend it. It expires on a clock the storage engine runs.

**Cost.** Bronze's 7 days are \~$200/month against \~$2,500 at 90 days. The residue in the last row costs nothing. Bronze bills logically, and logical billing does not charge for time-travel or fail-safe bytes. Bullet 2.2 shows why an expiring table takes that setting. The GCS archive holds the same week for \~$210.

## Rejected — one line each

| Option | Why not |
|---|---|
| **Silver at 13 months** | A bounded window only works if the layer can be rebuilt, and past day 7 there is nothing to rebuild from |
| **A residual JSON column in Silver** | The residual payload *is* the personal data — keeping it in an indefinitely-retained table means keeping forever the exact bytes the rule requires us to delete in seven days |
| **Backlog retention at Pub/Sub's 31-day maximum** | A deeper buffer is a longer-lived copy of the raw record. Replay past day 7 has nothing to replay *into* — Bronze is gone — so the depth breaches the ceiling and buys nothing |
| **Leaving GCS soft delete at its 7-day default** | Turns a 7-day lifecycle rule into a 14-day one, invisibly, on the copy the rule binds hardest |
| **Time travel at BigQuery's 7-day default** | **Five** extra days of queryable raw payload past expiry — pushing the last row from day 16 to day 21 — to protect a table that is immutable and already archived to GCS |

---

