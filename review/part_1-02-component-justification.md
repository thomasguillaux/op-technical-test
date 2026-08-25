# Review — `part_1/02-component-justification.md`

## Summary

The riskiest page in Part 1: it takes the five components the test names, keeps three, and deletes Dataflow and Composer with a reinstate condition attached to each, then adds Dataform and a Cloud Logging → Monitoring alert path the test did not ask for. It lands — the verdict table answers the bullet literally before diverging, the operational reasoning is genuinely senior, and the GCS storage-class arithmetic is correct — but one rejected alternative is conceded as "cheaper" when at list price it is not, and the Dataflow argument rests on a binary that has a third option the design already uses elsewhere.

## Grade

- **Decision quality — A.** Eight rejected options, each with a reason, two with a condition that reinstates them; cost is explicitly disqualified as the decider on the Dataflow call, which is what a senior engineer does and a junior one never does.
- **Narrative — B.** Verdict table → the one sentence that kills three components → depth only on the two contested ones is the right shape, but the GCS storage-class section is parachuted between the verdict and the Dataflow argument, spending the page's most precise arithmetic on its smallest decision at the moment the reader is waiting for the big one.
- **Operability instinct — A.** The Dataform gap table (no retry, skipped overlapping runs, nothing outside BigQuery) names three real product limits and answers each with a mechanism, and the "a skip emits no failure log, which is why the watermark-age monitor exists" link is the sentence that shows this was thought about rather than looked up.
- **Technical plausibility — B.** The numbers I can check hold up — 2B/day ÷ 86,400 ≈ 23k/s; 365 × 1.5 TB ≈ 547 TB billed × $0.0012 ≈ $657 against 10.5 TB × $0.020 = $210, a 3.1× inversion; $40 + $50 + $50 = $140/TiB for two export subscriptions against $40 + $40 + $25 ≈ $105/TiB for a standard subscription plus the Storage Write API — but the Pub/Sub-retention row runs the wrong way and the BigLake row is dated.
- **Signal density — B.** Almost every line carries argument; three passages are third or second statements of something the reader already has (the six-components sentence, the Cloud Logging justification, Dataform's API as an escape hatch).
- **Overall — B.** This survives the "you didn't answer the question" reading comfortably and would be interesting to interview on; what keeps it off A is one costed claim that runs backwards and one unexamined binary.

## Top findings

**1. [BLOCKER] "Pub/Sub retention alone, no GCS copy — the genuine cheaper alternative" is not cheaper, and the page concedes it without a number.**
- **What:** Retained messages are billed at roughly $0.27/GiB-month against Standard GCS at $0.020/GB-month — about 13× per byte — so holding the same 7 days (≈10 TiB) in topic retention costs on the order of $2,600/month against $2,310 for the archive subscription plus its storage; the page rejects the option on inspectability instead, and its supporting clause ("a replay is a re-ingest, so you cannot look at it without spending it") is loose, since a scratch subscription can seek back through topic retention without consuming it.
- **Why it matters to the evaluator:** The page has just demonstrated, with a table, that it checks storage unit economics before choosing a class — then hands the one genuinely competing alternative a cost advantage it does not have, on the same page, unpriced.
- **Fix:** Replace the row with the arithmetic: "Pub/Sub retained storage is ~$0.27/GiB-month against GCS Standard's $0.020 — the same week costs more, and it is not queryable: no SQL, no partition pruning, no point lookup, only a pull."

**2. [QUESTION] The Dataflow argument is posed as a binary — producer supplies the split, or Dataflow — when the design's own idiom offers a third option it never names.**
- **What:** 2.3 already maps fields per source with a `CASE` over `payload`, so the five envelope values could equally be extracted in Silver with no producer change and no Dataflow; the reason they cannot is that Bronze clusters on `publisher_id, ssp_id, event_type` and the topic schema refuses a broken envelope at publish, neither of which works if the fields live inside the JSON — and that reason is nowhere on the page.
- **Why it matters to the evaluator:** As written, the page trades a runtime it controls for a hard dependency on a third party's roadmap and does not show it considered the option that needs neither; a staff engineer finds this in thirty seconds and it reads as the one place the "delete the component" rule was applied without checking.
- **Fix:** Add one sentence to the reinstate paragraph: "Extracting the five fields in Silver instead needs no producer change and no Dataflow — but Bronze then has nothing to cluster on and the envelope check moves from publish time to 30 minutes later, which is bullet 2.2's argument, not this one."

**3. [QUESTION] Composer's reinstate condition is a mechanism, not a trigger — the opposite of Dataflow's.**
- **What:** Dataflow comes back on a testable event ("the producer refuses to emit the split"); Composer's condition is "a genuinely mixed step later", which names no observable, while the Rejected row offers only *how* it would be added (the Dataform API), not *when*.
- **Why it matters to the evaluator:** The methodology page claims the reinstate condition is the load-bearing half because it is the part a reviewer can test; one of the two conditions on this page is untestable, and it is the one attached to the component the test named.
- **Fix:** Convert the negation already in the prose into the trigger: "Composer arrives the first time a step waits on something outside BigQuery — a vendor API, a file that must exist, a cross-system dependency — not on model count."

**4. [QUESTION] 23k events/second is a daily mean presented as a capacity figure, and the strongest argument for the native subscription goes unmade.**
- **What:** 2B/day ÷ 86,400 is arithmetically right but auction traffic is diurnal, so the real design point is a peak two to three times that; nothing on the page says the native subscription absorbs it without anyone sizing a worker pool, which is precisely where a streaming Dataflow job would cost on-call attention.
- **Why it matters to the evaluator:** An interviewer reads a bare 23k/s as a candidate who divided by 86,400, and the correct answer — that peak is where "no ingestion job of ours" pays off most — is an argument the page is entitled to and does not take.
- **Fix:** "~23k/s average, and a diurnal peak two to three times that which nobody has to provision for: a subscription has no worker pool to size, where a streaming job's autoscaler is a thing we tune and get paged by."

**5. [QUESTION] The two most expensive rejections on the page carry no figure, while the cheapest decision gets a table.**
- **What:** Composer is rejected on "billed continuously whether a DAG fires or not" with no monthly number, and Dataflow on costs that "overlap across the range" with no bracket, while a ~$450/month storage-class choice gets three rows, four columns and a paragraph.
- **Why it matters to the evaluator:** A CTO reading a component-justification page wants the price of the components being deleted; leaving the smallest number as the most precise one on the page reads as pricing what was easy to price.
- **Fix:** One clause each — the smallest usable Composer environment's monthly floor, and the Dataflow compute band that makes $105/TiB plus compute meet $140/TiB — and compress the storage table to buy the room.

## Cuts

**1. "Six components lost to the same sentence…" (~50 words).** This is its third appearance: `intro/01-methodology.md`, `part1-pipeline.md`, and here. This page is where the sentence is actually *earned* — three of the six die on it — so the deletion belongs upstream, but as the reader arrives having read it twice, compress to the payoff only: "The same sentence deletes dbt Core below, and three more components in Part 2." **~35 words saved**, nothing lost but the second restatement of the rule.

**2. The Cloud Logging justification, "which exists for one reason — Dataform logs every workflow invocation and notifies no one" (~18 words).** Verbatim in substance from `01-architecture-diagram.md`, one page back and one click away. Name the component in the sentence above and let the previous page keep the reason. **~18 words.**

**3. Prose restating the storage table (~40 words).** The paragraph under the table re-reads the Archive row's minimum duration and price back to the reader before doing the arithmetic. Keep the arithmetic and the transferable rule ("a minimum-duration clause inverts cold-tier economics whenever retention is shorter than the minimum" — the best line in the section); drop the re-reading. Alternatively cut the Nearline row, which the argument never uses. **~40 words.**

**4. "Dataform exposes an API, so a genuinely mixed step later means adding Composer in front of it" (~20 words).** Said twice — here and in the Composer row of the Rejected table. Keep it in the Rejected table, where finding 3 wants it turned into a trigger anyway. **~20 words.**

## Interview questions this page invites

1. **"Why does the split have to happen before Bronze at all? You map fields per source in Silver anyway."** *Not answered on this page.* The answer exists in 2.2 (Bronze's cluster keys) and in 1.1 (publish-time envelope validation) but is never joined up here, which is why the Dataflow argument reads as a binary. This is finding 2 as it will actually be asked.
2. **"A BigQuery subscription is at-least-once and its write failures dead-letter silently — what does that cost you?"** *Answered elsewhere, muddied here.* 2.3's `MERGE` and 1.1's dead-letter monitor cover it, but this page's "plus the at-least-once handling the native subscription does for us" reads, to anyone who knows the delivery semantics, as a claim that the subscription solves duplicates rather than causes them. One word ("the ack, retry and redelivery handling") removes the misread.
3. **"Dataform has no retry and skips a run when the previous is still going — what happens if Silver starts taking 45 minutes on a 30-minute schedule?"** *Half answered.* The page covers one skip ("60 minutes instead of 30, identically") but not the compounding case, and it asserts the skip behaviour without a source — if Dataform instead launches a concurrent invocation, the design still holds, because the `MERGE` is idempotent on `event_id` and the watermark only advances on success. Saying that costs a clause and makes the row safe under either behaviour.

## Claims ledger

**DECISIONS**
- Pub/Sub kept — durable buffer, unforgeable `publish_time`, topic-schema validation at publish. Rejected alternative: collector writes to BigQuery directly (deletes the buffer, turns downstream failure into producer-side loss).
- BigQuery kept — native subscription target, `MERGE` unifies dedup/backfill/restatement. Rejected alternative: GCS + BigLake as primary store ("no `MERGE`, no real pruning, no clustering").
- Cloud Storage kept as a second export target — only copy that never passed through BigQuery; no rebuild path past day 7. Rejected alternative: Pub/Sub retention alone (rejected on inspectability, conceded as cheaper).
- GCS **Standard** class, not Archive or Nearline — minimum-duration clause inverts cold-tier economics when retention (7 days) is shorter than the minimum (365).
- **Dataflow/Beam rejected.** Reinstate condition: the producer refuses to emit the five-field split. Sub-decisions: field split done by the producer; replay via BigLake `INSERT … SELECT`; backfill via the same Dataform model; per-source normalisation via `CASE`; PII stripping rejected at ingest in favour of an allowlist typed schema in Silver.
- **Airflow/Composer rejected, Dataform instead.** Reinstate condition: "a genuinely mixed step later", added in front of Dataform via its API.
- Native export subscriptions chosen over a standard subscription + Storage Write API — decided on operational surface, explicitly *not* on cost.
- Cloud Run / GKE consumer rejected — same objection, plus at-least-once handling the subscription does.
- dbt Core rejected — portability irrelevant on a single required warehouse.
- BigQuery scheduled queries rejected — no dependency graph, SQL living in a console object.
- Two components added beyond the test's list: Dataform; Cloud Logging → Cloud Monitoring.

**TECH**
Pub/Sub (topic schema, BigQuery export subscription, Cloud Storage export subscription, standard subscription, message retention), Cloud Storage (Standard, Nearline, Archive), BigQuery (`MERGE`, `INSERT … SELECT`), BigLake external tables, Dataflow / Apache Beam, Cloud Run, GKE, Apache Airflow / Cloud Composer (scheduler, web server, DAG processor), Dataform (SQLX, Git, release configurations, workflow configurations, assertions, `${ref()}`, public API), dbt Core, BigQuery scheduled queries, BigQuery Storage Write API, Cloud Logging, Cloud Monitoring. Named as Part 2 rejects: Cube, LangChain, a vector database.

**TERMS**
- *"a runtime we operate, placed between us and something we could call directly"* — the single rule credited with deleting six components.
- *export subscription* — a Pub/Sub subscription writing directly to BigQuery or GCS with no consumer of ours.
- *the split* — moving `event_id`, `source_id`, `publisher_id`, `ssp_id`, `event_type` out of the JSON payload into named fields.
- *allowlist vs denylist* — typed Silver schema (fails closed) vs stripping filter (fails open).
- *mixed DAG* — one that touches more than one system; the condition under which Airflow is "right".
- *minimum duration* / *retrieval fee* — the two GCS storage-class clauses that decide the class.
- *reinstate condition* — the observable that would bring a rejected component back.
- *watermark* — used here as the mechanism that makes retry and skip safe; defined on other pages.

**NUMBERS**
- 23,000 events/second.
- Standard ~$0.020/GB/month, no minimum duration, no retrieval fee.
- Nearline ~$0.010/GB/month, 30-day minimum, $0.01/GB retrieval.
- Archive ~$0.0012/GB/month, 365-day minimum, $0.05/GB retrieval.
- 10.5 TB actually held; ~547 TB permanently billed under Archive; ~$657/month vs ~$210/month; "~3×". *(Verified: 365 × 1.5 TB = 547.5 TB; × $0.0012 = $657; 10,500 GB × $0.020 = $210; ratio 3.13.)*
- Second export subscription ~$2,100/month. *(Verified: 45 TB/month ≈ 40.9 TiB × $50/TiB ≈ $2,050.)*
- Two native export subscriptions ~$140/TiB; standard subscription + Storage Write API ~$105/TiB. *(Verified against $40/TiB ingestion, $40/TiB standard delivery, $50/TiB export delivery, ~$25/TiB Storage Write API.)*
- Silver runs every 30 minutes; a skipped run covers 60 minutes.
- Four schedules under Dataform.
- Six components deleted by one sentence: three here, three in Part 2.
- Five components named in the test.

**ASSUMES**
- 2B events/day and ~1.5 TB/day raw (`intro/02`), which is where 23k/s and 10.5 TB come from.
- 7-day retention binding every copy of the raw record (`part_1/00`).
- The producer/collector emits the five envelope fields, enforced by the topic schema (`part_1/01`, hop 1) — the single dependency the whole Dataflow rejection rests on.
- The collector "already routes on `publisher_id` and `event_type`" — asserted here, not in the assumptions table.
- SSPs will never converge on field semantics (`intro/02`, marked Confirmed).
- The watermark advances only on success, and a watermark-age monitor exists (`part_1/01`).
- Bronze clusters on `publisher_id, ssp_id, event_type` (`part_1/05`) — never stated here, though it is the reason the split must precede Bronze.
- Per-source `CASE` mapping happens in Silver (`part_1/06`).
- Reference data (FX rate, revenue share) is external tables over GCS with no loader and no schedule (`part_1/04`).
- Replay reads the GCS archive through a BigLake external table (`part_1/03`).
- Silver's typed schema is the anonymisation boundary (`part_1/00`).
- Single-region GCP list prices, no committed-use or negotiated discount.
- The BigQuery subscription can write the payload to a `JSON` column and dead-letters what it cannot (`part_1/01`).
