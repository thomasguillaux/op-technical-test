# Review — `intro/01-methodology.md`

## Summary

This page sets the frame for the whole write-up: it argues that components were derived from requirements rather than assumed from the test's own list, and it tells the reader how to attack what follows. It mostly lands — the opening two lines are the best framing device in the document — but two of its checkable claims about the pages downstream are inflated, which is an expensive place to be caught on a page whose subject is rigour.

## Grade

| Dimension | Grade | One line |
|---|---|---|
| Decision quality | **B** | The reinstate-condition device is real judgement — a rejection is a claim about *this* volume, not about the product — but the page never concedes the cost of its own delete-by-default bias. |
| Narrative | **B** | Strong epigraph, clear arc, ends by inviting attack; the middle section spends ~100 words on house formatting conventions, and the best line is repeated verbatim on `part1-pipeline.md`. |
| Operability instinct | **B** | "Volume, latency, team size or budget" is exactly the right set of axes for when a rejected component returns; it is asserted as a property of the pages more than it is delivered by them. |
| Technical plausibility | **C** | The only checkable technical claim on the page — one sentence killed six components — does not survive reading the two pages it points at; Part 2 itself attributes that sentence to four. |
| Signal density | **B** | 573 words is right for a frame page, but the private-notes flex and the cost-convention paragraph are inward-facing and buy the reader nothing. |
| **Overall** | **B** | A confident, well-shaped frame with one soft spot: it promises slightly more of the downstream pages than they deliver. |

## Top findings

**1. [BLOCKER] The six-component claim over-counts.**
- **What:** "A single sentence that killed six components at once — *a runtime we operate, placed between us and something we could call directly*" holds cleanly for Dataflow, dbt Core, Cube and LangChain, but Composer loses on "right for a mixed DAG; this one has a single system in it" and the vector database loses on "the corpus fits the context window / no free text" — the runtime rule is cited there only for a hypothetical future. `part_2/02-agent-flow.md` names four components for that sentence, not six.
- **Why it matters:** This is the page's signature line, it is offered as proof of method over taste, and a grader who follows the two links it makes finds a different count in the author's own words.
- **Fix:** Say four and name them, or keep six and add the half-clause that makes the other two fit (Composer: Dataform is the managed substitute, so the runtime *is* the objection; vector DB: the standalone index is the runtime, and corpus size is why the trade never gets close). Reconcile with `part1-pipeline.md:31` and `part_2/02-agent-flow.md:31` either way.

**2. [BLOCKER] The Rejected tables do not carry the "load-bearing half" the page says they do.**
- **What:** "The table gives the reason it lost *and* the condition that brings it back — the condition is the load-bearing half." Every Rejected table in the document is two-column, `Option | Why not`; across roughly fifty rows, a reinstate condition appears in a handful (Dataflow's "kept as the fallback if the producer will not supply the split", Composer's "Dataform's API lets us add it later").
- **Why it matters:** A reviewer who reads the frame page and then flips to any Rejected table finds the promise unmet on the first try, and the promise is the one the page rests its testability argument on.
- **Fix:** Narrow the claim to what `part_1/02` actually delivers — "where the test names the component, the table also gives the condition that brings it back" — or add the third column to the tables. The narrow version is already true and still strong.

**3. [QUESTION] The method never states its own failure mode.**
- **What:** Delete-by-default is presented as pure gain; the page never names what it costs.
- **Why it matters:** The CTO's private reaction to a six-service architecture is "this is a design one person can defend, not one five engineers can operate" — and the page has an answer (the reinstate condition is precisely the safeguard against premature minimalism) but never says so.
- **Fix:** One sentence in *How to attack it*: minimalism is a bet on this volume and this team, the reinstate conditions are where the bet is written down, and name the axis that trips first — a second source system, or the second engineer.

**4. [QUESTION] Rule 1 is unfalsifiable as written.**
- **What:** "I listed the scope as a dozen open questions ... before settling one" is a claim about process that leaves no trace the reader can check, unlike rules 2 and 3, which point at artefacts.
- **Why it matters:** On a page arguing "the option that lost is the part a reviewer can test", an untestable rule sits badly.
- **Fix:** Point at its output — the Given/Derived/Confirmed marking on `intro/02-business-assumptions.md` is what "no early convenience quietly decided a later question" looks like on the page.

**5. [POLISH] The private-notes paragraph invites a question with no upside.**
- **What:** "Behind it sits the longer material — one file per decision, reversals included — which stays private on purpose."
- **Why it matters:** It tells a reviewer there is a better document they are not being shown, and the only follow-up available is "can I see it?"
- **Fix:** Cut to the rule that actually matters and is already in the next sentence: a superseded position appears as a rejected alternative in the present tense, never as a reversal.

## Cuts

