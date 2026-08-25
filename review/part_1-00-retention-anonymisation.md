# Review — `part_1/00-retention-anonymisation.md`

## Summary

This page takes one line of the client brief — *"raw logs are kept 7 days, aggregation anonymises"* — and turns it into the structural inversion the rest of Part 1 rests on: raw is transient, so Silver, not Bronze, is the source of truth. It lands, and it earns its position ahead of bullet 1.1; the one place it falls short is that its central privacy claim is asserted where it needed to be argued.

## Grade

| Dimension | Grade | One line |
|---|---|---|
| Decision quality | **B** | Both neighbouring boundaries (Bronze, Gold) are rejected on named grounds and six alternatives carry real reasons — but the load-bearing claim, that `auction_id` is anonymous from day 8, rests on one clause that is not true as written. |
| Narrative | **A** | Opens by inverting a convention the reader already holds ("Bronze is the source of truth"), then spends the page earning the inversion; a busy CTO knows by paragraph two why this page exists before bullet 1.1. |
| Operability instinct | **B** | Retention is table properties and lifecycle rules rather than jobs that can be paused — excellent — but the page names its own worst failure mode and gives it no detector. |
| Technical plausibility | **A** | Every platform fact checks: 48h is BigQuery's time-travel minimum, fail-safe is a fixed unqueryable 7 days, GCS soft delete defaults to 7 days, Pub/Sub caps at 31, logical billing excludes travel and fail-safe bytes; the day-16 arithmetic and the ~$200/~$210 figures reconcile with 1.2 and 2.2. |
| Signal density | **A** | ~1,019 words carrying a decision that reshapes six pages; roughly four sentences are cuttable and they are all restatement of a point already landed. |
| **Overall** | **A** | The two Bs are one-sentence repairs, not rethinks, and most submissions would not name the fail-safe residue at all. |

## Top findings

**1. [BLOCKER] The `auction_id` anonymity argument accounts for *our* re-linking key, not the SSP's.**
- **What:** "The re-linking key is Bronze, and Bronze expires: on day 8, `auction_id` is a string that groups rows and joins to nothing" is true of our copy only — the SSP that generated the auction holds the same `auction_id` beside its own user/device identifiers on its own retention schedule, and GDPR Recital 26 tests means reasonably likely to be used *by the controller or by another person*.
- **Why it matters to the evaluator:** This is the claim that licenses indefinite retention of an event-grain table; if a DPO reads it as pseudonymised-with-key-held-by-a-third-party, the whole Silver-is-durable inversion needs a legal basis the page has not supplied. The page already shows it knows pseudonymous ≠ anonymous, which makes the omission look like an argument stopped one clause early rather than a blind spot.
- **Fix:** Two sentences. Name the relative test explicitly (the SRB v EDPS line: data can be anonymous in the hands of a holder with no reasonable means of re-identification) and state why we are that holder — no contractual or technical route to the SSP's mapping. Then close the second gap: say that with `auction_id` inert, the residual Silver columns (`publisher_id`, `ad_unit_id`, `auction_timestamp` to the second, `country`, `device`) still describe one impression opportunity, and say why that combination does not single out — or narrow the claim to "unlinkable by us" and stop calling it anonymous.

**2. [QUESTION] The body's argument for keeping an event-grain layer forever is circular; the non-circular one is a row in the Rejected table.**
- **What:** "Gold is too late: Silver is retained indefinitely, so an identifier that reaches Silver persists indefinitely" presupposes what it needs to prove — Silver is retained indefinitely *because* it is the anonymisation boundary. Meanwhile the client's sentence pairs anonymisation with *aggregation*, and Silver is not an aggregation; it is raw's grain, typed.
- **Why it matters to the evaluator:** A grader holding the brief will notice the design keeps an event-per-row table forever and calls it the anonymised layer, which is one layer earlier than the client's wording implies. The real justification — Gold fixes the analysable dimension combinations at design time — is strong and is currently a table cell.
- **Fix:** Promote the "Keep only Gold, drop Silver" reasoning into the boundary section as the *reason* Silver is durable, then derive the boundary from it. One sentence conceding that this reads the client's "aggregation" as "the anonymising transformation", not "the roll-up", removes the whole objection.

