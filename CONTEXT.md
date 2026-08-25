# Domain context — OptimusAds

OptimusAds monetizes ad inventory for media publishers through header bidding.

This file is the shared glossary: business vocabulary only. No architecture, no schemas, no implementation.

**No design decisions either.** A term belongs here only if it would mean the same thing under a completely different architecture. Anything we *chose* lives in the write-up — a decision parked in the glossary reads as a given and stops being grilled.

## Supply side

**Publisher** — a media company whose sites carry the ad inventory OptimusAds monetizes. Hundreds of them.

**Ad unit** — a named ad placement on a Publisher's page.

**Format** — the creative shape sold through a placement (display, video, native). A property of an individual **Event**, not of the **Ad unit**: one placement can serve several formats.

## Demand side

**SSP** — supply-side platform; a demand channel bidding on inventory. Identified by `ssp_id`.

**Header bidding** — running a simultaneous auction across several SSPs before the ad server is called, so demand competes in parallel rather than being offered inventory in waterfall order.

**Prebid** — the header-bidding stack that runs those auctions.

**Channel** — the route by which demand reached the inventory: the Prebid header-bidding auction, or another path such as a direct deal. A dimension of every Event.

**Prebid revenue** — revenue attributable to the Prebid **Channel**. A slice of total revenue by channel, not a separate kind of money.

**Device** — the class of device the visitor browsed on (desktop, mobile web, tablet, app). Describes incoming traffic rather than anything OptimusAds configures, but it is a frequent explanation for short-term revenue moves.

## Auction lifecycle

**Auction** — one competition for one impression opportunity on one **Ad unit**. Opens before any SSP is involved, so it carries no `ssp_id`. Identified by `auction_id`.

**Invited SSP set** — the SSPs the Auction was put to. Known when the Auction opens, but it is a *set*, not a single SSP: an Auction has many, which is why the Auction itself has no `ssp_id`.

**Bid** — one SSP's price offer in an Auction.

**No-bid** — one SSP declining to price the opportunity, or timing out. Analytically it answers "which SSPs are actually responding to this inventory".

Bid and No-bid are the two possible SSP responses, one per SSP invited. They are the unit of volume: an Auction putting the opportunity to N SSPs produces N responses, while every other event type occurs at most once per opportunity.

**Win** — the Bid that took the Auction.

**Impression** — a winning ad actually rendered to the visitor. Not every Win becomes an Impression.

**Event** — any of the five above, as a record on the stream, discriminated by `event_type`: `auction`, `bid`, `no_bid`, `win`, `impression`. Identified by `event_id`.

One ad slot therefore produces a small cluster of Events sharing an `auction_id` — the Auction, one response per invited SSP, and, if the inventory sold, a Win and an Impression.

Whether each Event carries its Auction's context or merely references the Auction is a modelling decision, not a domain fact — see [2.1 Medallion Model](/part_1/04-medallion-model.md).

**Auction lifecycle bound** — an Auction reaches its final state within **one hour** of its first Bid. A Win or Impression may reach the stream after the rest of its Auction, but never later than that.

**Duplicate** — a repeated copy of an Event already received, produced by client or collector retries. Carries the same `event_id`. Arrives within **one hour** of the original.

## Money

**Gross revenue** — total revenue the inventory generated, before OptimusAds' share.

**Publisher payout** — the portion owed to the Publisher.

**Net revenue** — OptimusAds' retained share: gross revenue minus publisher payout.

**Gross margin** — net revenue as a proportion of gross revenue.

All money figures are derived from winning bid prices observed on the auction stream. They are estimates: no SSP billing feed reconciles them.

## Performance metrics

**eCPM** — gross revenue per thousand **Impressions**. Gross, because that is the publisher-facing figure and what the term means outside the company. OptimusAds' retained equivalent is a separate metric under a separate name, never called eCPM.

**Fill rate** — the proportion of impression opportunities that resulted in a served ad: **Impressions** over **Auctions**. The numerator is Impressions rather than Wins because the business question is whether an ad was actually served, and not every Win becomes an Impression.

