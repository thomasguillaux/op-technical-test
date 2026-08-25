# Review — `introduction.md`

## Summary

A 66-word routing stub that tells the reader two framing pages come before the design, names what each one contains, and promises the rest follows the test's bullet order. It routes correctly and wastes nothing, but it spends the document's first ten seconds announcing a delay instead of landing the one claim that would make a CTO want to keep reading.

## Grade

- **Decision quality — B.** The page makes exactly one visible editorial decision (body ordered by the test's bullets, not the author's dependency order) and states it; the other decision — that framing precedes design at all — is asserted, never defended.
- **Narrative — C.** "Two pages before the answers" is a deferral, and the strongest sentence in the entire write-up ("Every component in this design survived an argument for deleting it. Several components named in the test did not.") is sitting one click away, unspent.
- **Operability instinct — B.** Correctly out of scope for a stub; nothing here to get wrong, and nothing here earning credit.
- **Technical plausibility — A.** No technical claims, and both routing claims are accurate against the pages they point at — a staff engineer has nothing to push back on.
- **Signal density — B.** Four sentences, no padding, admirable restraint against the 600-word preamble most candidates write — but only one of the four (the bullet-order line) carries information a reader could not have guessed.
- **Overall — B.** The brevity and the bullet-order sentence are deliberate and read as such; the missing thesis is the one visible soft spot.

## Top findings

**1. [BLOCKER] The page has no thesis.**
- **What:** The first page after Home tells the reader what genre of content is coming ("how the design was argued") rather than what the design is or what is unusual about it.
- **Why it matters to the evaluator:** A CTO forms their read of a candidate in the first screen; here the first screen says "not yet" — and the fact that would earn attention (three of the five components the test names were deleted, with reinstate conditions) is 1,200 words downstream, behind two pages the reader has just been told are not the answers.
- **Fix:** Hoist one line of thesis above the bullets — e.g. "The design keeps Pub/Sub, Cloud Storage and BigQuery, and deletes Dataflow and Composer; both pages below exist to show that this was argued, not assumed." Two of the three top-level pages already carry a summary; this one is the only routing-only exception, so the fix is also a consistency fix.

**2. [QUESTION] "What it was allowed to assume" undersells the strongest thing on the page it points at.**
- **What:** The phrase reads as permission-seeking and implies guessing, when four of the eleven lines on `02-business-assumptions.md` are marked **Confirmed** — i.e. the author went back to the client and asked.
- **Why it matters to the evaluator:** "Went and confirmed the four requirements that move the design" is a hiring signal; "was allowed to assume" is a candidate hedging about scope, and an interviewer will read the weaker of the two.
- **Fix:** Replace with "what was confirmed with you, and what is assumed on top" — the distinction is already the table's `Source` column, so the introduction only has to stop hiding it.

**3. [POLISH] No fast path through an 18-page document.**
- **What:** The stub routes to the next two pages but gives no sense of scale or priority for the other sixteen.
- **Why it matters to the evaluator:** A reader with twenty minutes will pick their own three pages and may pick badly; a candidate who names the three load-bearing ones is demonstrating editorial judgement about their own work.
- **Fix:** One line after the bullets — "If you read three pages: the retention ceiling, the component verdicts, and the guardrails." Costs 15 words, replaces a guess with a recommendation.

**4. [POLISH] The Methodology routing line leads with a formatting convention.**
- **What:** "why every section ends with a **Rejected** table" describes the layout of the page rather than the claim the table encodes.
- **Why it matters to the evaluator:** It makes a genuinely differentiating method (rejected option *plus* the condition that reinstates it) sound like a document template.
- **Fix:** Route on the claim instead — "the rule that removed Dataflow, Composer and dbt Core, and the condition that brings each back."

## Cuts

**1. "Two pages before the answers:" (5 words).** Announces a delay in the document's first five words. Nothing is lost by deleting it — the two bullets immediately below already show there are two pages — and the space is where the thesis from finding 1 goes.

**2. The Methodology bullet's descriptor, ~18 words → ~9.** "why every section ends with a **Rejected** table, and how each decision was argued down to what survived" says the same thing twice: the Rejected table *is* the argued-down decision. Keep one half. **~9 words saved**, nothing lost.

**3. "Everything after these two pages follows..." → "Everything after follows the test's bullets, in the test's order." (~4 words).** "these two pages" restates the list that ends one line above. Keep the sentence — it is the highest-value line on the page for a grader checking boxes — just stop it re-introducing its own context.

**4. The `Next:` footer, ~8 words — flagged, not recommended.** It is the third link to `01-methodology.md` inside 66 words. The horizontal rule and repeat earn their place everywhere else in the document as an unbroken chain; on the one page where the target is six lines up, they are duplication. Real tradeoff: consistency of the convention against 8 words. If the convention stays, that is a defensible call — but it should be a call, not an oversight.

## Interview questions this page invites

1. **"Give me the one-sentence version of the architecture."** *Not answered here.* It exists on `part1-pipeline.md`, two clicks away; a reader who bounces off the introduction never reaches it. This is finding 1 restated as the question it will actually be asked as.
2. **"Which of these assumptions did you confirm with us, and which did you invent?"** *Not answered here*, and actively muddied by "allowed to assume". Fully answered one page later by the `Source` column — the introduction should be pointing at that column, not obscuring it.
3. **"Why do I need two pages of method before I see a design — is the thinking in the preamble or in the design?"** *Not answered.* The page asserts that framing comes first without giving a reason to accept it; the nearest defence is `01-methodology.md`'s "How to attack it", which the reader reaches only by complying with the ordering they are questioning. One clause here ("both exist so that every later verdict can be tested, not taken") would pre-empt it.

## Claims ledger

**DECISIONS**
- Two framing pages (Methodology, Business assumptions) precede the design content — alternative not stated.
- Body content ordered by the test's own bullets, in the test's order — alternative (author's dependency order) not stated on this page.
- The introduction is routing-only, carrying no design summary — alternative not stated; diverges from the two sibling top-level pages, which are summary *and* routing.
- Methodology is routed to before Business assumptions — ordering not justified on this page.

**TECH**
- None named on this page.

**TERMS**
- *Methodology* — used here to mean "how each decision was argued down to what survived".
- *Business assumptions* — used here to mean "requirements only, never mechanisms".
- *Rejected table* — named, not defined; defined on the page it links to.
- *the answers* — Parts 1 and 2, i.e. everything after the two framing pages.
- *the test* — the source exercise; assumed to have numbered bullets and a fixed order.

**NUMBERS**
- "Two pages" of framing before the answers. (The only quantitative claim on the page.)

**ASSUMES**
- `/intro/01-methodology.md` and `/intro/02-business-assumptions.md` exist and contain what the bullets say. *(Verified true.)*
- The test has an explicit bullet structure and order that the write-up can mirror. *(True; bullets are quoted verbatim on each numbered page.)*
- The reader arrives from `README.md` or the sidebar and already knows this is a response to a technical test — the page never says so itself.
- The **OptimusAds** anonymisation convention, which is stated on the next page, not here. Deliberate and correct; noted only for cross-page tracking.
- That the reader will read linearly. The page provides no priority ordering for the remaining sixteen pages.
