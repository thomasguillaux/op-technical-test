# Review — `part_2/04-glossary-and-entities.md`

## Summary

This page answers the dictionary bullet by refusing its premise: the test's own example sentence contains two lookups with opposite cardinality and volatility, so it gets two mechanisms — terms injected whole from Dataform column descriptions, entities resolved live by a SQL fuzzy match — and a third problem, *"make us"*, that neither mechanism can fix. The reframe lands and the platform detail is first-hand; what wobbles is the page's own headline guarantee (definitions "cannot drift... because they are the same file") and the fact that the ambiguity section names a default it never implements.

## Grade

| Dimension | Grade | One line |
|---|---|---|
| Decision quality | **B** | Every option the bullet names is rejected with a reason and the vector DB gets a reinstate condition — but the condition names a variable that will never fire (context window), and the no-drift claim collides with 2.1's four-views-over-one-`includes` structure. |
| Narrative | **A** | Splits one quoted sentence into three distinct problems and gives each a different mechanism; the reader ends holding a rule ("make the model's reading explicit, not guaranteed") rather than a list of options. |
| Operability instinct | **B** | The cost paragraph names the cost that appears on no bill and the incident narrative is the right one (a client won this morning, asked about at 15:00) — but nothing detects the failure this design actually has: a column shipped with no description. |
| Technical plausibility | **A** | `COLUMN_FIELD_PATHS` is the right `INFORMATION_SCHEMA` view (`COLUMNS` has no `description` — that detail is only known by someone who hit it), the `EDIT_DISTANCE` cap semantics are correct, `SOUNDEX` and `CURRENT_DATE() - 30` are valid GoogleSQL. One date to re-verify. |
| Signal density | **A** | 1,194 words, no boilerplate, no hedging; the compressible material is one restated principle and one over-argued table cell. |
| **Overall** | **A** | Four of the five findings are one-clause repairs, and the entity/term split is an insight most submissions will not have. |

## Top findings

**1. [QUESTION] The *"make us"* section identifies the ambiguity precisely and then implements nothing.**
- **What:** The page says the analyst almost always means gross and that the copilot states the definition it used — but the synonym block shown (`"what a publisher makes, what a site earns, turnover, top line"`) deliberately does not contain the test's own phrase, so nothing in the artifact makes the model answer gross; the default lives only in the prose of this review page, and disclosure is a label on whatever the model already chose.
- **Why it matters to the evaluator:** This is the exact sentence the bullet quotes, so it is where a grader looks first, and the page has both mechanisms on it — entity ambiguity triggers a clarifying question, term ambiguity gets a unilateral pick — without ever arguing the asymmetry.
- **Fix:** Put the disambiguation in the description text where everything else lives (`gross_revenue`: *"'make us' is ambiguous — answer this and name it"*), and add the structural reason the default is gross rather than an appeal to what analysts usually mean: the retained-share reading maps to no column in Gold (only `gross_revenue` and `publisher_payout` exist), so one reading is a column and the other is arithmetic. Then one sentence on the asymmetry: a wrong entity is invisible in the answer, a wrong definition is printed in it — which is why one asks and the other discloses.

**2. [QUESTION] "A metric definition cannot drift from the query implementing it, because they are the same file" — but 2.1 puts the arithmetic in an `includes` file shared by four views.**
- **What:** The objects the copilot can name are the four semantic views (3.1), so the descriptions must be declared on those views' `config` blocks; the ratio expressions live in one Dataform `includes` file that all four reference (2.1, line 27). Description and expression are therefore in different files, and the same description is authored up to four times — hourly and daily, opportunity and SSP.
- **Why it matters to the evaluator:** This is the page's bolded guarantee, and the drift it claims to have eliminated is exactly the drift 2.1 spends a paragraph eliminating for the expressions. A reader who has both pages open finds it in thirty seconds.
- **Fix:** One clause: the column descriptions live in the same `includes` file as the ratio expressions and are spread into each view's `columns` block, so one definition and one implementation move together across all four views. That restores the claim literally instead of weakening it.

