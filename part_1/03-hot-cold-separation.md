# 1.3 — Hot/Cold Path Separation

*Test bullet: explain how you separate real-time processing (hot path) from batch archiving and re-processing (cold path).*

**The line sits at Bronze**, for one reason: **nothing that can be wrong happens before it.**

|                     | Hot path                                                 | Cold path                                                       |
| ------------------- | -------------------------------------------------------- | --------------------------------------------------------------- |
| **Scope**           | Ingestion only                                           | Everything from Bronze onward                                   |
| **Work**            | Receive, buffer durably, land Bronze and the GCS archive | Silver `MERGE`, Gold rebuild, quality checks, backfills, replay |
| **Latency**         | Seconds                                                  | 30 min · hourly · hourly and daily                              |
| **State held**      | None beyond the buffer                                   | None between runs — the watermark is a value, not a process     |
| **Who operates it** | GCP                                                      | Us, as SQL on a clock                                           |
| **Failure mode**    | Slower throughput, which Google handles                  | A run that failed and can be run again                          |
| **Personal data**   | **Lives here, and only here** — 7-day expiration          | None. Silver is the anonymisation boundary                      |

That last row is not decoration. **The hot path is the only place the raw payload exists, so the hot/cold line and the compliance boundary are the same line** — which is why the DDL shows where it sits: Bronze is the only table in the warehouse with an expiration set.

## Why the line sits exactly there

The hot path does **no dedup, no join, no aggregation, no validation**. It is a topic and two export subscriptions, so its only possible failure is not delivering, and the buffer turns that into a delay instead of a loss.

Everything that *can* be wrong is therefore on the cold path: a dedup rule, a currency conversion, a revenue-share join, an aggregate. On the cold path, being wrong is survivable: the repair is running the same SQL again.

> **Nobody is on call for the ingestion path**, because nothing of ours runs in it. Pub/Sub receives; two Google-operated subscriptions land Bronze and GCS. The failure mode is slower throughput, which Google handles, not a job of ours crashing at 03:00 and stopping Bronze until someone restarts it.

## Four triggers, one code path

This is what the separation buys, and the reason the cold path is batch:

| Trigger                                              | Operation                | Mechanism                                                                                                                    |
| ---------------------------------------------------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| A run failed                                         | Rerun                    | The watermark never advanced, so the next scheduled run processes the same pending rows plus the new ones, in exactly the same way |
| Data arrives late, within 3 days                     | Rebuild the affected day | Gold rebuilds the days whose Silver rows changed, inside a trailing 3-day window                                             |
| Data older than 3 days, or a backdated revenue share | Targeted rebuild         | The same model, pointed at named past days. **Detected, not noticed:** an alert fires when Silver writes into a partition older than D-3, because Gold's trailing window will not cover it |
| Bronze itself is wrong, or already purged            | Replay from GCS          | A BigLake external table over the archive prefix, `INSERT … SELECT` into Bronze; everything downstream then reruns unchanged |

**One code path covers steady state and all four repairs.** The claim is not that failures are rare; it is that recovering from them needs no special machinery.

**The fourth trigger now has a deadline.** Replay reaches back seven days and no further, and a repair that must complete inside a week needs a mechanism that is ready, tested and routine — not one built during the incident. **A repair path with a deadline is a stronger reason to own it than one without.**

## Why not lambda

The classic separation is a speed layer and a batch layer computing the same metrics, reconciled later.

- **The hourly requirement does not need it**, because **an hourly figure cannot exist before the hour it summarises has ended.** A speed layer delivering an event in four seconds and a batch tier delivering it in ten minutes produce the *same* figure at the *same* moment. The only other intraday consumer is our own team asking *"is data still arriving"*, which is a query against Silver.
- **It means two implementations of every metric that must agree.** Any disagreement is a bug in the one place nobody is looking.

## Why not continuous maintenance

This is the serious alternative, and its argument is not latency. A stateful streaming dedup keyed on `event_id` with a 1-hour TTL would remove four mechanisms at once — the watermark, the `MERGE`, the change-detection step and the orchestrator. Against a design that argues for fewer moving parts, that is a real claim.

**It fails because three repair operations are batch by nature:** backfill beyond the 3-day window, replay from GCS, and restating money after a reference-data correction. **Two of those got shorter when raw retention dropped to seven days, and a reviewer who spots that is right** — backfill and replay now reach back a week and no further.

**The third is untouched, and it is now the strongest.** A revenue share renegotiated and backdated to the 1st makes every `publisher_payout` for that month wrong on data that is otherwise *complete and healthy*, so no retry and no late-arrival window repairs it. **That repair reads Silver, not raw, so the 7-day rule does not bound it at all** — and Silver is retained indefinitely, so it restates months of history. It is a *"rebuild these named past days"* operation, which a continuous aggregate has no way to express.

One surviving leg is enough, because the conclusion is not *"batch is better on balance"* but ***a batch path must exist regardless***. So the continuous design ships two execution models where batch ships one that covers both; its simplicity argument turns around. And the two fail differently: a continuous design that loses its dedup state admits duplicates nothing downstream can detect — **silent wrongness**, against a batch failure that is loud and rerunnable.

**What batch costs**, stated plainly: a watermark, a `MERGE`, a change-detection step and an orchestrator, all four existing only because the work is split into runs. We keep all four. The claim is not that they are free — the alternative keeps them too, and adds ~10 GB of live keyed state on top.

## Rejected — one line each

| Option                                       | Why not                                                                                                |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **Lambda (speed layer + batch layer)**       | Two implementations of every metric that must agree, to serve a latency the hour boundary already caps  |
| **Continuous / streaming maintenance**       | Leaves the reference-data restatement to be built in batch anyway, and fails silently where batch fails loudly |
| **Validation or enrichment on the hot path** | Moves correctness to the one place where fixing it is a redeploy rather than a rerun                   |
| **A single daily cold-path run**             | A failed run leaves D-1 wrong for 24 hours; on an hourly schedule the next run repairs it unattended   |

---

Next: [**2.1 — Medallion Model**](/part_1/04-medallion-model.md)
