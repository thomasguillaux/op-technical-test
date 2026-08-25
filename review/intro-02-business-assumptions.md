# Review — `intro/02-business-assumptions.md`

## Summary

This page fixes the requirement set the other seventeen pages spend their arguments on — volume, event mix, schema variance, freshness, 7-day retention, ten users — and marks each line by where it came from, so a reader can attack the foundation separately from the design. It mostly lands: the discipline of "requirements only, never mechanisms" is real and the closing move (*the assumption we are least sure of is the one the pipeline measures*) is the most senior sentence in the intro — but the provenance labels claim more than the brief supports, and the volume line has no peak or growth figure behind it.

## Grade

- **Decision quality — B.** The confirm/assume split and the deliberate equalising of the two one-hour bounds are genuine choices, but only one line carries *what breaks if this is wrong*, and none carries the reinstate condition every other page in the document uses.
- **Narrative — A.** Opens with an admission rule, closes by handing the retention consequence to Part 1's first page; the reader arrives somewhere rather than being handed a table.
- **Operability instinct — B.** "Every window derives from that 1-hour figure, so the pipeline measures it, per hour and per publisher" is exactly right; there is no peak-to-average, no growth, and no cardinality line to size anything against.
- **Technical plausibility — B.** 2B/day, 1.5 TB/day and the 75-80% mix hang together arithmetically, but a *daily average* is the only volume figure offered and downstream pages spend it as a steady-state 23k/s.
- **Signal density — B.** 520 words for the document's foundation is tight, but roughly 90 of them are the page discussing its own labelling scheme rather than the assumptions.
- **Overall — B.** Strong instincts, one soft spot that happens to sit under everything else.

## Top findings

**1. [QUESTION] The volume line gives a daily total and no peak.**
- **What:** 2B events/day is an average; ad traffic is diurnal, and downstream pages convert it straight to a flat 23k/s that then sizes dedup state (~10 GB), alerting thresholds and the hourly-partition cost delta.
- **Why it matters:** Sizing streaming infrastructure off a daily mean is the specific mistake the evaluation grid's "understanding of scale constraints" is looking for; a staff engineer will circle 23k/s before reading anything else.
- **Fix:** Add one row — peak hour as a multiple of the daily mean (e.g. "peak ≈ 2× mean, so ~45k/s"), marked Assumed like the timing bounds — and note that every per-second figure downstream is the peak, not the mean.

**2. [BLOCKER] "Given" and "Confirmed" claim provenance the brief does not carry, and the taxonomy is never defined.**
- **What:** The brief says *several billion* events and *hundreds of publishers*; the page marks "2B events/day, ~1.5 TB/day" as **Given**, along with "~10 people" — none of which appears in the brief — while four other lines are **Confirmed**, and nowhere does the page say what distinguishes the two labels or who confirmed anything. The two **Assumed** rows are then described in the closing prose as coming "from a conversation, not a measurement", which is what Confirmed should mean.
- **Why it matters:** A four-way provenance taxonomy is a rigour signal only if the categories are distinguishable; here a reader holding the brief finds the one number it *does* state (several billion) rounded down and relabelled as handed over, which turns the whole scheme into decoration.
- **Fix:** Define the four labels in one line at the top (Given = in the brief; Confirmed = asked and answered in clarification; Derived = ours, from a Given; Assumed = ours, unvalidated), then re-mark: 2B/1.5 TB as Confirmed with "the low end of the test's *several billion*" stated explicitly, and "analytics only" as Derived from *availability for BI*.