**3. [QUESTION] Nothing detects a column that ships without a description.**
- **What:** The prompt block is generated from `COLUMN_FIELD_PATHS` at request time, so a new metric merged without a `columns` entry silently produces a dictionary with a hole — and the model does not fail, it infers the meaning from the column name and answers fluently.
- **Why it matters to the evaluator:** The whole design rests on the dictionary being complete and current; every other mechanism on this page has a named failure mode and this one, the likeliest in practice, has none. Part 1 already uses Dataform assertions, so the absence reads as an oversight rather than a scoping choice.
- **Fix:** A Dataform assertion over the same query the prompt uses — fail the build when any column in the semantic dataset has a `NULL` description. No new component, one file, and it converts "someone forgot" from an invisible answer-quality problem into a red build.

**4. [QUESTION] The condition that reinstates the vector database names the wrong variable.**
- **What:** "A vector store is the right answer when the corpus outgrows the context window" sets a threshold two and a half orders of magnitude away — a few thousand tokens against a million-token window — so as written the condition never fires and is not a condition. The one that would actually flip the decision is already on the page as an argument: free text entering the schema, which the client says does not exist.
- **Why it matters to the evaluator:** Every other rejection in this document carries a reinstate condition someone could plausibly hit; this one carries a rhetorical one, on the option the test names most prominently.
- **Fix:** Swap them. Reinstate on *"the day a free-text field enters the data — a creative name, a deal note, a support ticket — because semantic search needs something to search"*, and demote the window argument to the clause it already is. While there, soften "sending all fifty never does": injecting the whole corpus removes retrieval error and leaves selection error, which is the subject of the next section — say so and the two sections interlock instead of mildly contradicting.

**5. [POLISH] The Data Catalog row spends its length on the checkable claim and buries the load-bearing one.**
- **What:** Two of its three arguments are product trivia — a discontinuation date (the shutdown date Google published for Data Catalog is 2026-01-30, not 2026-06-01; worth re-verifying before it is defended live) and a rename — while the argument that actually decides it is "the LLM does not read a catalog; something would have to export it into the prompt". And that sentence is contradicted inside this document: 1.2 says Google's Conversational Analytics API reads *"a Knowledge Catalog glossary with synonyms"*.
- **Why it matters to the evaluator:** A dated product claim is the one thing on the page a CTO can check in twenty seconds, and it buys nothing the next clause does not; a general claim falsified by a sibling page is worse.
- **Fix:** Lead the row with the export argument, narrow the general claim to *our* loop ("our agent reads a prompt, not a catalog — the one product that reads one is the CA API, rejected in 1.2"), and keep the discontinuation as a half-clause without leaning on the date.

## Cuts

1. **Line 26** — "**A synonym and the definition it belongs to cannot be edited apart**, and neither reaches the prompt without the reviewer of the SQL having seen it." (~25 words). Third statement of co-location: line 18 already says "changed in the same pull request as the SQL", line 20 says "they are the same file". Nothing lost.
2. **The Data Catalog rejected row** (~75 → ~30 words, saving ~45). Three arguments where one decides it, and the two being cut are the two that carry risk (see finding 5). What is lost: the signal that the author tracks GCP product churn — already demonstrated on 1.2 with better-anchored dates.
3. **The vector-database row, first clause** (~25 words). "A vector store is the right answer when the corpus outgrows the context window, and ours does not — a few dozen definitions, a few thousand tokens" restates line 14 and the cost paragraph. Open the row on the free-text argument, which appears nowhere else on the page.
4. **Line 14, second sentence** (~15 words) — cut or reframe per finding 4. As written it is an overclaim the page itself refutes fifteen lines later.

Total ~110 words, ~9%. This is a dense page; there is no padding to find, only restatement.

## Interview questions this page invites

1. **"You have four semantic views sharing one `includes` file for the arithmetic. Where is the column description written, and how many copies of it exist?"** — *Not answered.* The page asserts one file without saying which, and 2.1's structure implies at least two. See finding 2.
2. **"Someone ships a new metric next sprint and forgets the description. What does the copilot answer, and how do you find out?"** — *Not answered.* The prompt is assembled from live metadata, so the dictionary degrades silently and the answer still renders. See finding 3.
3. **"An analyst says 'Le Figaro' and the column holds `lefigaro-fr-web`. Edit distance is well past 3 and SOUNDEX is comparing different strings. What comes back?"** — *Partially answered.* The `< 4` versus `<= 4` subtlety is handled precisely, but the threshold is absolute rather than length-normalised, so it is simultaneously too loose on four-character IDs and too tight on spoken shorthand against a canonical ID; the "ranked candidates, ask when close" rule mitigates a near-miss and does nothing for an empty result. The page also assumes, without establishing it anywhere, that the normalised `publisher_id` is the name the Yield team says out loud — while `intro/02` says every source names things differently.

