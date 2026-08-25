# Review — `part1-pipeline.md`

## Summary

This page is the executive summary of Part 1: the whole pipeline compressed into ten sentences, one "why this shape" section, and a routing table whose rows are claims rather than labels. It largely lands — a CTO who reads only this page leaves with the right mental model of the architecture and knows exactly which page to open — but one absolute in sentence two contradicts the pages beneath it, and the page never states how fresh the data actually is.

## Grade

| Dimension | Grade | One line |
|---|---|---|
| Decision quality | **A** | Every one of the ten sentences carries the alternative it beat ("two writes, not one write and a copy"; "two fact tables, not one"; allowlist vs stripping filter) — compression that keeps the argument rather than the conclusion. |
| Narrative | **B** | It leads somewhere (two shapes → no third shape → where the line sits → what it costs), but the reader never learns the pipeline's latency contract, and the strongest operability material is a subordinate clause in a table. |
| Operability instinct | **B** | The cost lever and the self-healing spine are named well; the "no process of ours can fail" framing reads as bravado where the sub-pages read as instinct, and monitoring — the best thing in Part 1 — is nearly invisible here. |
| Technical plausibility | **B** | Every number checks against the pages below (23k/s, 1.5 TB/day, the $5,100 grain delta = $6,100 − $1,000) and the design is coherent; two absolutes overreach in a way a staff engineer will pick at. |
| Signal density | **A** | 764 words, no boilerplate, no throat-clearing; the routing table is claims, not labels. Two meta-sentences are the only fat. |
| **Overall** | **A** | Reads as a strong senior candidate — the page earns interest rather than tolerance; the one credibility issue is a five-word fix, and I would grade it down to B if it survived to the defence. |

## Top findings

**1. [BLOCKER] "No process of ours that can fail between the publisher and the dashboard" is contradicted by the document's own operating model.**
- What: Dataform sits between Bronze and the dashboard, is operated by us, and can fail — 1.3 says the cold path's failure mode is "a run that failed and can be run again", and 1.2 says a run can be *skipped* silently, which is why the watermark-age monitor exists.
- Why it matters to the evaluator: it is sentence two, it is the page's thesis, and it is the sentence a hostile reviewer opens with; having to walk it back live costs more than the claim buys. (The charitable reading — "process" = deployed daemon — exists, but on a page this precise the looseness stands out.)
- Fix: swap *fail* for *be wrong*, or scope it: "no service we deploy, no runtime we patch, and no failure of ours that a rerun does not fix." Same rhetorical force, and it is the claim the pages below actually defend. The same edit is due on "Bronze itself validates nothing" — Bronze's `JSON` column refuses invalid payloads to the dead-letter topic, per 1.1 hop 4.

**2. [QUESTION] The page never states end-to-end freshness, and uses "hourly" in three different senses.**
- What: "hourly" means Bronze's partition grain (arrival clock), Gold's row grain (auction clock), and the quality-check cadence — three things, three sentences apart, and the actual refresh cadences (Silver every 30 min, Gold hourly) exist only inside a 3,464px diagram no one reads at a glance.
- Why it matters to the evaluator: "when does an event show up on the dashboard?" is the first question anyone asks about a pipeline, and a reader can easily come away thinking Bronze is an hourly batch rather than seconds-latency streaming ingest.
- Fix: add one clause to the Bronze or Gold sentence — "Bronze in seconds, Silver within 30 minutes, Gold on the hour" — and disambiguate one of the three uses of "hourly" (e.g. "hourly *arrival* partitions").

