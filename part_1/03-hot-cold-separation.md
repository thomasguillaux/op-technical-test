# 1.3 — Hot/Cold Path Separation

*Test bullet: explain how you separate real-time processing (hot path) from batch archiving and re-processing (cold path).*

**The line sits at Bronze, because everything before it can fail and nothing before it can be wrong.** The hot path receives, checks the envelope, buffers durably and lands — no judgement that could be wrong happens there. Everything that could is downstream, where being wrong costs a rerun instead of a redeploy. A speed layer loses on the same ground: an hourly figure cannot exist before its hour ends.

---

|                     | Hot path                                                 | Cold path                                                       |
| ------------------- | -------------------------------------------------------- | --------------------------------------------------------------- |
| **Scope**           | Ingestion only                                           | Everything from Bronze onward                                   |
| **Work**            | Receive, check the envelope, buffer durably, land Bronze and the GCS archive | Silver `MERGE`, Gold rebuild, quality checks, backfills, replay |
| **Latency**         | Seconds                                                  | Silver 30 min · Gold hourly · quality hourly and daily         |
| **Failure mode**    | Slower throughput, which Google handles — or a publish refused synchronously, to the producer | A run that failed and can be run again                          |

## Four triggers, one code path

| Trigger                                              | Operation                | Mechanism                                                                                                                    |
| ---------------------------------------------------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| A run failed                                         | Rerun                    | The watermark never advanced, so the next scheduled run processes the same pending rows plus the new ones, unchanged |
| Data arrives late, within 3 days                     | Rebuild the affected day | Gold rebuilds the days whose Silver rows changed, inside a trailing 3-day window                                             |
| Data older than 3 days, or a backdated revenue share | Targeted rebuild         | The same model, pointed at named past days. *Detected, not noticed:* an alert fires when Silver writes outside Gold's trailing window |
| Bronze itself is wrong, or a partition dropped       | Replay from GCS          | A BigLake external table over the archive prefix, `INSERT … SELECT` into Bronze; one `UPDATE` puts the watermark back behind the replayed rows, and everything downstream then reruns unchanged |

## Why not lambda

An hourly figure cannot exist before the hour it summarises has ended. A speed layer delivering an event in four seconds and a batch tier delivering it in ten minutes produce the same figure at the same moment.

**Cost.** The separation buys no component. Both paths are priced where their components are, in bullets 1.2, 2.1 and 2.2. The priced item is what it avoids: a speed layer means a streaming runtime on the full firehose, low thousands per month.

## Rejected — one line each

| Option                                       | Why not                                                                                                |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **Continuous / streaming maintenance**       | Leaves the reference-data restatement to be built in batch anyway, and fails silently where batch fails loudly |
| **Payload validation or enrichment on the hot path** | Moves correctness to the one place where the fix is a redeploy rather than a rerun. The envelope schema is not this — it refuses a message, it never alters one |
| **A single daily cold-path run**             | A failed run leaves D-1 wrong for 24 hours; on an hourly schedule the next run repairs it unattended   |

---

Next: [**2.1 — Medallion Model**](/part_1/04-medallion-model.md)