## Claims ledger

**DECISIONS**
- Data dictionary = table and column `description`s in the Dataform SQLX `config` block, injected into the prompt whole. Rejected: *vector database* (corpus fits; no free text to search; if it ever outgrew the window, BigQuery `VECTOR_SEARCH`, not a separate service), *data catalog* (a human discovery surface; an LLM cannot read one; sits downstream of the SQLX anyway), *dbt tags* (runtime removed in Part 1), *hand-maintained synonym table* (second source of truth).
- **Two mechanisms, not one**, because the test's example is two lookups: terms **injected whole** (few dozen, low volatility), entities **queried live** (high cardinality, changes as business is won/lost). Rejected: a single retrieval mechanism over both.
- Definitions live in the SQLX, not the prompt — a prompt is a deploy artefact nobody who owns a metric reviews. Changed in the same PR as the SQL.
- Prompt dictionary block generated **at request time** from `INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`.
- Synonyms embedded **inside the description text**, because BigQuery has no synonym field.
- *"Make us"* is irreducibly ambiguous; default reading is **gross**, and the mechanism is 2.1's rule that the copilot states the definition it used. Rejected: a better/larger synonym list.
- `resolve_entity` = SQL fuzzy match over live dimension values in the semantic views, not an index. Rejected: *a vector index over entity names* (a copy of a dimension table with a staleness problem the table lacks), *letting the model guess* (confident wrong-client answer).
- No mapping table: `publisher_id` / `ad_unit_id` values are themselves the human-readable names.
- `EDIT_DISTANCE(..., max_distance => 4)` with filter `distance < 4`; `SOUNDEX` as an OR branch; 30-day window on live names (wider lets churned names compete); `LIMIT 5`.
- Tool returns **ranked candidates, not an answer**; the copilot asks when two score close. Rejected: silently picking the nearest.

**TECH**
Dataform (SQLX, `config` block, column descriptions, build-time publication to BigQuery); BigQuery (`INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`, `description`, `EDIT_DISTANCE` + `max_distance`, `SOUNDEX`, `LOWER`, `CURRENT_DATE()`, `VECTOR_SEARCH`, `v_opportunity_daily`); Git / pull request; Google Data Catalog (discontinued) and Knowledge Catalog (successor); dbt tags, dbt runtime (rejected); vector database, embedding pipeline / index / re-indexing job (rejected); `resolve_entity` tool (from 1.1); the prompt block at hop 2 (from 1.2).

**TERMS**
*entity* vs *term* (the two halves of one question, split by cardinality and volatility); *injected whole*; *queried live*; *retrieval risk*; *deploy artefact*; *source of truth* (for vocabulary); *synonym* (a phrase inside a description, not a catalogued object); *ranked candidates*; *the cost that appears on no bill*; *staleness failure*; gross vs net revenue reading of "make us".

**NUMBERS**
Hundreds of publishers · "far more" ad units · a few dozen term definitions · "fifty items" (used twice as the corpus size) · a few thousand tokens injected per request · `max_distance => 4`, filter `< 4`, "misspelt by more than three characters" · 30-day live-name window · `LIMIT 5` · Data Catalog discontinued **2026-06-01**; Knowledge Catalog rename **April 2026** · €12,400 (illustrative answer) · `resolve_entity` scan cost = "cents".

**ASSUMES**
- 2.1's four semantic views exist, define every ratio, and carry the rule that the copilot states the definition it used — this page's entire close depends on that rule.
- 1.1 declares `resolve_entity` and the failure class "a confident, well-formed answer about the wrong client".
- 1.2 assembles the prompt at hop 2 and already states that RAG is two mechanisms here.
- 3.1 grants the agent the semantic dataset only, so the entity lookup necessarily reads a view rather than a base table.
- Part 1 removed the dbt runtime (making "dbt tags" dead) and has **no dimension tables**, so live dimension values only exist inside fact-derived views.
- Client-confirmed *"pas de texte libre, que des données liées aux enchères"* (`intro/02`) — the premise that removes semantic search's job.
- **"Hundreds of publishers"** is used as a load-bearing cardinality figure but does not appear in `intro/02`'s assumption table (it comes from the brief).
- `publisher_id` / `ad_unit_id` hold spoken business names rather than per-source or opaque keys — asserted here only.
- Dataform publishes `config` descriptions to BigQuery on every build, including for views.