**3. [QUESTION] The quality/monitoring spine — the strongest material in Part 1 — is almost absent from the ten sentences.**
- What: Cloud Logging and Cloud Monitoring are named in sentence one and then never explained; the "five signals that fire while every job reports success" (1.1) and the assertion-blocks-Gold-never-Silver rule appear only as a routing-table clause and a half-line in *Two spines*.
- Why it matters to the evaluator: a summary that describes only the happy path reads as an architecture diagram; the *wrong-while-green* material is what distinguishes this from a competent generic answer, and a CTO skimming one page will not see it.
- Fix: spend one of the ten sentences on it — "the alerts worth having are the ones that fire while every job reports success: watermark age, dead-letter depth, lateness against the 1-hour bound, Silver writes outside Gold's window" — funded by merging sentences one and two (see Cuts).

**4. [QUESTION] The cost paragraph pre-empts "what does this cost?" with a refusal rather than an answer, and states the refusal twice.**
- What: "No total on this page, and none anywhere — each page prices its own decision" declines the one number a CTO will look for on a 2B-events/day pipeline, and the convention is already explained on the methodology page.
- Why it matters to the evaluator: the abstention is methodologically defensible, but drawing attention to it invites the question instead of closing it, and a reader cannot sanity-check the design's scale without an order of magnitude.
- Fix: cut the meta-sentence and keep the lever; if a figure is allowed at all, one clause does it — "the bill is dominated by ingestion, not by anything we operate" — which is an argument, not a TCO.

**5. [POLISH] The routing table's strongest claim is the one row that does not state a claim.**
- What: the Retention row explains why the page exists ("stated once instead of six times") where every other row states what its page proves; the actual claim — *Bronze is not the source of truth here, Silver is* — is the most interesting inversion in Part 1 and only surfaces in sentence five. "Six of the answers below" is also a checkable count that neither page enumerates.
- Why it matters to the evaluator: the table is the page's navigation and its second-best argument; one row wasted on housekeeping is a wasted slot.
- Fix: rewrite the row as "The medallion convention inverts: raw is legally transient, so Silver — not Bronze — is the source of truth", and either enumerate the six answers or drop the number.

## Cuts

1. **Sentences one and two of the ten (lines 9 and 11)** — merge into one. "Two shapes" and "no third shape" are the same idea stated twice; the second sentence's only new content is the triplet, and that survives inside the first. **~35 words saved**, nothing lost, and the freed slot pays for finding 3.
2. **"Dataform's compile-time templating is not a counterexample — a build step is not a runtime." (line 31)** — defensive pre-emption of an objection nobody raises at summary altitude; it belongs in 1.2 where the templating is actually shown. **~18 words**. Lost: a good line, in the wrong room.
3. **"No total on this page, and none anywhere — each page prices its own decision, so no argument rests on a figure." (line 35)** — the convention is already stated in `intro/01-methodology.md`; on the front page of Part 1 it is a rule about the document, not about the design. **~22 words**. Lost: nothing a reader misses.
4. **"Each page stands alone and ends with the options it rejected, one line each." (line 39)** — restates the methodology page a second time; the table below demonstrates it. **~14 words**. Lost: nothing.
5. **Cross-page duplication (no cut here, a note):** "One rule applied six times is a design; six separate verdicts would be taste" appears verbatim on this page, in `intro/01-methodology.md` and in `part_1/02-component-justification.md`. This page is the right home for it — cut it from one of the other two.

## Interview questions this page invites

1. **"Dataform runs fail, and you say a skipped run emits no failure log — so who gets paged, and how fast? Sentence two says nothing of yours can fail."** Not answered here; answered well in 1.1 and 1.2. The page should not leave the contradiction to be resolved three clicks away.
2. **"An impression happens at 10:02. When can I see it on a dashboard, and when is that number final?"** Not answered on this page; `is_settled` is named in a routing row and the cadences are only on the diagram. 2.1 answers it fully.
3. **"Is the 7-day rule a legal ceiling or a client policy? If it moves to 90 days, how much of this design changes?"** Not answered anywhere in Part 1 — the page asserts "legally transient" (a word the assumptions page does not use) and the whole Silver-as-source-of-truth spine, the typed-wide Silver and the GCS storage-class arithmetic all hang off it. A one-line "what changes if the ceiling moves" would match the reinstate-condition habit used everywhere else.

