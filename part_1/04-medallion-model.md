# 2.1 — Medallion Model

*Test bullet: propose a data organization according to the Medallion pattern (Bronze, Silver, Gold).*

**Bronze accepts everything, Silver is the source of truth, Gold answers the question.** The layer allowed to persist is the anonymised one, not the raw one — the inverse of the usual instinct, and forced by the client's 7-day retention rule. Gold is two fact tables rather than one, because sell-through and SSP performance have two different denominators, and a single table keyed by SSP can only produce the wrong one.

---

| | **Bronze** | **Silver** | **Gold** |
|---|---|---|---|
| **Rule** | Accepts everything, validates nothing | Types, deduplicates, **anonymises**, applies anything that can later change | Aggregates to the grain the business asks its questions in |
| **Grain** | One row per message | One row per event, deduplicated on `event_id` | One row per **hour** × dimensions |
| **Shape** | Typed envelope + opaque `payload` JSON | \~21 typed columns, no residual JSON | Two fact tables + a quality table |
| **Partition / cluster** | `TIMESTAMP_TRUNC(publish_time, HOUR)` / `publisher_id, ssp_id, event_type` | `auction_day` / `publisher_id, event_type, ad_unit_id` | `DATE(auction_hour)` / `publisher_id, ad_unit_id` (+ `ssp_id`) |
| **Consumer** | Reprocessing, and the DE team | The DE team, operationally | BI, and the Part 2 copilot — through views |

## Silver — types, deduplicates, anonymises

> **Type wide, aggregate narrow.**

| Column | Type | Null? | Note |
|---|---|---|---|
| `event_id` | STRING | no | Dedup key. Envelope |
| `event_type` | STRING | no | `auction` / `bid` / `no_bid` / `win` / `impression` |
| `source_id` | STRING | no | Drives the per-source mapping in 2.3 |
| `publisher_id` | STRING | no | Envelope |
| `ingestion_timestamp` | TIMESTAMP | no | Pub/Sub `publish_time`; the `MERGE` tie-break |
| `auction_timestamp` | TIMESTAMP | no | The auction's clock — stamped once by the wrapper, echoed by every event of the auction |
| `auction_day` | DATE | no | `DATE(auction_timestamp)` at first insert, never updated after — *partition key* |
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

## Gold — hourly stored, daily derived

The client named two aggregations: hourly to watch a release land, daily to follow trends. **Hourly is stored; daily is a view over it.** An hour cannot be recovered from a day, and two independently built tables eventually disagree with nobody able to say which is right.

### `is_settled` — published, not left to the reader

> `is_settled` — a Silver run has succeeded **whose watermark on `publish_time` has passed `auction_hour + 2h`**.

### Two fact tables, because there are two denominators

The obvious design is one fact table at SSP grain. It cannot hold `auctions`, the denominator of fill rate: an auction opens before any SSP is involved, so it has no single `ssp_id` — one auction with ten SSPs invited becomes ten rows, and `auctions` is counted ten times.

| Table | Grain | Measures |
|---|---|---|
| **`gold_opportunity`** | `auction_hour, publisher_id, ad_unit_id, format, device, channel` | `auctions`, `auctions_with_bid`, `responses`, `bids`, `wins`, `impressions`, `gross_revenue`, `publisher_payout` |
| **`gold_ssp`** | `auction_hour, publisher_id, ad_unit_id, ssp_id, format, device, channel` | `bids`, `no_bids`, `wins`, `impressions`, `gross_revenue`, `publisher_payout` |

> **An analyst asks why SSP 7's fill rate looks catastrophic.** It isn't. SSP 7 is invited to 4% of auctions, so measured against every opportunity it looks like it never delivers; measured against the auctions it was invited to, it performs fine. A single fact table keyed by SSP gives only the first number, and the decision that number drives is *"drop SSP 7"*.

### `quality_hour`, the third table

`quality_hour` sits beside the two fact tables, at `auction_hour × publisher_id`. Per hour: how late a publisher's events arrived (`late_beyond_1h`), how long auction-to-impression actually takes, and how many rows carry a re-stamped `auction_timestamp` — a duplicated `event_id`, or a row whose day disagrees with its partition.

**Cost.** The hourly rebuild is \~$450/month, against \~$113 at four-hourly and \~$900 at 30 minutes. Thirty minutes buys nothing: an hourly figure cannot exist before its hour ends.

## The anonymisation boundary is Silver

**Raw is transient; the irreplaceable copy is the first layer *allowed* to persist.** The instinct runs the other way: raw as the irreplaceable copy, kept longest. Aggregation is named as the anonymising step, so the *deletable*/*durable* line is a pipeline layer, not a policy document.

Silver is the source of truth, anonymous and retained indefinitely; Bronze is a landing and replay buffer whose window we do not control. **Silver is the layer that has to be durable** because Gold fixes the analysable dimension combinations at design time: ask it for *fill rate by device on one ad unit during a specific incident* and the rows were already collapsed. Silver's are fixed at query time.

Bronze is too early: stripping fields there means parsing the payload at ingest, which puts back the processing component bullet 1.2 deletes. Gold is too late: Silver is retained indefinitely, so an identifier that reaches Silver persists indefinitely. That leaves Silver, where the mechanism is that the typed schema does not have those columns — an allowlist, not a filter.

> An SSP starts sending a new user-level identifier in its payload. It lands in Bronze, where everything lands, and it is gone at day 7. It never reaches Silver, because nobody added it to the allowlist — nobody had to notice it, classify it, or update a filter. **An allowlist's worst case is losing a field we wanted. A denylist's worst case is keeping one we were obliged to delete.**

`auction_id` looks like the case that breaks this. It stays in Silver: the events of one auction cannot be tied together without it. Pseudonymous is not anonymous while a re-linking key exists — but the re-linking key is Bronze, and Bronze expires. On day 8, `auction_id` is a string that groups one auction's rows and joins to nothing. **It does not need to be removed; it needs to stop meaning anything, and the retention rule does that on a schedule.** The quality job asserts that the distinct-`auction_id` count tracks the auction count — a value repeating across auctions would make it a session key, the one way this argument fails.

**The honest cost: a field nobody typed is unrecoverable after a week.** With an indefinite raw archive, recovering it would be a query. Here it is unrecoverable. That is the strongest attack available on this design.

## Rejected — one line each

| Option | Why not |
|---|---|
| **A self-join on `auction_id` to find the auction hour** | Correct, and a three-day shuffle on every hourly run. Denormalising `auction_timestamp` makes it a column read |
| **Holding unsettled hours back from publication** | Throws away real data to hide incompleteness. `is_settled` labels it instead |
| **Change detection on `ingestion_timestamp`** | Reads a clock Pub/Sub owns, so a row Silver wrote late lands behind Gold's line and its day is never rebuilt — silently, inside the window meant to repair it |
| **Deriving `auctions_with_bid` in the view** | The per-event evaluation it needs no longer exists after aggregation |
| **Unconditional rebuild of the whole Gold window** | \~5× the scan, to produce output that is almost always identical. The lever to pull *if* scan cost becomes significant, not now |
| **Silver at 13 months** | A bounded window only works if the layer can be rebuilt, and past day 7 there is nothing to rebuild from |
| **A residual JSON column in Silver** | The residual payload *is* the personal data — keeping it in an indefinitely-retained table means keeping forever the exact bytes the rule requires us to delete in seven days |

---

Next: [**2.2 — Bronze Partitioning & Clustering**](/part_1/05-bronze-partitioning.md)
