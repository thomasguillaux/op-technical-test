# 2.1 — Medallion Model

*Test bullet: propose a data organization according to the Medallion pattern (Bronze, Silver, Gold).*

| | **Bronze** | **Silver** | **Gold** |
|---|---|---|---|
| **Rule** | Accepts everything, validates nothing | Types, deduplicates, **anonymises**, applies anything that can later change | Aggregates to the grain the business asks its questions in |
| **Grain** | One row per message | One row per event, deduplicated on `event_id` | One row per **hour** × dimensions |
| **Shape** | Typed envelope + opaque `payload` JSON | \~21 typed columns, no residual JSON | Two fact tables + a quality table |
| **Partition / cluster** | `TIMESTAMP_TRUNC(publish_time, HOUR)` / `publisher_id, ssp_id, event_type` | `auction_day` / `publisher_id, event_type, ad_unit_id` | `DATE(auction_hour)` / `publisher_id, ad_unit_id` (+ `ssp_id`) |
| **Consumer** | Reprocessing, and the DE team | The DE team, operationally | BI, and the Part 2 copilot — through views |

## Bronze — accepts everything, validates nothing

A fixed typed header we enforce, plus one JSON column absorbing whatever else the SSP or the event type sent. **A new SSP field means no schema migration, no dropped events, no pipeline deploy.** Only STRING columns are promoted out of the payload — `event_id`, `source_id`, `publisher_id`, `ssp_id`, `event_type` — because a STRING cannot refuse a value. `NUMERIC price` and `TIMESTAMP auction_timestamp` *can* fail on malformed input, and promoting them would make Bronze validate, which is the next layer's job.

## Silver — types, deduplicates, anonymises

One table for all five event types: the `MERGE`, the partitioning and the watermark are identical, and splitting multiplies three mechanisms by five to save a predicate.

Silver is typed wide, and the retention rule forces it. A narrow Silver is correct when raw is kept forever — anything omitted still sits in the archive. Here omission is permanent at day 7. Every structured non-PII field gets a column whether a metric uses it today or not; Gold stays as narrow as its metrics require. Affordable only because there is no free text — every field is a low-cardinality auction attribute.

> **Type wide, aggregate narrow.**

| Column | Type | Null? | Note |
|---|---|---|---|
| `event_id` | STRING | no | Dedup key. Envelope |
| `event_type` | STRING | no | `auction` / `bid` / `no_bid` / `win` / `impression` |
| `source_id` | STRING | no | Drives the per-source mapping in 2.3 |
| `publisher_id` | STRING | no | Envelope |
| `ingestion_timestamp` | TIMESTAMP | no | Pub/Sub `publish_time`; the `MERGE` tie-break |
| `auction_timestamp` | TIMESTAMP | no | The auction's clock — stamped once by the wrapper, echoed by every event of the auction |
| `auction_day` | DATE | no | `DATE(auction_timestamp)` — *partition key* |
| `auction_hour` | TIMESTAMP | no | `TIMESTAMP_TRUNC(auction_timestamp, HOUR)` — Gold's grain |
| `job_insert_timestamp` | TIMESTAMP | no | When this pipeline first wrote the row |
| `job_update_timestamp` | TIMESTAMP | no | When it last rewrote it — *Gold's change-detection clock* |
| `auction_id` | STRING | yes | Ties the cluster of events together. Pseudonym; unlinkable from day 8 |
| `event_timestamp` | TIMESTAMP | yes | This event's own clock. For latency, never for bucketing |
| `ad_unit_id` | STRING | yes | |
| `ssp_id` | STRING | yes | Null on `auction` — an auction has no single SSP |
| `format`, `device`, `channel` | STRING | yes | display/video/native · device class · prebid/direct |
| `price`, `currency` | NUMERIC, STRING | yes | As reported |
| `gross_revenue` | NUMERIC | yes | `price` converted to the reporting currency |
| `publisher_payout` | NUMERIC | yes | `gross_revenue` × the publisher's share for that day |