## Claims ledger

**DECISIONS**
- Six GCP services only, in two shapes (Google-operated config left of Bronze, SQL on a clock right of it) — rejects: any third shape, i.e. a service we deploy or a runtime we patch
- Dataflow, Composer, dbt Core rejected by one rule: *a runtime we operate, placed between us and something we could call directly* (same rule kills Cube, LangChain, a vector DB in Part 2)
- Dataform kept as orchestrator — rejects: Composer/Airflow, on "this DAG has one system in it"
- Dataform's compile-time templating declared not a runtime ("a build step is not a runtime")
- One topic → two export subscriptions in parallel (BigQuery + GCS) — rejects: one write plus a downstream copy
- Hot/cold line at Bronze; hot path does envelope check only — rejects: any processing before Bronze
- Silver is the durable record / source of truth, retained indefinitely — rejects: raw as the irreplaceable copy
- Anonymisation boundary = Silver's typed schema (allowlist) — rejects: stripping filter (denylist)
- Bronze: typed envelope + opaque JSON, validates nothing, hourly partition on `publish_time`, cluster `publisher_id, ssp_id, event_type`, 7-day expiry — rejects: daily grain; a producer-owned clock
- Dedup = window function on `event_id` + `MERGE` — rejects: window function alone
- Gold stores hourly rows on the auction's clock; daily tier is a view over them — rejects: two independently built tiers
- Two Gold fact tables (`auctions` denominator vs `bids + no_bids`) — rejects: a single fact table
- Quality checks run hourly — rejects: weekly ("a repair vs an obituary")
- No TCO total anywhere; per-page cost paragraphs only

**TECH**
Pub/Sub · Cloud Storage · BigQuery · Dataform · Cloud Logging · Cloud Monitoring · SQLX · Git · BigQuery views (implied via routing) · rejected/named: Dataflow, Beam (implied), Airflow/Composer, dbt Core, Cube, LangChain, vector database

**TERMS**
two shapes / no third shape · hot path · cold path · "the hot path can fail but cannot be wrong" · envelope check · Bronze / Silver / Gold · anonymisation boundary · allowlist vs stripping filter (fails closed vs fails open) · durable record · legally transient · daily tier as a view · denominator · fact table · assertions as the quality gate · watermark read (routing) · repair trigger (routing) · `is_settled` published not inferred (routing) · spine · "a runtime we operate, placed between us and something we could call directly" · "type wide, aggregate narrow" (routing)

**NUMBERS**
2B events/day · ~23,000 events/second sustained · ~1.5 TB/day raw · 6 GCP services · 6 components rejected by one rule (3 in Part 1, 3 in Part 2) · 2 export subscriptions · 7-day Bronze expiry · hourly Bronze partition grain · 3 Bronze cluster keys · 2 Gold fact tables · 24 hours = one day (additivity) · ~$5,100/month between hourly and daily Bronze partitioning · 48 Silver watermark reads/day (routing) · 4 repair triggers (routing) · 5 signals that fire while jobs are green (routing) · 7 pages below · "six of the answers" reshaped by the retention rule

**ASSUMES**
- Volume (2B/day, 1.5 TB/day) taken as Given from `intro/02-business-assumptions.md`
- 7-day raw retention as a ceiling we do not control, and "aggregation anonymises" — Confirmed with the client; this page additionally characterises it as **legal**, a word the assumptions page does not use
- Two required aggregation grains (hourly to watch a release, daily for trend)
- The producer supplies the envelope field split (from 1.2 — the condition that reinstates Dataflow)
- Auction lifecycle ≤ 1 hour, and duplicates arriving ≤ 1 hour late (underpins hourly bucketing and the watermark)
- Part 2 exists and rejects Cube, LangChain and a vector database by the same sentence
- `assets/architecture.png` carries the cadences (30 min / hourly) that the prose does not state
