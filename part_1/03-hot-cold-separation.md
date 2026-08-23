# 1.3 — Explain how you separate real-time processing (hot path) from batch archiving/re-processing (cold path)

**The line is drawn at Bronze**, and it is drawn there for one reason: **nothing that can be wrong happens before it.**


|                     | Hot path                                                 | Cold path                                                       |
| ------------------- | -------------------------------------------------------- | --------------------------------------------------------------- |
| **Scope**           | Ingestion only                                           | Everything from Bronze onward                                   |
| **Work**            | Receive, buffer durably, land Bronze and the GCS archive | Silver `MERGE`, Gold rebuild, quality checks, backfills, replay |
| **Latency**         | Seconds                                                  | 30 min / 4h / daily                                             |
| **State held**      | None beyond the buffer                                   | None between runs — the watermark is a value, not a process     |
| **Who operates it** | GCP                                                      | Us, as SQL on a clock                                           |
| **Failure mode**    | Throughput degradation Google handles                    | A run that failed and can be run again                          |


## Why the line sits exactly there

The hot path does **no dedup, no join, no aggregation, no validation**. It is a topic and two export subscriptions, so the only failure available to it is not delivering — which the buffer converts into a delay rather than a loss.

Everything that *can* be wrong is therefore on the cold path: a dedup rule, a currency conversion, a revenue-share join, an aggregate. And on the cold path, being wrong is survivable, because the repair is running the same SQL again.

> **Nobody is on call for the ingestion path**, because nothing of ours runs in it. Pub/Sub receives; two Google-operated subscriptions land Bronze and GCS. The failure mode is throughput degradation Google handles — not a crashed job of ours at 03:00 that stops Bronze until someone restarts it.

## Re-processing has four triggers and one code path

This is the part the separation buys, and the reason the cold path is batch:


| Trigger                                              | Operation                | Mechanism                                                                                                                    |
| ---------------------------------------------------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| A run failed                                         | Rerun                    | The watermark never advanced, so the next scheduled run processes the same pending rows plus the new ones — identically      |
| Data arrives late, within 3 days                     | Rebuild the affected day | Gold rebuilds the days whose Silver rows changed, inside a trailing 3-day window                                             |
| Data older than 3 days, or a backdated revenue share | Targeted rebuild         | The same model, pointed at named past days. **Detected, not noticed** — an alert fires when Silver writes into a partition older than D-3, because Gold's trailing window will not pick it up |
| Bronze itself is wrong, or already purged            | Replay from GCS          | A BigLake external table over the archive prefix, `INSERT … SELECT` into Bronze; everything downstream then reruns unchanged |


**One code path covers steady state and all four repairs.** That equivalence is the claim — not that failures are rare, but that recovering from them uses no special machinery.

## Why not a streaming layer that also computes (lambda)

The textbook separation is a speed layer and a batch layer computing the same metrics, reconciled later. Rejected on two counts:

- **Nobody needs it.** The Yield team reads D-1 — *look at yesterday, act today*. The only intraday consumer is our own team asking *"is data still arriving, has a publisher gone quiet"*, which is a query against Silver.
- **It means two implementations of every metric that must agree.** Any disagreement is a bug in the one place nobody is looking.

## Why not continuous maintenance instead of batch

The serious alternative, and its argument is not latency. It is that a stateful streaming dedup keyed on `event_id` with a 1-hour TTL would delete four mechanisms at once: the watermark, the `MERGE`, the change-detection step, and the orchestrator. Against a design that argues for fewer moving parts, that is a real claim.

**It fails because three repair operations are batch by construction**, and none is optional: backfill beyond the 3-day window, replay from GCS, and restating money after a reference-data correction — a revenue share renegotiated and backdated makes the data *complete and wrong*, so no retry fixes it. Each needs a job that can be pointed at a past day and told to rebuild it. **That job is the batch path.**

So continuous ships two execution models — a streaming one for steady state, a batch one for every repair — where batch ships one that covers both. Its simplicity claim inverts: it deletes nothing and duplicates instead.

*Continuous buys latency nobody asked for, and cannot repair, so it needs the batch path beside it anyway.*

There is also an asymmetry in how the two fail. Continuous losing its dedup state admits duplicates into Silver with nothing downstream able to detect them — **silent wrongness**. Batch fails loudly, and rerunnably.

## What batch costs, stated plainly

Four mechanisms exist only because the work is chopped into runs: a watermark, a `MERGE`, a change-detection step, and an orchestrator. We are keeping all four. The claim is not that they are free — it is that the alternative keeps them too, and adds ~10 GB of live keyed state on top.

## Rejected — one line each


| Option                                       | Why not                                                                                                |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **Lambda (speed layer + batch layer)**       | Two implementations of every metric that must agree, to serve a latency no consumer asked for          |
| **Continuous / streaming maintenance**       | Leaves all three repair paths to be built in batch anyway, and fails silently where batch fails loudly |
| **Validation or enrichment on the hot path** | Moves correctness to the one place where fixing it is a redeploy rather than a rerun                   |
| **A single daily cold-path run**             | A failed run leaves D-1 wrong for 24 hours; the 4-hour cadence means the next run repairs it           |


---

Next: [**2.1 — Medallion data organization**](/part_1/04-medallion-model.md)