**1. Lines 26–28 — the private-notes flex and the cost convention (~85 words).**
"Behind it sits the longer material ... stands without the figure." The reader does not need to be told that costs live in marked paragraphs; they will see it on the first page that has one, and telling them in advance is house-rules documentation pointed at the author. Keep only "Where I changed my mind, the argument that won is here in the present tense; the fact that I once held the other position is not." **Lost:** nothing a CTO uses.

**2. The verbatim duplication with `part1-pipeline.md:31` (~35 words on one of the two).**
"One rule applied six times is a design. Six separate verdicts would be taste" appears identically on both pages, two clicks apart. **Recommendation:** keep it here, where it is the payoff of the three rules, and trim the downstream copy to the sentence plus the component list. **Lost:** Part 1's summary loses a flourish it does not need — the six names carry it.

**3. Line 6, the anonymisation note (~35 words, move rather than delete).**
It is necessary exactly once, but sitting between the epigraph and the first argument it costs the opening its momentum. Move to the page footer or to `introduction.md`. **Lost:** nothing; the note is context, not argument.

**4. Line 18, second half (~15 words).**
"...is one I can source on the spot" is a promise; the three examples before it are the evidence. The examples do the work alone.

## Interview questions this page invites

1. **"You say each rejection carries the condition that brings the component back. Show me the one for dbt Core. For BigLake."** *Not answered* — only Dataflow and Composer carry one, and the page generalises from those two.
2. **"Your rule deletes runtimes you operate. Dataform is a runtime, and a Pub/Sub BigQuery subscription is a transform you don't control and can't test. Where exactly is the line?"** *Not answered here.* `part1-pipeline.md` offers "a build step is not a runtime", which the methodology page — the page that owns the rule — should be the one to state.
3. **"What did you get wrong, and what changed your mind?"** *Deliberately refused.* Keeping reversals off the page is a defensible editorial choice for a document, but the question gets asked out loud, and the page currently reads as pre-declining it. Worth having one reversal ready to give warmly in the room.

## Claims ledger

**DECISIONS**
- Derive components from requirements, then argue for deleting each — rejected: drawing the components the test names and connecting them.
- End most sections with a **Rejected** table giving reason + condition to reinstate — rejected: publishing only the chosen option.
- Rule 1: enumerate all open decisions before settling any — rejected: sequential settling, where an early convenience decides a later question.
- Rule 2: check figures against primary documentation — rejected: recollection.
- Rule 3: record the argument (requirement satisfied + alternative beaten) — rejected: recording the conclusion alone.
- Write-up is self-contained; no links into working notes — rejected: linking to a decision log.
- Working notes (one file per decision, reversals included) stay private — rejected: publishing the design's history.
- Superseded positions appear as present-tense rejected alternatives — rejected: narrating reversals.
- Cost confined to a marked per-page paragraph; the argument above it stands without the figure — rejected: cost running through the prose.
- Some detail deferred to live conversation rather than written down.
- Company anonymised to **OptimusAds**; nothing else changed.

**TECH** (all named only as rejected): Dataflow, Composer, dbt Core, Cube, LangChain, vector database.

**TERMS**
- *Rejected table* — closing table of an option, why it lost, and (claimed) the condition that reinstates it.
- *Condition that brings it back* — the reinstatement trigger; called "the load-bearing half".
- *"Requirements are the input; components are the output."*
- *"A runtime we operate, placed between us and something we could call directly."* — the recurring rejection rule.
- *Marked cost paragraph* — cost is quarantined per page, never in prose.
- *Self-contained* — every load-bearing argument written on the page that makes the claim.
- Referenced numeric arguments, not stated here: *the partition-grain delta*, *the streaming rates*, *the 7-day retention arithmetic*.

**NUMBERS**
- 6 components rejected by one sentence — 3 in Part 1 (Dataflow, Composer, dbt Core), 3 in Part 2 (Cube, LangChain, vector database). *Conflicts with `part_2/02-agent-flow.md:31`, which attributes it to 4.*
- "A dozen open questions" scoped before any was settled.
- 7-day retention, referenced as an arithmetic (defined in `intro/02` and `part_1/00`).
- One private file per decision.
- No cost, latency or SLA figure on this page — consistent with its own rule.

**ASSUMES**
- The brief names candidate components (Pub/Sub, Dataflow/Beam, Cloud Storage, BigQuery, Airflow/Composer; dbt Semantic Layer / Cube / BigQuery views; LangChain / FastAPI; dbt tags / data catalog / vector database) — the "components named in the test" this page rejects.
- `part_1/02` rejects Dataflow, Composer, dbt Core; `part_2/03` rejects Cube; `part_2/02` rejects LangChain; `part_2/04` rejects the vector database.
- Every numbered page ends with a Rejected table and carries a marked cost paragraph.
- `intro/02-business-assumptions.md` holds the requirements everything else rests on.
- The 7-day raw-retention rule is client-given.
- The repository is public (basis for anonymisation).
