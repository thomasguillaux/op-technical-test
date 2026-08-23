# 2.1 — Propose a data organization according to the Medallion pattern (Bronze, Silver, Gold)

Each layer enforces exactly one rule, and the rule is what decides what may not happen there.

| | **Bronze** | **Silver** | **Gold** |
|---|---|---|---|
| **Rule** | Accepts everything, validates nothing | Types, deduplicates, applies anything that can later change | Aggregates to the grain the business asks questions at |
| **Grain** | One row per message | One row per event, deduplicated on `event_id` | One row per day × dimensions |
| **Shape** | Typed envelope + opaque `payload` JSON | 16 typed columns, no residual JSON | Two fact tables |
| **Partition / cluster** | `TIMESTAMP_TRUNC(publish_time, HOUR)` / `publisher_id, ssp_id, event_type` | `event_day` / `publisher_id, event_type, ad_unit_id` | `day` / `publisher_id, ad_unit_id` (+ `ssp_id`) |
| **Retention** | 90 days | 13 months | Indefinite |
| **Consumer** | Reprocessing, and the DE team | The DE team, operationally | BI, and the Part 2 copilot — through views |

Retention follows one principle rather than four negotiations: **pay indefinitely for the copy that cannot be recreated, and the shortest useful window for every copy that can.**

- **GCS raw, indefinite** — the only irreplaceable copy. Gold's dimensions are fixed at design time and Silver's schema at transform time, so neither answers for a field never typed.
- **Bronze, 90 days** — the reprocessing window, long enough that a live incident is repaired from Bronze rather than from the archive.
- **Silver, 13 months** — spans a year-over-year comparison without a rebuild. A convenience, not a capability, and buyable back at any time because Silver is derived.
- **Gold, indefinite — and it is the exception.** Recreatable, yet kept forever, because at ~1M rows/day it is four orders of magnitude below the event layers: its retention is not a cost decision.

## Bronze — accepts everything, validates nothing

A fixed typed header we enforce, plus one JSON column absorbing whatever else that SSP or event type sent. **A new SSP field means no schema migration, no dropped events, no pipeline deploy.**

Only STRING columns are promoted out of the payload — `event_id`, `publisher_id`, `ssp_id`, `event_type` — and the cut falls there for a reason that is not stylistic: **a STRING cannot fail to accept a value.** `NUMERIC price` and `TIMESTAMP event_timestamp` *can* fail on malformed or skewed input, and promoting them would make Bronze validate, which is the next layer's job.

So Bronze rejects nothing that is a well-formed envelope. The only thing refusable is a message violating the topic schema, and that is dead-lettered individually rather than dropped.

**90 days** is the reprocessing window — long enough that any live incident is repaired from Bronze rather than from the archive.

## Silver — types, deduplicates, enriches

**One table for all five event types.** The dedup `MERGE`, the partitioning and the watermark are identical for `auction`, `bid`, `no_bid`, `win` and `impression`; splitting would multiply three mechanisms by five to save a predicate.

| Column | Type | Note |
|---|---|---|
| `event_id` | STRING | Dedup key |
| `event_type` | STRING | `auction` / `bid` / `no_bid` / `win` / `impression` |
| `event_timestamp` | TIMESTAMP | Producer clock |
| `event_day` | DATE | `DATE(event_timestamp)` — **partition key** |
| `ingestion_timestamp` | TIMESTAMP | Pub/Sub `publish_time`; the `MERGE` tie-break |
| `publisher_id`, `ad_unit_id`, `auction_id` | STRING | `auction_id` ties the event cluster together |
| `ssp_id` | STRING | **Nullable, and only on `auction`** |
| `format`, `device`, `channel` | STRING | display/video/native, device, prebid/direct |
| `price`, `currency` | NUMERIC, STRING | **As reported** |
| `gross_revenue` | NUMERIC | `price` converted to the reporting currency |
| `publisher_payout` | NUMERIC | `gross_revenue` × the publisher's share for that day |

Three properties are load-bearing:

**Enrichment from mutable reference data happens here, never at ingest.** Revenue share terms and FX rates get corrected retroactively — a revenue share renegotiated mid-month and backdated to the 1st makes every `publisher_payout` for that month wrong on data that is otherwise *complete and healthy*. Nothing is missing, so no retry and no late-arrival window repairs it. Applied at ingest, that repair becomes a GCS replay, because the raw record now carries a derived value with a stale rate baked in. Applied in Silver, it is a transform rerun over a bounded set of partitions, with Bronze untouched and still correct.

**And the reference data it enriches from is declared, not built.** Neither `ref_fx_rate` nor `ref_revenue_share` is something we measure; both are business inputs their owners already maintain — a finance-owned rate table, a contract export. BigQuery reads them as **Drive-backed external tables**, declared in Dataform and reached through `${ref()}` like any other source: no loader, no schedule, nothing to fail. **The FX rate is a finance input, not a data-engineering input — there is no API to call.** The guardrail is a Dataform assertion: every `impression` row in the days being built must resolve to a non-null `publisher_payout`, so a lapsed contract row fails the build instead of silently nulling revenue.

**`ssp_id` is nullable, and only for `auction`.** An auction opens before any SSP is involved — in Prebid, `auctionInit` fires at `requestBids()` and `ssp_id` first exists at `bidResponse`. `NOT NULL` would force a sentinel value that every downstream query has to remember. This same fact produces two Gold tables below.