Everything read out of a payload is nullable. Requiring more hands a third party the ability to stop our pipeline: an SSP that never reports `device` is not sending garbage, it simply does not measure device, and a `NOT NULL` there rejects every one of its rows. *Empty, never `'unknown'`, never a default.* Typing failures follow the same rule — `SAFE_CAST` on a `price` of `"n/a"` yields null, which propagates into a metric that refuses to render. Only a missing `auction_timestamp` diverts the row entirely, to `silver_rejects`: the one field whose absence makes a row unplaceable rather than incomplete.

Money lands here, not at ingest, and only on `impression` rows — `price` appears on `bid` and `win` too, but a win that never renders earns nothing, and summing over impressions is the only definition consistent with eCPM's denominator. `gross_revenue` and `publisher_payout` come from joining two declared external tables over GCS: an FX rate owned by finance, a revenue share owned by the contract, each read in place with no loader and no schedule. **Enriching at ingest instead turns a revenue share backdated to the 1st from a rerun over named partitions into a GCS replay.**

## Gold — hourly stored, daily derived

The client named two aggregations: hourly to watch a release land, daily to follow trends. **Hourly is stored, daily is a view over it** — an hour cannot be recovered from a day, and two independently built tables eventually disagree with nobody able to say which is right.

This is free rather than clever. The semantic layer requires every stored measure to be additive — counts and sums, never ratios — and additivity over dimensions and additivity over time are the same property, so **a rule adopted so a fill rate could be computed per publisher makes a day the exact sum of its 24 hours.**

### Bucketing: by the auction's hour, not the event's

At daily grain this barely matters. At hourly grain it is the decision the tier rests on: an auction opening at 09:58 whose impression renders at 10:02 puts its denominator in one hour and its numerator in the next, so every ratio is wrong in both, in opposite directions. Flow attribution's defence is that the errors cancel under steady traffic — but a deploy is a step change, the one condition where inflow and outflow are not equal, so **flow breaks precisely in the scenario the hourly tier was requested for.**

So every event counts in the hour its *auction* opened, read from `auction_hour`, and a fill rate for 09:00 means *"of the opportunities opened at 09:00, how many filled"*. That rests on one property: the Prebid wrapper stamps `auction_timestamp` once, when the auction opens, and every event of the auction echoes it — an attribute the producer *carries*, never one each source *generates*. Integrations report it at different paths, which is why 2.3 maps it per source; none of them invent it.

### `is_settled` — published, not left to the reader

Cohort attribution costs one thing: an hour is not final when it closes. Each hour row carries a boolean, and the rule is a predicate rather than a phrase:

> `is_settled` — a Silver run has succeeded **whose watermark on `publish_time` has passed `auction_hour + 2h`**.

Two hours because the auction lifecycle is bounded at one — its events publish within seconds — and a retry lands at most an hour after the original. The watermark, not the wall clock, is what makes it safe: during a drain the watermark lags, so hours stay unsettled until the data is genuinely in, where a clock rule would declare an hour final while the outage that emptied it was still draining. Each row also carries `sources_total` and `sources_reporting_impressions`, publishing the same kind of verdict: an SSP with no impression beacon contributes real bids and no impressions, which reads as inventory won and never served rather than as a measurement that is missing. So a metric a source cannot report is `NULL`, never `0`, and `SAFE_DIVIDE` propagates it until the ratio refuses to render.

### Two fact tables, because there are two denominators

The obvious design is one fact table at SSP grain. It cannot hold `auctions`, the denominator of fill rate: an auction opens before any SSP is involved, so it has no single `ssp_id` — one auction with ten SSPs invited becomes ten rows, and `auctions` is counted ten times.

