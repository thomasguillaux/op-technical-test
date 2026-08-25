# 1.3 — Hot/Cold Path Separation

*Test bullet: explain how you separate real-time processing (hot path) from batch archiving and re-processing (cold path).*

The test's phrase is *real-time processing*. There is none of ours: the hot path receives and buffers; every processing step — dedup, typing, joins, aggregation — sits on the cold side of the line.

The line sits at Bronze, for one reason: **everything before it can fail, and nothing before it can be wrong.**

|                     | Hot path                                                 | Cold path                                                       |
| ------------------- | -------------------------------------------------------- | --------------------------------------------------------------- |
| **Scope**           | Ingestion only                                           | Everything from Bronze onward                                   |
| **Work**            | Receive, check the envelope, buffer durably, land Bronze and the GCS archive | Silver `MERGE`, Gold rebuild, quality checks, backfills, replay |
| **Latency**         | Seconds                                                  | 30 min · hourly · hourly and daily                              |
| **State held**      | None beyond the buffer                                   | None between runs — the watermark is a value, not a process     |
| **Who operates it** | GCP                                                      | Us, as SQL on a clock                                           |
| **Failure mode**    | Slower throughput, which Google handles — or a publish refused synchronously, to the producer | A run that failed and can be run again                          |
| **Personal data**   | Lives here, and only here — 7-day expiration             | None. Silver is the anonymisation boundary                      |

The raw payload exists only on the hot path, so the hot/cold line is also the compliance boundary: Bronze is the only table in the warehouse with an expiration set.

*Batch archiving* is the other half of the test's phrase, and it is not batch either: the archive is a second export subscription writing as events arrive, on the hot path — only reading it back is cold.

The hot path does **no dedup, no join, no aggregation, no cast** — a topic, its envelope schema, and two export subscriptions. A `CAST`, a currency conversion or a revenue-share join can each produce a number that is plausible, different from the truth, and reported by nobody; a schema check produces an error or it produces nothing. The line is not drawn on the absence of work before Bronze — it is drawn on the absence of *quiet* work, so everything that *can* be wrong sits on the cold path, where the repair is running the same SQL again. The envelope is the five named fields the topic schema declares, never the payload beneath them, and the buffer is what makes the other half true: the only failure available before Bronze is not delivering, and a durable subscription turns that into a delay rather than a loss.

> Nobody is on call for the ingestion path, because nothing of ours runs in it. The failure mode is slower throughput, which Google handles — not a job of ours crashing at 03:00 and stopping Bronze until someone restarts it.

## Four triggers, one code path

| Trigger                                              | Operation                | Mechanism                                                                                                                    |
| ---------------------------------------------------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| A run failed                                         | Rerun                    | The watermark never advanced, so the next scheduled run processes the same pending rows plus the new ones, unchanged |
| Data arrives late, within 3 days                     | Rebuild the affected day | Gold rebuilds the days whose Silver rows changed, inside a trailing 3-day window                                             |
| Data older than 3 days, or a backdated revenue share | Targeted rebuild         | The same model, pointed at named past days. *Detected, not noticed:* an alert fires when Silver writes outside Gold's trailing window |
| Bronze itself is wrong, or a partition dropped       | Replay from GCS          | A BigLake external table over the archive prefix, `INSERT … SELECT` into Bronze; everything downstream then reruns unchanged |

**One code path covers steady state and all four repairs** — not because failures are rare, but because recovering from them needs no special machinery.

## Why not lambda

An hourly figure cannot exist before the hour it summarises has ended: a speed layer delivering an event in four seconds and a batch tier delivering it in ten minutes produce the same figure at the same moment. The only intraday consumer is our own team asking *"is data still arriving"* — a query against Silver. What the speed layer costs is two implementations of every metric that must agree, and any disagreement is a bug in the one place nobody is looking.

## Why not continuous maintenance

The serious alternative, and its argument is not latency: a stateful streaming dedup keyed on `event_id` with a 1-hour TTL removes the watermark, the `MERGE`, the change-detection step and the orchestrator at once.

It fails on one repair, and one is enough. A revenue share renegotiated and backdated to the 1st makes every `publisher_payout` for that month wrong on data that is otherwise complete and healthy, so no retry and no late-arrival window touches it. **That repair reads Silver, not raw, so the 7-day rule does not bound it** — and Silver is retained indefinitely, so it restates months of history. It is a *"rebuild these named past days"* operation, which a continuous aggregate cannot express. So a batch path must exist regardless, and the continuous design ships two execution models where batch ships one: it keeps the watermark, the `MERGE`, the change detection and the orchestrator anyway, and adds \~10 GB of live keyed state on top. **The simplicity argument turns around.**

**Cost.** The separation is a line drawn, not a component bought — both paths are priced where their components are, in bullets 1.2, 2.1 and 2.2. What it *avoids* is the priced item: a speed layer means a streaming runtime on the full firehose, low thousands per month, to deliver an hourly figure the hour boundary already caps — and that is the smaller half of the bill, next to a second implementation of every metric.

## Rejected — one line each

| Option                                       | Why not                                                                                                |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **Lambda (speed layer + batch layer)**       | Two implementations of every metric that must agree, to serve a latency the hour boundary already caps  |
| **Continuous / streaming maintenance**       | Leaves the reference-data restatement to be built in batch anyway, and fails silently where batch fails loudly |
| **Payload validation or enrichment on the hot path** | Moves correctness to the one place where the fix is a redeploy rather than a rerun. The envelope schema is not this — it refuses a message, it never alters one |
| **A single daily cold-path run**             | A failed run leaves D-1 wrong for 24 hours; on an hourly schedule the next run repairs it unattended   |

---

Next: [**2.1 — Medallion Model**](/part_1/04-medallion-model.md)