**Money is computed on `impression` rows only.** `price` appears on `bid` (the offer), `win` (the clearing price) and `impression` (the clearing price again), but a win that never renders earns nothing. Summing revenue over impressions is the only definition consistent with eCPM's denominator.

Types are enforced at this boundary, which is the whole reason Bronze promoted only STRINGs. Rows that fail typing are routed to a rejects table with their raw payload attached rather than failing the run — **one publisher sending garbage must not stop Silver for everyone.**

**Silver keeps no residual payload**, so its contract is *typed and only typed*. Retaining the leftover JSON would cost roughly 4× (~$3,000/month against ~$800) to buy a shorter-lived, partial copy of what GCS already holds indefinitely. Promoting a field later is a SQLX change plus a backfill — from Bronze inside 90 days, from the archive beyond it.

## Gold — two fact tables, because there are two denominators

Daily and dimensioned, not daily totals: the copilot's *"why"* decomposition is only cheap if the dimensions it drills into already exist.

The obvious design is a single table at `day × publisher × ad_unit × ssp × format × device × channel`. **That grain cannot hold `auctions`** — and `auctions` is the denominator of fill rate. An auction carries no `ssp_id`, and while it knows *which* SSPs were invited, that is an **array, not a scalar dimension**. Attaching it fans one auction out into N rows and inflates the opportunity count by the number of SSPs invited, 10-20×.

**`gold_opportunity`** — `day × publisher_id × ad_unit_id × format × device × channel`
`auctions` · `auctions_with_bid` · `responses` · `bids` · `wins` · `impressions` · `gross_revenue` · `publisher_payout`

**`gold_ssp`** — `day × publisher_id × ad_unit_id × ssp_id × format × device × channel`
`bids` · `no_bids` · `wins` · `impressions` · `gross_revenue` · `publisher_payout`

The weak argument for two tables is *"measures at different grains belong in different fact tables"* — Kimball-standard, and it invites *"then just aggregate away the SSP dimension"*. The strong argument is that **each table has a denominator the other cannot express**:

| Table | Denominator | The question only it answers |
|---|---|---|
| `gold_opportunity` | `auctions` | *What share of our inventory sold?* — including auctions nobody bid on, which is exactly the unsold inventory the Yield team exists to fix |
| `gold_ssp` | `bids + no_bids` for that SSP | *Of the auctions SSP X was invited to, how often did it respond and win?* — i.e. is X worth keeping |

Every invited SSP produces exactly one response, so `bids + no_bids` is the count of opportunities *that SSP actually saw*.

> **An analyst asks why SSP 7's fill rate looks catastrophic.** It isn't. SSP 7 is invited to 4% of auctions, so measured against every opportunity it looks like it never delivers. Measured against the auctions it was actually invited to, it performs fine. A single fact table keyed by SSP offers only the first number — and the decision that number drives is *"drop SSP 7"*.

**On the duplication:** `wins`, `impressions`, `gross_revenue` and `publisher_payout` appear in both tables. They are a **conformed rollup, not a copy** — summing `gold_ssp` over `ssp_id` reproduces them in `gold_opportunity` exactly, and both are built by the same job in the same run from the same Silver rows, so they cannot drift. The alternative pushes a correctness trap into every consumer, including a copilot composing its own SQL.

**`auctions_with_bid` must be stored, and the principle matters more than the column:** any count requiring per-event evaluation has to be computed during the Gold build. Once rows are aggregated to daily grain, *"how many auctions drew zero bids"* is unrecoverable — the aggregation destroyed the information. This is the boundary between what a semantic layer can define and what Gold must supply.

**The build rule:** every 4 hours, rebuild every day inside a trailing **3-day window** whose Silver rows changed. Cadence and window are different levers — the cadence buys recovery *latency*, the window buys recovery *reach*. Three days is sized to the worst realistic detection delay: a Friday failure found Monday sits at exactly D-3.

**A third table sits beside the two facts — `quality_day`, which records whether each day is complete**: hourly counts and lateness from the daily quality job. It lives in Gold so Part 2's copilot can check whether a day is trustworthy through the grant it already has, with no access exception into Silver.

## Rejected — one line each

| Option | Why not |
|---|---|
| **A single Gold fact table at SSP grain** | Cannot express `auctions`; forces either a 10-20× opportunity overcount or a sentinel row every query must remember |
| **One Silver table per event type** | Multiplies the `MERGE`, the partitioning and the watermark by five to save a predicate |
| **Residual JSON retained in Silver** | ~4× the storage, to buy a shorter-lived partial copy of what the GCS archive already holds indefinitely |
| **Enrichment applied at ingest** | Turns a backdated revenue-share correction from a bounded transform rerun into a GCS replay |
| **Validation in Bronze** | Makes the landing layer capable of rejecting, which is the one thing it must never do |
| **Deriving `auctions_with_bid` in the view** | The per-event evaluation it needs no longer exists after aggregation |
| **Unconditional rebuild of the whole Gold window** | ~5× the scan to almost always produce byte-identical output — the lever to pull *if* scan cost becomes material, not now |

---

Next: [**2.2 — Bronze partitioning and clustering**](/part_1/05-bronze-partitioning.md)