**3. [QUESTION] The page names "a field nobody typed is unrecoverable after a week" as the strongest attack on the design, then leaves it undefended.**
- **What:** No mechanism anywhere in Part 1 detects a new key appearing inside the opaque `payload` — the dead-letter topic in 1.1 fires on *topic-schema* drift and on invalid JSON, neither of which a new key inside a valid `JSON` column triggers.
- **Why it matters to the evaluator:** The incident narrative celebrates that "nobody had to notice it" for an identifier we want gone — which is precisely why nobody will notice the field we wanted to keep, and the page has already conceded the loss is permanent. Naming a weakness without a cheap mitigation invites the interviewer to supply one.
- **Fix:** Add an hourly Dataform assertion over the distinct JSON key paths per `source_id` — metadata, not values, pennies to run — that alerts on a path never seen before. It turns "a wall" into "we know inside an hour what we are about to lose" without adding a component.

**4. [QUESTION] The allowlist is a real control against SSPs and no control at all against us.**
- **What:** The failure-mode asymmetry argument (allowlist loses a field; denylist keeps one) holds for fields arriving from outside, but nothing described stops an engineer adding a column next quarter that carries an identifier into a table with no expiry — the guard is a code review of a SQLX file.
- **Why it matters to the evaluator:** The page sells the typed schema as a mechanism rather than a policy ("an allowlist, not a filter"); a staff engineer will test whether the mechanism binds the insiders too.
- **Fix:** One clause: Silver's schema change is a Git diff on a reviewed model, so adding a column is the one privacy decision the design forces a human to make explicitly — which is the property being bought, not the absence of humans.

**5. [POLISH] "The five events of one auction" contradicts the volume model.**
- **What:** `CONTEXT.md` and `intro/02` both say bid/no_bid scale with the number of SSPs invited, so an auction produces 1 + N + 2 events, not five; five is the number of event *types*.
- **Why it matters to the evaluator:** It is a small slip in the one sentence that motivates keeping `auction_id`, on a page whose authority comes from precision, and 2.2 elsewhere uses the same five as a cardinality figure for `event_type`.
- **Fix:** "the cluster of events belonging to one auction" — two words, no other change.

## Cuts

1. **Line 30, final sentence** — "Naming it is also the only way to be *sure* it expires — a design that claims day 7 has no reason to check what happens on day 8." (~28 words). The preceding sentence already made disclosure the point; this restates it as a virtue. Nothing lost.
2. **Line 32, final sentence** — "**The copy nobody chose to keep still has to be disclosed, even when it is free.**" (~16 words). Third statement of the disclosure principle on one page (line 30 carries it twice). Cutting it also stops the cost paragraph editorialising, which the house rule asks it not to do.
3. **Rejected row, "Backlog retention at Pub/Sub's 31-day maximum"** (~40 words → ~15). The second half — "replay past day 7 has nothing to replay *into*" — repeats the "Silver at 13 months" row two lines above. Compress to "A deeper buffer is a longer-lived copy of the record the ceiling binds." The knob is worth showing you know about; the paragraph is not.
4. **Line 7, the middle claim** — "**Which means the medallion convention — Bronze is the source of truth — does not hold here.**" (~15 words). The paragraph states the inversion three times (the reverse / does not hold / Silver is the source of truth); the first and third are the strong ones.

Total ~85 words, ~8% of the page. Note that this is a genuinely dense page — the cuts are restatement, not substance, and there is no boilerplate or defensive hedging to find.

## Interview questions this page invites

1. **"The SSP still has that `auction_id` in its own logs, next to a user identifier, for however long it keeps them. On what basis is your Silver anonymous rather than pseudonymised?"** — *Not answered.* The page reasons only about keys we hold. See finding 1.
2. **"The client said *aggregation* anonymises. Silver is the same grain as raw and you keep it forever. Why does that satisfy the sentence?"** — *Partially answered.* The Rejected table explains why Gold-only is insufficient, but the body derives the boundary circularly and never engages the word "aggregation" after the opening paragraph. See finding 2.
3. **"You call the untyped field the strongest attack on this design. How do you find out you lost one — and who stops someone typing the wrong one into a table that never expires?"** — *Not answered on either half.* The design has no payload-key drift detector, and the allowlist's enforcement is a code review the page does not name. See findings 3 and 4.

