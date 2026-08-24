# 1.3 — Hot/Cold Path Separation

*Test bullet: explain how you separate real-time processing (hot path) from batch archiving and re-processing (cold path).*

The test's phrase is *real-time processing*. The answer here is that there is none of ours: the hot path receives and buffers, and every processing step — dedup, typing, joins, aggregation — sits on the cold side of the line.

The line sits at Bronze, for one reason: **nothing that can be wrong happens before it.**

|                     | Hot path                                                 | Cold path                                                       |
| ------------------- | -------------------------------------------------------- | --------------------------------------------------------------- |
| **Scope**           | Ingestion only                                           | Everything from Bronze onward                                   |
| **Work**            | Receive, buffer durably, land Bronze and the GCS archive | Silver `MERGE`, Gold rebuild, quality checks, backfills, replay |
| **Latency**         | Seconds                                                  | 30 min · hourly · hourly and daily                              |
| **State held**      | None beyond the buffer                                   | None between runs — the watermark is a value, not a process     |
| **Who operates it** | GCP                                                      | Us, as SQL on a clock                                           |
| **Failure mode**    | Slower throughput, which Google handles                  | A run that failed and can be run again                          |
| **Personal data**   | Lives here, and only here — 7-day expiration             | None. Silver is the anonymisation boundary                      |

The raw payload exists only on the hot path, so the hot/cold line and the compliance boundary are the same line: Bronze is the only table in the warehouse with an expiration set.

## Why the line sits exactly there

The hot path does **no dedup, no join, no aggregation, no validation** — a topic and two export subscriptions. Its only possible failure is not delivering, and the buffer turns that into a delay, not a loss.

Everything that *can* be wrong is therefore on the cold path — a dedup rule, a currency conversion, a revenue-share join, an aggregate — where being wrong is survivable: the repair is running the same SQL again.

> Nobody is on call for the ingestion path, because nothing of ours runs in it. Pub/Sub receives; two Google-operated subscriptions land Bronze and GCS. The failure mode is slower throughput, which Google handles — not a job of ours crashing at 03:00 and stopping Bronze until someone restarts it.

## Four triggers, one code path

What the separation buys, and why the cold path is batch:

| Trigger                                              | Operation                | Mechanism                                                                                                                    |
| ---------------------------------------------------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| A run failed                                         | Rerun                    | The watermark never advanced, so the next scheduled run processes the same pending rows plus the new ones, unchanged |
| Data arrives late, within 3 days                     | Rebuild the affected day | Gold rebuilds the days whose Silver rows changed, inside a trailing 3-day window                                             |
| Data older than 3 days, or a backdated revenue share | Targeted rebuild         | The same model, pointed at named past days. *Detected, not noticed:* an alert fires when Silver writes into a partition older than D-3, which Gold's trailing window does not cover |
| Bronze itself is wrong, or already purged            | Replay from GCS          | A BigLake external table over the archive prefix, `INSERT … SELECT` into Bronze; everything downstream then reruns unchanged |

**One code path covers steady state and all four repairs** — not because failures are rare, but because recovering from them needs no special machinery.

## Why not lambda

The classic separation is a speed layer and a batch layer computing the same metrics, reconciled later.

- **An hourly figure cannot exist before the hour it summarises has ended.** A speed layer delivering an event in four seconds and a batch tier delivering it in ten minutes produce the same figure at the same moment. The only other intraday consumer is our own team asking *"is data still arriving"* — a query against Silver.
- It costs two implementations of every metric that must agree, and any disagreement is a bug in the one place nobody is looking.

## Why not continuous maintenance

The serious alternative, and its argument is not latency: a stateful streaming dedup keyed on `event_id` with a 1-hour TTL removes the watermark, the `MERGE`, the change-detection step and the orchestrator at once.

It fails because three repairs are batch by nature: backfill beyond the 3-day window, replay from GCS, and restating money after a reference-data correction. The first two are bounded by raw retention, seven days and no further.

The third is not. A revenue share renegotiated and backdated to the 1st makes every `publisher_payout` for that month wrong on data that is otherwise complete and healthy, so no retry and no late-arrival window repairs it. **That repair reads Silver, not raw, so the 7-day rule does not bound it** — and Silver is retained indefinitely, so it restates months of history. It is a *"rebuild these named past days"* operation, which a continuous aggregate cannot express.

One leg is enough, because the conclusion is not *"batch is better on balance"* but that a batch path must exist regardless. So the continuous design ships two execution models where batch ships one that covers both: it keeps the watermark, the `MERGE`, the change detection and the orchestrator anyway, and adds \~10 GB of live keyed state on top. The simplicity argument turns around.

It also fails quietly: a continuous design that loses its dedup state admits duplicates nothing downstream can detect, where a batch failure is loud and rerunnable.

## Rejected — one line each

| Option                                       | Why not                                                                                                |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **Lambda (speed layer + batch layer)**       | Two implementations of every metric that must agree, to serve a latency the hour boundary already caps  |
| **Continuous / streaming maintenance**       | Leaves the reference-data restatement to be built in batch anyway, and fails silently where batch fails loudly |
| **Validation or enrichment on the hot path** | Moves correctness to the one place where fixing it is a redeploy rather than a rerun                   |
| **A single daily cold-path run**             | A failed run leaves D-1 wrong for 24 hours; on an hourly schedule the next run repairs it unattended   |

---

Next: [**2.1 — Medallion Model**](/part_1/04-medallion-model.md)
