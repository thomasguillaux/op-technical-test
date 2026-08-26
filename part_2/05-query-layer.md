# 3.1 — Gold, Through Its Views Only

*Test bullet: on which BigQuery layer (Bronze, Silver, or Gold) should the LLM agent execute its generated SQL queries? Why?*

**Gold.** It is the only layer where a question has an answer, a definition, and a published verdict on whether that answer is trustworthy.




## The mechanism: authorized datasets


BigQuery's authorized datasets close it. The semantic dataset is authorized on the Gold dataset, so the views can read the base tables while the caller cannot — per Google's documentation, *"to query a view in an authorized dataset, a user needs to have access to the view, but access to the shared dataset is not required."* The authorization names the dataset, not its views: a view added tomorrow needs no grant of its own.

**The grant in full, because it is checkable:** `roles/bigquery.jobUser` on the project — a query job needs `bigquery.jobs.create` wherever the data lives — and `roles/bigquery.dataViewer` on the semantic dataset alone. **No grant on Bronze, Silver or the Gold base tables exists anywhere for this service account.**


## The same question, priced at three layers


| Executed against | What one publisher-slice question scans | Order |
|---|---|---|
| **The semantic views** | One publisher's slice of two daily Gold partitions — a few million rows/day on `gold_opportunity`, ten million on `gold_ssp` | **cents, or fractions of one** |
| **Bronze** | A read across the full 7-day window, ~10.5 TB logical | **~$60** |
| **Silver** | Nothing expires, so this figure has no ceiling — hundreds of TB at five years | **thousands, on a table larger every month** |

**So the layer choice is the largest cost control in Part 2, and it is not a guardrail — it is an IAM grant.** A design that leaves the agent on Silver and defends the bill with query-time limits is paying attention to the query that goes wrong and none to the thousands that go right.

**Cost.** A logical view stores no bytes and adds none to a scan — it is expanded into the referencing query, so the reader pays for the partitions the base table would have charged for anyway.

## Rejected — one line each

| Option | Why not |
|---|---|
| **A copied read-only dataset for the agent** | A second physical copy of Gold to solve an access problem that a view and an authorized dataset solve with no bytes |
| **Row-level security** | Around ten users, all of whom see every publisher, with no entitlement scoping |

---

Next: [**3.2 — Guardrails**](/part_2/06-guardrails.md)