## Claims ledger

**DECISIONS**
- Anonymisation boundary = **Silver**. Rejected: *Bronze* (stripping requires parsing the payload at ingest, reinstating the processing component 1.2 removes); *Gold* (Silver is retained indefinitely, so identifiers reaching Silver persist indefinitely).
- **Silver is the source of truth**, not Bronze; Bronze is a landing and replay buffer. Rejected: the medallion default.
- Mechanism = **allowlist** (typed schema lacks the columns). Rejected: denylist / stripping filter — fails open on a new identifier.
- `auction_id` is **kept** in Silver and not removed; Bronze expiry is what breaks linkage.
- Silver retention **indefinite**. Rejected: *Silver at 13 months* (a bounded window needs a rebuild source; none exists past day 7).
- Keep Silver **and** Gold. Rejected: *Gold only* (fixes analysable dimension combinations at design time; Silver's are fixed at query time).
- **No residual JSON column in Silver.** Rejected: the residual payload is the personal data.
- Pub/Sub subscription **and** dead-letter retention = 7 days, declared in Terraform. Rejected: the 31-day maximum.
- Bronze `partition_expiration_days = 7` as a **table property**, not a scheduled job.
- GCS bucket lifecycle 7 days with **soft-delete retention = 0**. Rejected: leaving the 7-day default (makes it 14 invisibly).
- `max_time_travel_hours = 48`. Rejected: BigQuery's 7-day default (pushes the last residue from day 16 to day 21).
- **Disclose** the fail-safe residue rather than claim day 7.
- Bronze dataset bills **LOGICAL** (asserted here, argued in 2.2).
- Quality assertion: distinct-`auction_id` count tracks the auction count (detects a session key).

**TECH**
Pub/Sub (subscription message retention, dead-letter topic); BigQuery (Bronze table, `partition_expiration_days`, `max_time_travel_hours`, fail-safe, logical storage billing); Cloud Storage (bucket lifecycle rule, soft delete); Terraform; Silver and Gold (BigQuery); "the quality job" (Dataform assertions, unnamed here).

**TERMS**
raw log; *ceiling* (a limit we do not control, binding every copy); *copy of the raw record*; anonymisation boundary; allowlist vs denylist; pseudonymous vs anonymous; *re-linking key*; source of truth; landing and replay buffer; *residue* (fail-safe bytes we cannot read, pause or extend); time travel; fail-safe; soft delete; session key; deletable vs durable.

**NUMBERS**
7 days — raw retention, every copy · 6 answers reshaped by the rule · day 7 — Bronze partition expiry · day 8 — `auction_id` unlinkable · **day 16** — last residue expires · `max_time_travel_hours = 48` (2 days) · fail-safe = 7 days, fixed · GCS soft-delete default 7 days, set to 0 · Pub/Sub retention default 7 days, maximum 31 · BigQuery time-travel default 7 days → 5 extra days → day 21 · Bronze storage ~$200/month at 7 days vs ~$2,500/month at 90 · GCS archive ~$210/month for the same week · Silver at 13 months (rejected) · "five events of one auction" (see finding 5).

**ASSUMES**
- The retention rule is client-**Confirmed** as a ceiling (`intro/02`), not a cost choice — do not re-litigate.
- Bullet 1.2 removes the stream-processing component, so no parse can happen at ingest.
- Bullet 2.2 justifies logical billing on an expiring table (and the day-16 arithmetic is reused there).
- Silver's typed schema (2.1, ~26 columns) contains no identifier columns.
- A GCS archive exists as a second export subscription (1.1 / 1.2), Standard class, same 7 days.
- A dead-letter topic exists (1.1).
- No free text anywhere in payloads (`intro/02`) — the premise that makes an allowlist sufficient.
- ~1.5 TB/day raw → ~10.5 TB per week, implied by the ~$200 / ~$210 figures.
- Infrastructure is Terraform-declared — asserted in one table cell and nowhere else in the 18 pages.