**The denominator must count *every* impression opportunity offered**, including Auctions that drew no response at all. Recorded because it is a business fact rather than a modelling preference: a denominator restricted to Auctions with at least one response would hide exactly the unsold inventory the **Yield team** exists to fix.

**Fill rate has three stages**, each with a different cause and a different owner: whether any SSP bid at all, whether a bid cleared, and whether the Win rendered. A movement in the whole is not actionable until it is attributed to one of the three.

**Revenue per opportunity** — gross revenue per thousand **Auctions**. Exists because **eCPM** and **Fill rate** trade against each other — raising floor prices lifts one and drops the other — so neither on its own says whether a configuration change made money.

**SSP participation rates** are measured against the Auctions that SSP was invited to, which is its own **Bids** plus **No-bids** — never against every Auction. See the distinction recorded below.

**Inventory fill and SSP participation are different measurements**, and the distinction is a business fact rather than a modelling choice:

- *Inventory fill* asks **what share of our inventory sold**. Its denominator is every Auction.
- *SSP participation* asks **is this SSP worth keeping** — how often it responds, and how often it wins. Its denominator is the Auctions **that SSP was invited to**, which is the count of its own Bids plus No-bids.

Measuring an SSP against every Auction would make an SSP invited to a small slice of inventory look poor for reasons unrelated to its performance. The two questions do not share a denominator and are not roll-ups of one another.

## People

**Yield team** — the internal team that tunes monetization: floor prices, SSP mix, placement configuration. Small — around ten people — and every member sees every Publisher.

They work on **two rhythms**, and they are different instruments rather than two resolutions of one need:

- **Look at yesterday, act today** — analyse complete Days, change configuration in response. Trend work.
- **Ship, then watch** — after a configuration or release change, watch the next few closed Hours to see whether it broke something. Episodic: nobody watches an hourly chart all day, but on a deploy day a closed Hour is read within minutes of closing.

**Data engineering team** — owns the pipeline. Consumers of current-Day data for operational reasons: whether Events are still arriving, and whether a given Publisher has gone quiet.

## Scale

**\~2 billion Events per day**, roughly 1.5 TB of raw payload. Bid and No-bid together account for 75-80% of that count, since they alone multiply by the number of SSPs invited.

**Raw logs are retained 7 days.** A constraint given by the client, not chosen. Everything retained beyond that must be **Anonymous**.

**No free text.** Every field on the stream is a structured auction attribute — bid value, filled/unfilled, bidders, winner. Nothing is prose or user-supplied string content.

## Conventions

**Day** — the UTC calendar day, everywhere. An Event's day is the day it *happened*, not the day it reached us; the one-hour lifecycle bound caps how far those can diverge.

**Hour** — the UTC clock hour. An Auction belongs to the Hour it **opened**, and every Event of that Auction belongs to the same one — including a Win or Impression that fires after the Hour has closed. This is a convention rather than a decision only in the sense that the alternative was considered and rejected; the argument is in [2.1 Medallion Model](/part_1/04-medallion-model.md).

**Settled** — an Hour is settled once no further Events for it can arrive: the lifecycle bound and the duplicate-arrival bound have both elapsed. An Hour that has closed on the clock is not yet settled, and the two are routinely confused.

**Source** — the origin system a raw Event came from. Sources do not agree on payload shape, and not every Source reports every **Event** type. Distinct from **SSP**: one Source may carry events about many SSPs.

**Coverage** — for a given measurement, the share of contributing **Sources** that are capable of reporting it. Below 1, a metric describes fewer Sources than the slice contains, and is not comparable with one at 1.

**Anonymous** — for this pipeline's purposes: carrying no field that identifies a person, and no key that can be linked back to one. **Pseudonymous is not anonymous while a re-linking key still exists** — which is why the boundary is defined by what the raw layer retains, not only by what the aggregated layer contains.

**Currency** — SSPs report prices in their own currency. A single reporting currency is used everywhere the business sees a figure. *Where* in the pipeline conversion happens is a decision, not a convention — see [2.1 Medallion Model](/part_1/04-medallion-model.md).