| Table | Grain | Measures |
|---|---|---|
| **`gold_opportunity`** | `auction_hour, publisher_id, ad_unit_id, format, device, channel` | `auctions`, `auctions_with_bid`, `responses`, `bids`, `wins`, `impressions`, `gross_revenue`, `publisher_payout` |
| **`gold_ssp`** | `auction_hour, publisher_id, ad_unit_id, ssp_id, format, device, channel` | `bids`, `no_bids`, `wins`, `impressions`, `gross_revenue`, `publisher_payout` |

`responses` is bids + no_bids across every SSP invited — demand depth per opportunity, readable without joining `gold_ssp`. Both tables also carry `is_settled` and the two coverage counts, and both partition by `DATE(auction_hour)`: daily partitions holding hourly rows, because hourly ones would put 8,760 a year against BigQuery's 10,000-partition ceiling, on a table retained indefinitely.

> **An analyst asks why SSP 7's fill rate looks catastrophic.** It isn't. SSP 7 is invited to 4% of auctions, so measured against every opportunity it looks like it never delivers; measured against the auctions it was invited to, it performs fine. A single fact table keyed by SSP gives only the first number, and the decision that number drives is *"drop SSP 7"*.

The five measures both tables share are a conformed rollup, not a copy: summing `gold_ssp` over `ssp_id` reproduces every one of them, and one job builds both in the same run from the same rows. **The two that do not roll up are the argument for the second table** — no sum over SSPs recovers `auctions` or `auctions_with_bid`, because they are counted per auction and an auction has no `ssp_id`.

Every hour, rebuild each day inside a trailing 3-day window whose Silver rows changed. Frequency buys recovery *speed*, the window buys recovery *reach*, and three days matches the worst realistic detection delay — a Friday failure found on Monday sits at exactly D-3. The cadence is set by self-healing, not freshness: a failed run is repaired by the next one instead of leaving D-1 wrong all day.

### `quality_hour`, the third table

It sits beside the two at `auction_hour × publisher_id`: per hour, how late its events arrived (`late_beyond_1h`), how many `event_id`s appeared with more than one `auction_timestamp`, and how long auction-to-impression actually takes. Per publisher, because *which* publisher is late is the entire actionable content — **a total names nobody.** It lives in Gold so Part 2's copilot reads it with the access it already has.

**Cost.** The hourly rebuild is \~$450/month, against \~$113 at four-hourly and \~$900 at 30 minutes. Thirty minutes buys nothing: an hourly figure cannot exist before its hour ends.

### No dimension tables

Every dimension — `publisher_id`, `ad_unit_id`, `ssp_id`, `format`, `device`, `channel` — is a column on the fact row. **Normalisation exists to stop repeating a string on disk, and a columnar store already does that**: `device` with four values dictionary-encodes to almost nothing, so a dimension table saves storage BigQuery was never going to spend, and costs a join on every query for every consumer — including a copilot composing its own SQL, where a wrong join is a wrong number rather than an error. The one attribute that genuinely varies over time is the publisher's revenue share, and it is versioned in Silver with `valid_from` / `valid_to` before Gold sees the row: **the history a slowly-changing dimension exists to keep is kept one layer earlier, where the money is computed.**

## Rejected — one line each

| Option | Why not |
|---|---|
| **A self-join on `auction_id` to find the auction hour** | Correct, and a three-day shuffle on every hourly run. Denormalising `auction_timestamp` makes it a column read |
| **Holding unsettled hours back from publication** | Throws away real data to hide incompleteness. `is_settled` labels it instead |
| **Change detection on `ingestion_timestamp`** | Reads a clock Pub/Sub owns, so a row Silver wrote late lands behind Gold's line and its day is never rebuilt — silently, inside the window meant to repair it |
| **Deriving `auctions_with_bid` in the view** | The per-event evaluation it needs no longer exists after aggregation |
| **Unconditional rebuild of the whole Gold window** | \~5× the scan, to produce output that is almost always identical. The lever to pull *if* scan cost becomes significant, not now |

---

Next: [**2.2 — Bronze Partitioning & Clustering**](/part_1/05-bronze-partitioning.md)