**3. [QUESTION] The one line that deletes work is the one line with no consequence attached.**
- **What:** "~10 people, all seeing all publishers — **no entitlement scoping, so no row-level security to design**" removes an entire security surface from Part 2, in a business with hundreds of publishers, and the page never says what reinstates it.
- **Why it matters:** Every other page in this document pairs a rejection with the condition that brings it back; the page that most needs that convention is the only one without it, and "publishers get a login" is the most predictable roadmap item in adtech.
- **Fix:** One clause on that row: the condition that reinstates it (publisher-facing access, or an agency user), and where it lands (authorized views become per-publisher, the agent's IAM identity stops being shared).

**4. [QUESTION] "Derived" is asserted for the event mix, but the derivation needs a number the page never gives.**
- **What:** 75-80% bid/no_bid follows only from the count of SSPs invited per auction and the fill rate; the mechanism is stated, the arithmetic is not, and the invited-SSP count is absent from the table despite being the multiplier that produces the 2B in the first place.
- **Why it matters:** A line labelled Derived invites the reader to check the derivation; if they cannot, the label is doing less work than "Assumed" would.
- **Fix:** Add the invited-SSP count as its own row and close the mix row with the arithmetic in one clause: "~4 SSPs invited, most opportunities unsold, so responses are 4 of every 5 events."

**5. [POLISH] The table breaks its own opening rule twice.**
- **What:** "A line belongs here only if it stays true under a completely different architecture," then the Freshness and Retention rows name Bronze, Silver and Gold, and the Duplicate row justifies itself with "how far back must a run look" — layer names and run cadence are architecture.
- **Why it matters:** It is the page's own stated test, applied in the first sentence and failed three rows later; a reader who notices stops trusting the separation the page is selling.
- **Fix:** State freshness in business terms — "raw available as it arrives; a clean queryable layer within 30 minutes; two aggregation grains, hourly and daily" — and cut the parenthetical justification from the Duplicate row.

## Cuts

- **Line 19, "Four of these are confirmed rather than assumed…" (~45 words).** This restates the Source column and then justifies the labelling scheme rather than the assumptions. Nothing is lost that a defined label glossary at the top would not carry better; if the point ("guessing at these would be guessing at the answer") is worth keeping, it is worth one clause, not a paragraph.
- **Line 21, "The rhythm line is derived, not quoted…" (~40 words) and the second half of the Rhythm row (~35 words).** The Freshness row already states two grains and why; the Rhythm row restates it as a reading; the paragraph restates the reading. Keep the sharpest form only — *"nobody stares at an hourly chart, but on a deploy day the closed hour is read within minutes"* — and drop the other two passes. Lost: nothing but repetition.
- **Line 13, "Same bound on purpose: both answer *how far back must a run look*" (~15 words).** Mechanism on a mechanism-free page, and it is also the weaker argument: two independent physical phenomena landing on the same number reads as convenience. Either drop the justification or replace it with the honest one — the design uses the larger of the two, and the two happen to be equal.

## Interview questions this page invites

1. **"The brief said several billion; you designed for two. What is your headroom, and what is your peak hour?"** — Not answered. The page has no growth line and no peak multiple, and the number it does give is below the brief's own wording.
2. **"Who confirmed the four Confirmed lines, and what exactly did you ask?"** — Not answered. The page asserts confirmation for retention, schema variance, payload content and Gold grain without saying what the question was; the only provenance narrative on the page ("a conversation") is attached to the two rows marked Assumed.
3. **"Your duplicate bound is one hour. What happens when a collector replays a day-old backlog?"** — Partly answered, and not here. The page's answer is "we would know, and here is the metric"; the correctness answer (Gold's trailing 3-day rebuild, the alert on Silver writes outside that window) lives in Part 1 and is not previewed, so on this page the assumption reads more load-bearing than it actually is.

## Claims ledger

**DECISIONS**
- Volume pinned at 2B events/day, ~1.5 TB/day raw — brief's "several billion" narrowed; no alternative stated
- Auction lifecycle bound and duplicate-arrival bound deliberately set to the same value (1h) — rejected: two independent bounds, on the grounds both answer the same question
- Two Gold grains (hourly, daily) treated as two distinct needs — rejected: one need at two resolutions
- No row-level security designed — rejected: entitlement scoping, because all users see all publishers
- Provenance labelled four ways (Given / Confirmed / Derived / Assumed); labels undefined on-page
- The 1h bound is instrumented rather than validated before design — rejected implicitly: measure first
- Durable record is the anonymised event layer, not raw — consequence of the 7-day ceiling
- Table scope rule: requirements only, nothing that assumes a given architecture

**TECH**
- Prebid (named as in place, not as a choice)
- Bronze / Silver / Gold (medallion layer names used in the Freshness and Retention rows)
- No GCP service named anywhere on the page (deliberate)

**TERMS**
- Given / Confirmed / Derived / Assumed (provenance labels, used in a specific sense, undefined)
- Mix (share of event count by `event_type`)
- Auction lifecycle (first bid → final state)
- Duplicate arrival (retry lag relative to original)
- Settled / D-1 correctness ("D-1 must always be correct")
- Rhythm — *look at yesterday, act today* (trend) vs *ship, then watch* (episodic)
- Anonymises (retention rule: aggregation removes identity)
- Entitlement scoping / row-level security (declared out of scope)

**NUMBERS**
- 2B events/day
- ~1.5 TB/day raw payload (≈750 B/event, not stated)
- bid + no_bid = 75-80% of event count
- Auction lifecycle bound: max 1 hour
- Duplicate arrival bound: max 1 hour
- Silver staleness: ≤30 min
- Gold grains: hourly and daily
- Raw retention: 7 days
- Users: ~10
- Four assumptions marked Confirmed, two marked Assumed

**ASSUMES (taken as given from elsewhere)**
- The test brief: analytics scope, BI availability, Yield team as the consumer, GCP
- The client conversation: 7-day retention, schema divergence across sources, no free text, two Gold grains
- `CONTEXT.md` domain model: event types, one response per invited SSP, publisher/SSP/ad-unit vocabulary
- Forward-references `part_1/00-retention-anonymisation.md` for the retention consequence
- Silently assumed and not listed: peak-to-average traffic ratio, growth rate, publisher/SSP cardinality, SSPs invited per auction, fill rate
