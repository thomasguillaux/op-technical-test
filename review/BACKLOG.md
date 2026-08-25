# BACKLOG

Consolidated from the 21 files in `review/` (18 per-page reviews, `SYNTHESIS.md`, `00-MAP.md`, `metrics.md`).

Read section 5 first. The document grades well; the volume below is a function of 21 independent readers, not of 21 problems.

**Status legend:** all items are `PENDING`. Classes: `CUT` (deletion, executes directly) · `MECHANICAL` (consistency/relocation/arithmetic already implied, executes directly) · `DIAGRAM` (edit `diagrams_src/`, re-render) · `RATIFY` (fix supplied, contains a design choice — author replies ACCEPT / MODIFY / REJECT) · `AUTHORED` (needs reasoning only the author has).

---

## 1. MUTUAL CUTS — RESOLVE BEFORE WAVE 1

Seven places where two or more reviews each delete the same content on the grounds that the *other* page carries it. Applying both sides removes the content from the document entirely, and no single diff shows it. Each entry names the owner and marks which cut is conditional.

### MC-1 — "One rule applied six times is a design; six separate verdicts would be taste" + the six-component roster

- **Content:** the payoff sentence of the runtime rule, plus the roster of components it deletes.
- **Pages:** `intro/01-methodology.md`, `part1-pipeline.md`, `part_1/02-component-justification.md` (verbatim on all three).
- **The collision:** `intro/01`'s Cut 2 says *"keep it here, where it is the payoff of the three rules, and trim the downstream copy."* `part1-pipeline`'s Cut 5 says *"This page is the right home for it — cut it from one of the other two."* `part_1/02`'s Cut 1 says *"This page is where the sentence is actually earned … so the deletion belongs upstream."* Three pages, three claims of ownership, each licensing deletion of the other two.
- **Owner: `intro/01-methodology.md`.** It states the three rules; the sentence is their payoff, and it is where a reader first meets the rule. `SYNTHESIS` §2 agrees.
- **Therefore:**
  - `intro/01` **keeps** the sentence and the canonical roster. Its Cut 2 executes as written (trim the downstream copies), not as licence to delete its own.
  - `part1-pipeline`'s copy compresses to the six names only — **conditional on `intro/01` keeping the sentence.**
  - `part_1/02`'s copy compresses to the payoff clause (*"The same sentence deletes dbt Core below, and three more components in Part 2"*) — **conditional on `intro/01` keeping the sentence.**
  - `part1-pipeline`'s Cut 5 and `part_1/02`'s Cut 1 are **not** to be read as deletions from `intro/01`.

### MC-2 — The cost convention ("no total anywhere; each page prices its own decision")

- **Content:** the statement of the rule that costs live in marked per-page paragraphs and no TCO total exists.
- **Pages:** `intro/01-methodology.md`, `part1-pipeline.md`.
- **The collision:** `intro/01` Cut 1 deletes the cost-convention paragraph (~85 w) because *"they will see it on the first page that has one, and telling them in advance is house-rules documentation."* `part1-pipeline` Cut 3 deletes its sentence (~22 w) because *"the convention is already stated in `intro/01-methodology.md`."* Each defers to the other. Apply both and the document never says why there is no total — a CTO reads the absence as an omission rather than a rule.
- **Owner: `intro/01-methodology.md`, as one clause, not a paragraph.** A reader hits it before any cost paragraph, which is the only place a rule about cost presentation does work.
- **Therefore:**
  - `intro/01` keeps **one clause** ("cost is confined to a marked paragraph per page; no total anywhere, so no argument rests on a figure") and cuts the remaining ~60 w. This is C-03.
  - `part1-pipeline`'s cut executes — **conditional on that clause surviving on `intro/01`.**

### MC-3 — The house-convention meta ("each page stands alone and ends with the options it rejected")

- **Content:** the sentence describing the per-page structure.
- **Pages:** `intro/01-methodology.md`, `part1-pipeline.md`, `part2-llm-agent.md`.
- **The collision:** a deferral chain, not a pair. `part1-pipeline` Cut 4 deletes it because it *"restates the methodology page a second time."* `part2-llm-agent` Cut 4 deletes it because it is *"word-for-word `part1-pipeline.md`"* — a justification that evaporates the moment `part1-pipeline`'s copy is cut. `intro/01` Cut 1 deletes an adjacent block on the same page. Executed in sequence by three different diffs, all three copies can disappear.
- **Owner: `intro/01-methodology.md`.**
- **Therefore:** both downstream cuts execute — **conditional on `intro/01` retaining one sentence of the convention.** If `intro/01`'s Cut 1 is widened, the downstream cuts must be reverted, not the reverse.

### MC-4 — "A logical view stores no bytes" (the semantic-layer cost claim)

- **Content:** the cost answer for the whole semantic layer — a view stores nothing and adds no maintenance line.
- **Pages:** `part_2/03-semantic-layer.md`, `part_2/05-query-layer.md`.
- **The collision:** `part_2/05` Cut 4 deletes its cost paragraph because *"2.1's cost paragraph already says a logical view stores nothing."* `SYNTHESIS` §2 assigns ownership the other way — *"The view-stores-no-bytes cost paragraph | `part_2/03`, `part_2/05` | **`part_2/05`** — the price table lives there."* Apply both and Part 2 carries no statement that its semantic layer is free.
- **Owner: `part_2/05-query-layer.md`.** The three-layer price table is there; the claim is that table's row zero, and `part_2/05` is where a reader is asking the cost question.
- **Therefore:**
  - `part_2/05` **keeps** the claim. Its own Cut 4 is **rejected** — recorded here so it is not re-applied from the per-page file.
  - `part_2/03`'s cost paragraph compresses to a forward reference — **conditional on `part_2/05` keeping the claim.**

### MC-5 — "A build step is not a runtime"

- **Content:** the boundary of the runtime rule — the answer to *"Dataform is a runtime you operate; where exactly is the line?"*
- **Pages:** `part1-pipeline.md` (states it), `intro/01-methodology.md` (owns the rule, does not state the boundary), `part_1/02-component-justification.md` (shows the templating, does not state the boundary), `part_1/06-dedup-sql.md` (defends the template at length, and its Cut 2 deletes that defence).
- **The collision:** `part1-pipeline` Cut 2 deletes the clause and relocates it — *"it belongs in 1.2 where the templating is actually shown."* `intro/01`'s interview Q2 says the opposite — *"`part1-pipeline.md` offers 'a build step is not a runtime', which the methodology page — the page that owns the rule — should be the one to state."* `part_1/06` Cut 2 simultaneously removes the only extended defence of the compile-time template. Two proposed destinations and three deletions: if the relocation half is skipped, the answer to the most obvious challenge to the document's signature rule exists nowhere.
- **Owner: `intro/01-methodology.md`.** It owns the rule, so it owns the rule's boundary; placing it there also closes `intro/01`'s own open interview question, which no other placement does.
- **Therefore:** `part1-pipeline`'s cut executes **only in the same commit that lands the clause on `intro/01`.** `part_1/06`'s Cut 2 executes unconditionally (it removes a defence of a *different* claim — that the macro is compile-time — which nobody attacks).

### MC-6 — Non-overlapping `valid_from`/`valid_to` on the revenue-share table

- **Content:** the correctness property that overlapping validity windows would fan out duplicates after dedup.
- **Page:** `part_1/06-dedup-sql.md` — a single review whose two cuts name opposite survivors.
- **The collision:** Cut 1 lists *"overlapping validity windows"* among the Rejected rows to **keep**, *"whose argument appears nowhere else."* Cut 3's heading names *"the tail of the loud-vs-silent paragraph"* as the cut, while its body says *"Keep it in one place — the prose."* Read literally, one cut deletes the prose and the other's premise is false. An implementer applying both by heading deletes both copies.
- **Owner: the prose**, where the loud-vs-silent frame the argument depends on lives.
- **Therefore:** the Rejected row goes; Cut 1's "keep" list is corrected to drop *"overlapping validity windows"*; the prose tail stays. Recorded as C-12.

### MC-7 — The catchability argument (either/or hazard, not a reciprocal deferral)

- **Content:** the thesis that an explanation cannot be sanity-checked by its recipient — the load-bearing idea of Part 2.
- **Pages:** `part_2/01-question-classes.md` (owner), restated on `part_2/02` hop 9, `part_2/03` lines 83-85, `part2-llm-agent`.
- **The collision:** `part_2/02` Cut 1 and `part_2/03` Cut 1 both delete their restatements and defer to `part_2/01`. `part_2/01`'s own Cut 2 is an **either/or** — *"The catchability table … **or** the two paragraphs at 23-25 — **not both**"* — and its Cut 1 deletes the italic third statement. Three deletions plus an either/or read as two is enough to strip the thesis to a table row.
- **Owner: `part_2/01-question-classes.md`, and specifically its prose** (which carries the €12,400-vs-SSP-3 contrast the table does not).
- **Therefore:** on `part_2/01` the prose survives and the table compresses to a one-line mapping. The downstream cuts on `part_2/02` and `part_2/03` execute **only against that surviving prose.** Separately, `part2-llm-agent`'s finding 3 wants `part_2/01`'s *honest limit* sentence hoisted **up** — that is an addition to the summary, not a restatement to delete (M-19).

### Checked and confirmed *not* mutual

Recorded so they are not re-opened: retention logic (`part_1/03`, `part_1/04` both defer to `part_1/00`, which keeps it) · Cloud Logging's justification (`part_1/02` defers to `part_1/01`, which keeps it) · the envelope definition (`part_1/03` defers to `part_1/01` hop 1, which keeps it) · the additivity identity (`part_1/04` compresses, `part_2/03` keeps and defines it) · the Looker rejection (`part_2/02` internal either/or — prose **or** row, the row being the better version). **One caveat:** `part_1/01`'s Cut 3 deletes the six-service enumeration on the grounds `part1-pipeline` carries it, while `part1-pipeline`'s Cut 1 merges the two sentences that carry it. The merge must preserve the six service names.

---

## 2. THE TABLE

| ID | Page(s) | Class | Sev | Item | Effort | Status |
|---|---|---|---|---|---|---|
| C-01 | 1/03, 1/04, 1/05, 1/06, 2/01, 2/02, 2/05, 2/06 | CUT | High | Rejected-table pass: delete rows restating the prose immediately above | half-day | PENDING |
| C-02 | introduction | CUT | Med | "Two pages before the answers"; compress the two routing descriptors | 15m | PENDING |
| C-03 | intro/01 | CUT | Med | Private-notes flex; cost convention to one clause (see MC-2) | 15m | PENDING |
| C-04 | intro/02 | CUT | Med | Labelling-scheme paragraph, rhythm stated three ways, same-bound justification | 15m | PENDING |
| C-05 | part1-pipeline | CUT | Med | Merge sentences one and two; keep the six service names | 15m | PENDING |
| C-06 | part_1/00 | CUT | Low | Four internal restatements of the disclosure and inversion principles | 15m | PENDING |
| C-07 | part_1/01 | CUT | Med | Latency column hops 1-4, duplicated monitor definition, service enumeration | 15m | PENDING |
| C-08 | part_1/02 | CUT | Med | Storage-table prose re-read, Cloud Logging reason, Dataform-API duplicate | 15m | PENDING |
| C-09 | part_1/03 | CUT | High | Non-incident blockquote (frees a slot), retention restatement, cost tail | 15m | PENDING |
| C-10 | part_1/04 | CUT | High | Denominator table, Silver 26 rows to ~14, summary retention/PII rows | 1h | PENDING |
| C-11 | part_1/05 | CUT | Med | `storage_billing_model` paragraph to ~40 w; drop the Silver-PHYSICAL clause | 15m | PENDING |
| C-12 | part_1/06 | CUT | Med | Template defence, upsert aside, validity-window row (see MC-6) | 15m | PENDING |
| C-13 | part2-llm-agent | CUT | Low | Routing-row repeat, SDK name, sentence-1 clause, deeper-reading preamble | 15m | PENDING |
| C-14 | part_2/01 | CUT | Med | Italic third statement; catchability table to one mapping line (see MC-7) | 15m | PENDING |
| C-15 | part_2/02 | CUT | Med | Hop 9 scope paragraph, Looker prose, CA feature list, Cloud Next aside | 15m | PENDING |
| C-16 | part_2/03 | CUT | Med | 1.1 interlock paragraph, drift restatement, averaging generality | 15m | PENDING |
| C-17 | part_2/04 | CUT | Med | Third co-location statement, Data Catalog row, vector-DB row first clause | 15m | PENDING |
| C-18 | part_2/05 | CUT | Med | Gold paragraph, "the gap is the argument" hedge, trailing clause | 15m | PENDING |
| C-19 | part_2/06 | CUT | High | Closing blockquote (frees a slot), layer-1 paragraph, `execute()` comment | 15m | PENDING |
| C-20 | part_2/04, part_2/06 | CUT | High | Drop both dated product figures; keep the mechanisms they support | 15m | PENDING |
| M-01 | intro/01, part1-pipeline, part_1/02, part2-llm-agent, part_2/02 | MECHANICAL | High | One roster, one count: Cube back to Part 2, split stated 3/3 | 15m | PENDING |
| M-02 | intro/02, 1/00, 1/04, 1/05, 2/02, 2/04 | MECHANICAL | High | Numeric sweep: `no_bid` share, "five events", 25→26, `is_settled` +2h, token size | 1h | PENDING |
| M-03 | part_2/01 | MECHANICAL | High | Make both worked-example scenarios −$1.20 (Desktop 36% / Mobile 64%) | 15m | PENDING |
| M-04 | part_1/03 | MECHANICAL | High | Trigger 4: "set the watermark back" — 2.3 already makes it settable | 15m | PENDING |
| M-05 | intro/02 | MECHANICAL | High | Add the publisher-count row; the number is already on `part_1/05` | 15m | PENDING |
| M-06 | part2-llm-agent, part1-pipeline | MECHANICAL | Med | "the quality table" → `v_quality_hour`; disambiguate three senses of "hourly" | 15m | PENDING |
| M-07 | introduction | MECHANICAL | Med | "what it was allowed to assume" → "what was confirmed, and what is assumed on top" | 15m | PENDING |
| M-08 | part1-pipeline | MECHANICAL | High | State the latency contract: Bronze seconds, Silver 30 min, Gold hourly | 15m | PENDING |
| M-09 | part_2/03, part_1/04 | MECHANICAL | Med | `auctions_with_bid` is a boundary of derivability, not of additivity | 15m | PENDING |
| M-10 | part1-pipeline | MECHANICAL | Med | Drop "legally transient" — `intro/02` never calls the ceiling legal | 15m | PENDING |
| M-11 | part_2/05 | MECHANICAL | Low | Quote the sentence that covers future views, or drop the quote | 15m | PENDING |
| M-12 | part_1/06 | MECHANICAL | Low | Same parameterisation form in the headline query and the script | 15m | PENDING |
| M-13 | part_1/03 | MECHANICAL | High | Move the hot/cold table above the reframe — lead with their construct | 15m | PENDING |
| M-14 | part_1/03 | MECHANICAL | Low | Label the three latency values; give "State" its own row | 15m | PENDING |
| M-15 | part_2/06 | MECHANICAL | Med | Fifth (quota) row in the layer table; close the page after the Rejected table | 15m | PENDING |
| M-16 | part_1/00 | MECHANICAL | Med | Promote the "Gold only" Rejected row into the boundary section as its reason | 15m | PENDING |
| M-17 | part_2/03, part_2/02 | MECHANICAL | Med | Reconcile "Looker is already in the estate" with 1.2's Looker rejection | 15m | PENDING |
| M-18 | part_1/02 | MECHANICAL | Low | "at-least-once handling" → "the ack, retry and redelivery handling" | 15m | PENDING |
| M-19 | part2-llm-agent | MECHANICAL | High | Hoist four existing sentences: build-vs-buy, honest limit, latency, price | 15m | PENDING |
| M-20 | part1-pipeline | MECHANICAL | Med | Routing table: Retention row states the inversion; drop "six of the answers" | 15m | PENDING |
| D-01 | part1-pipeline, part_1/01 | DIAGRAM | High | `architecture.png` unreadable at docsify width: DDL off nodes, re-rank | half-day | PENDING |
| D-02 | part1-pipeline, part_1/01 | DIAGRAM | Med | `architecture.png` edges: `quality_hour` via semantic; dotted DLQ → Monitoring | 15m | PENDING |
| D-03 | part2-llm-agent, part_2/02 | DIAGRAM | Med | `agent.png`: `check_quality` box on the tool tier; clear the Gemini label | 1h | PENDING |
| R-01 | introduction | RATIFY | High | Thesis and three-page fast path on the first screen | 15m | PENDING |
| R-02 | intro/01 | RATIFY | High | Six components or four — the count the roster actually supports | 15m | PENDING |
| R-03 | intro/01 | RATIFY | Med | Narrow the reinstate-condition promise to what three tables deliver | 15m | PENDING |
| R-04 | intro/02 | RATIFY | High | Define the four provenance labels; re-mark the three lines not in the brief | 1h | PENDING |
| R-05 | intro/02 | RATIFY | Med | Reinstate condition on the no-row-level-security line | 15m | PENDING |
| R-06 | part1-pipeline, part_1/03, part_1/04 | RATIFY | High | Scope the two absolutes against the dead-letter path 1.1 documents | 1h | PENDING |
| R-07 | part_1/00 | RATIFY | High | `auction_id` anonymity: the relative test, and the residual columns | 1h | PENDING |
| R-08 | part_1/01 | RATIFY | High | Scope the `publisher_payout` assertion so an SSP cannot block Gold | 15m | PENDING |
| R-09 | part_1/01 | RATIFY | Med | What runs the watermark monitor when the release config is deleted | 15m | PENDING |
| R-10 | part_1/01, part_1/02, part_1/03 | RATIFY | Med | State the GCS archive's write format once — `publish_time` depends on it | 15m | PENDING |
| R-11 | part_1/02 | RATIFY | High | Reprice the Pub/Sub-retention row; it is not the cheaper alternative | 15m | PENDING |
| R-12 | part_1/02 | RATIFY | Med | Name the third option — extract the split in Silver — and why it loses | 15m | PENDING |
| R-13 | part_1/02 | RATIFY | Med | Convert Composer's reinstate condition from a mechanism into a trigger | 15m | PENDING |
| R-14 | part_1/04 | RATIFY | High | Price Silver — the only line item in the design that grows without bound | 1h | PENDING |
| R-15 | part_1/04 | RATIFY | Med | One clause on how `auctions_with_bid` is actually computed | 15m | PENDING |
| R-16 | part_1/04 | RATIFY | Med | Name Silver's dominant reader, or lead the cluster on `event_id` | 15m | PENDING |
| R-17 | part_1/05 | RATIFY | High | Reconcile cluster position 1 with the dominant-query argument | 1h | PENDING |
| R-18 | part_1/06 | RATIFY | High | Source the 2-minute offset and give it a detector | 1h | PENDING |
| R-19 | part_1/06 | RATIFY | High | State the real invariant: one row per (`event_id`, `auction_day`) | 1h | PENDING |
| R-20 | part_1/06 | RATIFY | Med | Pruning fallback: `require_partition_filter` rejects, it does not bill | 15m | PENDING |
| R-21 | part_1/06, part_1/04, part_1/01 | RATIFY | High | FX table's own convention, and the repair for already-merged nulls | 1h | PENDING |
| R-22 | part_2/01, part_2/02 | RATIFY | High | `mode = ANY`: name the narrowing turn, or downgrade the claim | 1h | PENDING |
| R-23 | part_2/01 | RATIFY | High | Report `rpm` and `fill_rate` beside a headline eCPM move | 1h | PENDING |
| R-24 | part_2/01, part_2/02 | RATIFY | Med | Latency and cost for the `diagnose_change` path | 1h | PENDING |
| R-25 | part_2/02, part_2/04, part_2/06 | RATIFY | High | Close statelessness against the clarifying turn | 15m | PENDING |
| R-26 | part_2/02 | RATIFY | High | Model drift and answer quality — the rubric line currently at zero | 1h | PENDING |
| R-27 | part_2/02 | RATIFY | Med | Dictionary built at deploy, not per request; carry the size clause from 2.2 | 1h | PENDING |
| R-28 | part_2/03 | RATIFY | High | Concede the re-aggregation residual and close it in 3.2's validator | 1h | PENDING |
| R-29 | part_2/03 | RATIFY | High | Gate `fill_rate` too, and state the grain coverage is evaluated at | 1h | PENDING |
| R-30 | part_2/03 | RATIFY | Med | Name the capability dbt SL and Cube buy that four views do not | 15m | PENDING |
| R-31 | part_2/04 | RATIFY | Med | Descriptions live in the same `includes` file as the ratio expressions | 15m | PENDING |
| R-32 | part_2/04 | RATIFY | Med | Reinstate the vector DB on free text entering the schema, not window size | 15m | PENDING |
| R-33 | part_2/04 | RATIFY | Med | Dataform assertion: fail the build on a NULL column description | 15m | PENDING |
| R-34 | part_2/04 | RATIFY | Med | Write the "make us" default into the description, with its structural reason | 1h | PENDING |
| R-35 | part_2/05 | RATIFY | High | Reprice the three-layer table under Part 1's actual DDL | 1h | PENDING |
| R-36 | part_2/05 | RATIFY | High | Out-of-grain questions are a Dataform change, never a wider grant | 15m | PENDING |
| R-37 | part_2/05 | RATIFY | High | Who holds `dataEditor` on `semantic` | 15m | PENDING |
| R-38 | part_2/05 | RATIFY | Med | Bronze is the only layer holding personal data — a privacy call, not a cost one | 15m | PENDING |
| R-39 | part_2/06 | RATIFY | High | The 20 GiB ceiling fires on an ordinary twelve-month question | 1h | PENDING |
| R-40 | part_2/06 | RATIFY | High | `referencedTables`: state what you observed, and fail closed | 15m | PENDING |
| R-41 | part_2/06, part_2/02 | RATIFY | High | The rejection path: what the analyst sees, and whether the model retries | 15m | PENDING |
| R-42 | part_2/06 | RATIFY | Med | Job timeout, and a bounded date comparison in layer 1 | 1h | PENDING |
| A-01 | intro/02 (spent on 1/01, 1/02, 1/03, 1/05) | AUTHORED | High | Peak-to-average and growth headroom behind every 23k/s figure | 1h | PENDING |
| A-02 | part_1/04, part_2/05, part_2/06 | AUTHORED | High | Ad-unit cardinality and Gold's real compression ratio | 1h | PENDING |
| A-03 | part_2/02 | AUTHORED | Med | What would make you delete your loop and buy the CA API | 15m | PENDING |
| A-04 | introduction, part1-pipeline, part2-llm-agent | AUTHORED | High | Do the three top-level pages declare themselves the deliverable | 1h | PENDING |
| A-05 | part_2/02, part_2/04 | AUTHORED | Med | The one sentence that reads as "RAG: done" to a box-checking grader | 15m | PENDING |
| A-06 | intro/01 | AUTHORED | Low | The first axis on which the minimal design becomes the wrong one | 15m | PENDING |
| A-07 | part_1/03, part_2/06 | AUTHORED | Low | Two blockquote slots freed by C-09 and C-19 — spend or bank | 15m | PENDING |

**Counts:** CUT 20 · MECHANICAL 20 · DIAGRAM 3 · RATIFY 42 · AUTHORED 7 · **92 items, 7 mutual cuts.**

---

## 3. RATIFY QUEUE

Each entry quotes the reviewer's proposed fix verbatim, then names the decision the author is agreeing to. Reply on the decision line.

### R-01 — `introduction.md`: thesis and fast path

> "Hoist one line of thesis above the bullets — e.g. 'The design keeps Pub/Sub, Cloud Storage and BigQuery, and deletes Dataflow and Composer; both pages below exist to show that this was argued, not assumed.'"

> "One line after the bullets — 'If you read three pages: the retention ceiling, the component verdicts, and the guardrails.'"

Accepting commits you to naming the retention ceiling, the component verdicts and the guardrails as the three load-bearing pages of eighteen — an editorial ranking of your own work that a reader will test against what they find.

**Decision:**

### R-02 — `intro/01-methodology.md`: the component count

> "Say four and name them, or keep six and add the half-clause that makes the other two fit (Composer: Dataform is the managed substitute, so the runtime *is* the objection; vector DB: the standalone index is the runtime, and corpus size is why the trade never gets close)."

Accepting the six-branch commits you to the claim that Composer loses on the runtime rule rather than on "one system in the DAG", which is a different argument from the one `part_1/02` currently makes. Accepting the four-branch costs the "one rule applied six times" line.

**Decision:**

### R-03 — `intro/01-methodology.md`: the reinstate promise

> "Narrow the claim to what `part_1/02` actually delivers — 'where the test names the component, the table also gives the condition that brings it back' — or add the third column to the tables. The narrow version is already true and still strong."

Accepting the narrow branch concedes that ~47 of ~50 Rejected rows carry no reinstate condition, and re-scopes the methodology page's testability argument to the five components the test names.

**Decision:**

### R-04 — `intro/02-business-assumptions.md`: the provenance labels

> "Define the four labels in one line at the top (Given = in the brief; Confirmed = asked and answered in clarification; Derived = ours, from a Given; Assumed = ours, unvalidated), then re-mark: 2B/1.5 TB as Confirmed with 'the low end of the test's *several billion*' stated explicitly, and 'analytics only' as Derived from *availability for BI*."

This corrects the *labels*, not the assumptions — the requirement values stay exactly as the client gave them. Accepting commits you to stating in the write-up that 2B/day is the floor of the brief's *several billion*, which invites the headroom question A-01 answers.

**Decision:**

### R-05 — `intro/02-business-assumptions.md`: the no-RLS reinstate condition

> "One clause on that row: the condition that reinstates it (publisher-facing access, or an agency user), and where it lands (authorized views become per-publisher, the agent's IAM identity stops being shared)."

Accepting commits Part 2 to a named consequence — per-publisher authorized views and a non-shared agent identity — which `part_2/05` and `part_2/06` must then not contradict.

**Decision:**

### R-06 — `part1-pipeline.md` + `part_1/03` + `part_1/04`: the two absolutes

> "swap *fail* for *be wrong*, or scope it: 'no service we deploy, no runtime we patch, and no failure of ours that a rerun does not fix.' … The same edit is due on 'Bronze itself validates nothing' — Bronze's `JSON` column refuses invalid payloads to the dead-letter topic, per 1.1 hop 4."

> "the hot path's only silent failure is *under*-delivery, it is caught by the dead-letter depth monitor rather than prevented by the shape, and it is replayable from the GCS archive — which holds the declined message — inside the 7-day window."

Accepting concedes in writing that the hot path has one silent failure mode, and relocates the defence from the shape of the design to a monitor plus a replay path. `part_1/03`'s thesis sentence and `part1-pipeline`'s sentence two both change; `part_1/04`'s "Bronze accepts everything, validates nothing" inherits.

**Decision:**

### R-07 — `part_1/00-retention-anonymisation.md`: the anonymity argument

> "Two sentences. Name the relative test explicitly (the SRB v EDPS line: data can be anonymous in the hands of a holder with no reasonable means of re-identification) and state why we are that holder — no contractual or technical route to the SSP's mapping. Then close the second gap: say that with `auction_id` inert, the residual Silver columns (`publisher_id`, `ad_unit_id`, `auction_timestamp` to the second, `country`, `device`) still describe one impression opportunity, and say why that combination does not single out — or narrow the claim to 'unlinkable by us' and stop calling it anonymous."

Accepting the first branch commits you to a legal position — the relative/subjective test — on the claim that licenses indefinite retention of an event-grain table. Accepting the second branch weakens the word "anonymous" everywhere it appears in Part 1 and must be swept.

**Decision:**

### R-08 — `part_1/01-architecture-diagram.md`: the `publisher_payout` assertion

> "scope the assertion to the join failure it is actually about — `gross_revenue IS NOT NULL AND publisher_payout IS NULL` (money computed, share missing) — and say in the row that a null `price` is a *monitor*, not a gate."

Accepting decides that a source which stops reporting `price` degrades a number rather than stopping Gold — consistent with `part_1/04`'s nullable-by-design rule, and a concession that one class of wrongness now reaches the dashboard behind a monitor.

**Decision:**

### R-09 — `part_1/01-architecture-diagram.md`: the watchdog's watchdog

> "one clause saying what fires out-of-band — a Cloud Monitoring absence-of-metric alert on the quality job's log line, or the quality workflow held in its own release config so the two cannot be deleted together."

Accepting adds one out-of-band alert to a design whose case is that it deploys nothing; the absence-of-metric branch is the cheaper of the two and does not add a component.

**Decision:**

### R-10 — `part_1/01` (or `1.2`): the archive's write format

> "state the archive's write format once, on 1.1 or 1.2, since `publish_time` is Bronze's partition key."

Accepting commits the export subscription to Avro with message metadata written — the only configuration under which `part_1/03`'s replay path returns rows with their original `publish_time`. Three pages currently assume another states it.

**Decision:**

### R-11 — `part_1/02-component-justification.md`: the Pub/Sub-retention row

> "Replace the row with the arithmetic: 'Pub/Sub retained storage is ~$0.27/GiB-month against GCS Standard's $0.020 — the same week costs more, and it is not queryable: no SQL, no partition pruning, no point lookup, only a pull.'"

Accepting withdraws a concession — the page currently hands its only genuine competitor a cost advantage it does not have. The figure needs your own check before it is defended live.

**Decision:**

### R-12 — `part_1/02-component-justification.md`: the third option

> "Add one sentence to the reinstate paragraph: 'Extracting the five fields in Silver instead needs no producer change and no Dataflow — but Bronze then has nothing to cluster on and the envelope check moves from publish time to 30 minutes later, which is bullet 2.2's argument, not this one.'"

Accepting turns the Dataflow rejection from a binary into a three-way and makes Bronze's cluster keys (2.2) load-bearing for a Part 1.2 argument — a cross-page dependency that must survive R-17.

**Decision:**

### R-13 — `part_1/02-component-justification.md`: Composer's trigger

> "Convert the negation already in the prose into the trigger: 'Composer arrives the first time a step waits on something outside BigQuery — a vendor API, a file that must exist, a cross-system dependency — not on model count.'"

Accepting commits you to model count never being the trigger, which is the opposite of the usual reason teams adopt Airflow, and you should expect that pushed on.

**Decision:**

### R-14 — `part_1/04-medallion-model.md`: pricing Silver

> "Two clauses in the Cost paragraph: Silver's physical bytes per day and the resulting monthly figure at 12 and 36 months, plus the mitigation that is already true and unstated — the trailing 3-day rebuild window never touches older partitions, so all but three days of Silver sit in BigQuery long-term storage at half price."

Accepting puts the design's one unbounded line item on the page. It does not create a TCO total; it prices the decision the page argues, which is the existing convention. `part_2/05`'s Silver row (R-35) must then agree with it.

**Decision:**

### R-15 — `part_1/04-medallion-model.md`: how `auctions_with_bid` is built

> "One clause — `COUNT(DISTINCT auction_id)` filtered to bid rows, grouped by the dimensions, inside the day partition already being rebuilt: one aggregation, not a join back to every event row, and on-demand billing charges bytes read, not shuffle."

Accepting states a mechanism the page currently only negates, and closes the apparent inconsistency with the rejected self-join two rows away.

**Decision:**

### R-16 — `part_1/04-medallion-model.md`: Silver's cluster keys

> "One sentence naming Silver's dominant reader and why the keys serve it (the Gold rebuild scans whole partitions and never filters, so the keys are for operational reads), or change the leading key to `event_id` and say why the MERGE won."

Accepting the first branch concedes that Silver's cluster keys serve humans, not the `MERGE` — which is the opposite criterion to the one `part_1/05` uses for Bronze, and you will be asked why the rule flips.

**Decision:**

### R-17 — `part_1/05-bronze-partitioning.md`: cluster position 1

> "one paragraph plus a Rejected row. The defensible answer is already implicit — the partition already satisfies the time predicate, so a leading time key would prune only the sub-hour remainder, on rows the automatic re-clusterer has not yet touched, while demoting the two keys the test named by name."

Accepting states that clustering optimises the operational read while partitioning optimises the machine read — two criteria on one DDL, argued rather than switched silently. This is the question the reviewer says he would open the interview on.

**Decision:**

### R-18 — `part_1/06-dedup-sql.md`: the 2-minute offset

> "One sentence saying the offset is set from the measured p99.9 of `publish_time` → queryable skew, and one row added to the quality job (or the 1.1 monitor table) that counts Bronze rows arriving with `publish_time` below the current watermark."

Accepting adds a sixth signal to `part_1/01`'s monitor table and commits you to the offset being measured rather than chosen — meaning the number can move, and the page should say what moves it.

**Decision:**

### R-19 — `part_1/06-dedup-sql.md`: the real invariant

> "State the real invariant once — *at most one row per `event_id` per `auction_day`* — and add a clause acknowledging that when the batch spans midnight the row is updated in place, leaving `auction_day ≠ DATE(auction_timestamp)`, which is the same producer bug surfacing in a second shape and is caught by the same quality counter."

Accepting changes Silver's stated grain, which `part_1/04` and `part_2/03` both quote as "one row per `event_id`". Both inherit the correction.

**Decision:**

### R-20 — `part_1/06-dedup-sql.md`: the pruning fallback

> "Replace the fallback sentence with 'and if BigQuery ever stops pruning it, `require_partition_filter` rejects the statement rather than silently billing a full scan.'"

Accepting makes the failure loud rather than expensive — which is the page's own frame, and a better story than the hedge it replaces.

**Decision:**

### R-21 — `part_1/06` + `part_1/04` + `part_1/01`: FX timing

> "One line on the FX table's own convention (previous close carried forward, or a rate valid from D-1) and one line saying a late rate is repaired by the same settable-watermark rewind already described, not by a new mechanism."

Accepting picks an FX convention on the client's behalf. Without it, the composition of `part_1/06` (revenue computed at merge time, within 30 min), `part_1/04` (FX external, no loader, no schedule) and `part_1/01` (null `publisher_payout` blocks Gold) makes a blocked Gold build the design's normal daily state.

**Decision:**

### R-22 — `part_2/01` + `part_2/02`: `mode = ANY`

> "Name the narrowing step in one clause — e.g. a first turn classifies, and turn two re-invokes with `allowed_function_names=['diagnose_change']` so the model cannot revise its own routing mid-answer — or downgrade the claim to what the API actually gives (a tool call rather than free text, plus schema adherence) and let *'misrouting degrades an answer; it does not falsify one'* carry the defence, which it already does well."

Accepting the first branch commits the flow to two model turns for every routed question, which changes `part_2/02`'s hop table and its latency column. Accepting the second withdraws the mechanism claim that `part_2/02` currently spends again to beat the Conversational Analytics API — the reviewer calls that verdict the strongest thinking in Part 2, so the downgrade must be paired with a check that the verdict still stands.

**Decision:**

### R-23 — `part_2/01-question-classes.md`: eCPM and `rpm`

> "Add one line to step 2: for `ecpm`, report the movement in `rpm` and `fill_rate` alongside the headline before decomposing, so *'eCPM −20%, rpm flat — floors were lowered, revenue per opportunity is unchanged'* is reachable. It costs one extra measure per pass and closes the whole category."

Accepting means the copilot answers the test's own example question by first reframing it — a strong move, and one you must be willing to defend as helpful rather than evasive.

**Decision:**

### R-24 — `part_2/01` + `part_2/02`: the why-path's latency and cost

> "Say the four passes are issued concurrently and give an end-to-end figure (~4–6 s), plus the per-invocation scan."

> "two figures and a verdict — *what* ≈ 5 s, *why* ≈ 10–15 s because the routine is N sequential passes, acceptable against the analyst's alternative of writing the SQL herself."

The two reviews propose **opposite** implementations — concurrent (≈4–6 s) versus sequential (≈10–15 s). Accepting picks one, and the same figure has to appear on both pages and in M-19's hoist.

**Decision:**

### R-25 — `part_2/02` + `part_2/04` + `part_2/06`: statelessness

> "one sentence at hop 1 — the client echoes the prior `contents` back on the next `POST`, so the conversation is state the caller carries and the service still holds none — or state that clarification resolves inside the same request by re-prompting with the candidate list."

Accepting the first branch makes conversation history the client's responsibility and hop 9's contract must then return something to echo. Accepting the second keeps one request per question and makes `part_2/04`'s "one question costs a turn" an internal turn, not a user round trip. `part_2/06`'s "a model in a retry loop" must be reconciled with whichever you take.

**Decision:**

### R-26 — `part_2/02-agent-flow.md`: model drift

> "One clause here and a short paragraph on `1.2`: the four response fields are logged, and a fixed set of questions with known answers is re-run on model change — the cheapest possible version, sized for ten users."

This is the rubric line the brief names (*"without unnecessarily exposing the infrastructure to model drift"*) and the word "drift" appears nowhere in eighteen pages. Accepting commits you to owning a golden question set and to a stated trigger for re-running it, on a design that deliberately pins no model ID.

**Decision:**

### R-27 — `part_2/02-agent-flow.md`: the dictionary at hop 2

> "cache the assembled block with a TTL (or build it at deploy, since Dataform publishes on build) and relabel the hop; one clause saying the dictionary refreshes on deploy rather than per request removes the issue entirely."

> "carry one clause from 2.2 — a few dozen definitions, a few thousand tokens against a million-token window — plus the reinstate condition (`VECTOR_SEARCH` in BigQuery if the corpus outgrows the window), and reconcile it with the 4,096-token caching claim."

Accepting the deploy-time branch means a new column description does not reach the copilot until the next Dataform build — a freshness trade `part_2/04` currently does not make. It also interacts with R-33: an assertion that fails the build on a NULL description is exactly what makes deploy-time safe.

**Decision:**

### R-28 — `part_2/03-semantic-layer.md`: the re-aggregation residual

> "Concede the residual in one sentence — the view fixes *definition* drift absolutely and *re-aggregation* only at its own grain — then close it with machinery already on the page: the ratio column names are a known list of ten, so 3.2's `sqlglot` pass rejects any `exp.AggFunc` over one of them, and 2.2's injected dictionary states the re-aggregation form (`SUM(gross_revenue)/SUM(impressions)*1000`) beside the definition."

Accepting withdraws the page's bolded headline claim and adds a fifth static check to `part_2/06`'s validator. The concession is the stronger position — but it must be made before the argument that Cube and dbt SL lose (R-30), because it is the one capability they win on.

**Decision:**

### R-29 — `part_2/03-semantic-layer.md`: the coverage gate

> "Gate every metric that mixes the impression stream with a non-impression denominator (`fill_rate`, `render_rate`), and state in one clause why `ecpm` and `gross_margin` need no gate — revenue lands only on impression rows (2.1), so their numerator and denominator drop together and the ratio stays honest over reporting sources. Say at which grain coverage is evaluated on a multi-hour query, because `SUM(reporting)/SUM(total)` over a month is below 1 almost always and would make `render_rate` permanently empty at the grain people ask at."

Accepting means a month-long `fill_rate` question returns NULL whenever any source missed one hour, unless you also pick a coverage grain that tolerates it. The grain choice is the buried decision, and it is the one that determines whether the gate is a safeguard or an outage.

**Decision:**

### R-30 — `part_2/03-semantic-layer.md`: what Cube and dbt SL actually buy

> "Add a clause to the two rows: 'buys query-time aggregation at an arbitrary grain, which the views buy only at their own — closed by the validator rule above, at a fraction of the operational cost.' That converts the weakest leg of the rejection into the strongest."

Accepting concedes a real capability gap and then closes it with the validator rule from R-28 — so this item is dependent on R-28 being accepted, not independent of it.

**Decision:**

### R-31 — `part_2/04-glossary-and-entities.md`: where the descriptions live

> "One clause: the column descriptions live in the same `includes` file as the ratio expressions and are spread into each view's `columns` block, so one definition and one implementation move together across all four views. That restores the claim literally instead of weakening it."

Accepting commits `part_2/03`'s `includes` file to holding descriptions as well as expressions — a structure `part_2/03` does not currently describe, so that page inherits one clause.

**Decision:**

### R-32 — `part_2/04-glossary-and-entities.md`: the vector-DB reinstate condition

> "Swap them. Reinstate on *'the day a free-text field enters the data — a creative name, a deal note, a support ticket — because semantic search needs something to search'*, and demote the window argument to the clause it already is."

Accepting makes the reinstate condition fireable, on the option the test names most prominently. It also ties the rejection to a client-Confirmed fact (no free text) rather than to a model-vendor number that moves.

**Decision:**

### R-33 — `part_2/04-glossary-and-entities.md`: the missing-description detector

> "A Dataform assertion over the same query the prompt uses — fail the build when any column in the semantic dataset has a `NULL` description. No new component, one file, and it converts 'someone forgot' from an invisible answer-quality problem into a red build."

Accepting is the cheapest available answer to the whole of §3.8 (Part 2 has no operational spine): it is one assertion, in a mechanism Part 1 already uses, and it is the only detector Part 2 would have.

**Decision:**

### R-34 — `part_2/04-glossary-and-entities.md`: the "make us" default

> "Put the disambiguation in the description text where everything else lives (`gross_revenue`: *\"'make us' is ambiguous — answer this and name it\"*), and add the structural reason the default is gross rather than an appeal to what analysts usually mean: the retained-share reading maps to no column in Gold (only `gross_revenue` and `publisher_payout` exist), so one reading is a column and the other is arithmetic. Then one sentence on the asymmetry: a wrong entity is invisible in the answer, a wrong definition is printed in it — which is why one asks and the other discloses."

Accepting commits you to the asymmetry as a stated rule — entities ask, terms disclose — which is a design principle the page currently applies without arguing.

**Decision:**

### R-35 — `part_2/05-query-layer.md`: the three-layer price table

> "Reprice all three rows for the *same* question under each layer's actual DDL: Gold, fractions of a cent; Silver, one publisher's slice of *N* day-partitions of event-grain rows — still two to three orders up, and growing with history rather than bounded by it; Bronze, the question mostly has no answer at all, and the one it has costs a JSON extraction the model has to invent. The gap survives honest numbers; state it as 'the same question, two to three orders apart, with only one of the three bounded by anything'."

This is the largest single credibility item in Part 2: the table contradicts `part_1/05` outright (`require_partition_filter` makes the ~10.5 TB / ~$60 Bronze row a query that *errors*), and the page's most quotable line rests on it. Accepting commits you to numbers that must agree with R-14's Silver figure and with R-39's ceiling.

**Decision:**

### R-36 — `part_2/05-query-layer.md`: questions outside Gold's grain

> "Two sentences: an out-of-grain question is a Dataform change — a dimension added to Gold and surfaced in the view, shipped like any model change — and never a temporary grant, because the grant is the one control in this design that does not bend. Add 'a question outside Gold's grain' as a named limit, the way 1.1 names its honest limit."

Accepting states a limit rather than waiting to be asked, and commits you to refusing the widened grant even under pressure — which is the answer, but it should be a decision, not a reflex.

**Decision:**

### R-37 — `part_2/05-query-layer.md`: write access to `semantic`

> "One clause: the agent's service account holds `dataViewer` and therefore cannot create anything; `dataEditor` on `semantic` belongs to the Dataform deploy account alone, so a new view is a reviewed diff in the same repo as the metric definitions."

The authorized dataset blesses every view in `semantic`, present and future, so this is what stops `CREATE VIEW v_raw AS SELECT * FROM gold_opportunity` handing the agent base-table grain. Accepting also supplies the deployment-model answer §3.7 says no page owns.

**Decision:**

### R-38 — `part_2/05-query-layer.md`: Bronze holds the personal data

> "One clause in the Bronze paragraph: Bronze is the only layer holding personal data, so an agent that narrates what it reads is a privacy decision before it is a cost one — and the grant, not a prompt rule, is what settles it."

A free point already paid for in `part_1/00`. Accepting connects Part 1's privacy boundary to Part 2's access decision, which nothing currently does.

**Decision:**

### R-39 — `part_2/06-guardrails.md`: the 20 GiB ceiling

> "Either raise it and price it — 200 GiB is $1.25 at on-demand $6.25/TiB and still four orders of magnitude below the bullet's terabyte scan — or keep 20 GiB and say what it costs ($0.12) and what it rejects, and add the one sentence the page is missing: the rejection message goes back to the model, which retries with a narrower period. Cheapest version: replace the comment with *'~a month of `v_ssp_daily`; longer periods must narrow the filter.'*"

By the document's own sizing (`part_2/05`: ten million rows/day on `gold_ssp`), 20 GiB is roughly one month of the SSP view, so a twelve-month trend — a first-class *what* question on `part_2/01` — is refused. Accepting picks a ceiling and, either way, commits you to a rejection path (R-41).

**Decision:**

### R-40 — `part_2/06-guardrails.md`: `referencedTables`

> "State the observed behaviour in one clause (*'on an authorized view the job statistics name the view; the Gold branch is there for the day view expansion changes'*), and make the loop fail closed — `if not dry.referenced_tables: raise Rejected(...)` — which is two words of code and converts a silent gap into a stated one."

Accepting asserts what you observed. If you have not run it, the honest version is to say the branch is defensive and drop the bolded "checked twice" — object resolution is the only thing layer 2 uniquely contributes, so the hedge is load-bearing.

**Decision:**

### R-41 — `part_2/06` + `part_2/02`: the rejection path

> "one sentence at hop 1, one at hop 9 covering what the analyst sees when a guardrail fires and whether it returns to the model." (`SYNTHESIS` §6.8)

With the ceiling firing on ordinary twelve-month questions until R-39 lands, the failure UX is the common path, not the edge case. Accepting decides whether a rejection is a user-facing message or a model retry — and if it is a retry, `part_2/02`'s "loop bounded at two" has to accommodate it.

**Decision:**

### R-42 — `part_2/06-guardrails.md`: compute and the date check

> "One line in `QueryJobConfig` (`job_timeout_ms=120_000`) and one sentence: under on-demand the bill is bytes, so a compute blowup is a hung request and a timeout, not an invoice — which is the same argument the quota section already makes against a shared reservation."

> "Require a bounded comparison — the date column against a literal or a query parameter under `>=`/`>`/`BETWEEN`/`=` — and say plainly that layer 1 is a cheap shape filter while the dry run is the only honest byte check."

Accepting concedes that four byte-guards guard no compute, and that layer 1 is cosmetic where the dry run is structural. Both concessions are favourable to the design and pre-empt "write me a query that gets through all four layers".

**Decision:**

---

## 4. AUTHORED QUESTIONS

### A-01 — Peak-to-average and headroom

`intro/02` gives a daily average (2B/day). Four pages spend `2B ÷ 86,400 ≈ 23k/s` as a **capacity** figure — dedup state (~10 GB), alert thresholds, the $5,100 partition-grain delta. Ad traffic is diurnal, the brief's stated quantity is *several billion*, and the rubric's first line reads *"understanding of scale constraints"*.

**Question:** What peak-hour multiple of the daily mean does the collector actually see, what growth do you design a year of headroom for, and which of the design's numbers move if the peak is 3× rather than 2×?

**CANDIDATE:** none. Searched the DECISIONS and NUMBERS ledgers on all 18 pages: no peak, no growth rate, no headroom figure exists anywhere in the write-up. `part_1/02`'s reviewer proposes "two to three times", but that is the reviewer's number, not yours. This stays a genuine question, and it is the one gap `SYNTHESIS` places against the weakest of the four rubric lines.

**Answer:**




### A-02 — Ad-unit cardinality, and whether Gold is actually an aggregate

`gold_ssp` is keyed on `auction_hour, publisher_id, ad_unit_id, ssp_id, format, device, channel`. Ad-unit cardinality appears on no page. `part_2/05` asserts a Gold scan is two to three orders below the event layers; `part_2/06` sets a byte ceiling against that assumption. Part 2's whole cost story rests on a number the document never states.

**Question:** How many ad units per publisher, what does that make `gold_ssp`'s rows per hour, and at what cardinality does the compression argument stop holding — at which point does `ad_unit_id` drop out of `gold_ssp`'s grain and survive only on `gold_opportunity`?

**CANDIDATE (your own words, from `part_2/05-query-layer.md`):** *"a few million rows/day on `gold_opportunity`, ten million on `gold_ssp`"* — you have already committed to a Gold row count. Combined with `part_1/04`'s *"SSP 7 invited to 4% of auctions"* and *"10-20× opportunity overcount"*, the sizing may already be implied rather than open. If ten million/day is a figure you can stand behind, the answer is to state the ad-unit cardinality that produces it on `intro/02` and let `part_1/04` and `part_2/05` cite it — which converts this to MECHANICAL.

**Answer:**




### A-03 — What would make you buy the Conversational Analytics API

`part_2/02` concedes the CA API *"carries most of this page"* and beats it on two documented facts. Unlike every rejection in Part 1, the build-vs-buy table states no reinstate condition — which its reviewer calls *"the one question the author would have to improvise"*, and it is the first question a CTO asks.

**Question:** What specific, observable change in Google's product deletes your fifty-line loop — and what do you keep even then?

**CANDIDATE (your own words, from `part_1/02-component-justification.md`):** *"the producer refuses to emit the five-field split"* — the Dataflow row's condition is the shape you already use for a testable trigger: a named third-party behaviour, observable without a judgement call. The equivalent here is a documented capability (forced routine invocation, or table selection documented as a security control), not a version number. The form exists in your own words; the content does not.

**Answer:**




### A-04 — Do the three top-level pages declare themselves the deliverable

The brief asks for *"a summary document (or presentation deck for discussion)"*. The write-up is ~20,300 words across eighteen pages, of which the summary layer is 70 + 764 + 510 = 1,344 — with the 70-word page as the entry point. `SYNTHESIS` §5's central recommendation is not to cut 20,000 words but to make those three pages *be* the summary and let the rest read as annex, at a cost of ~150 words of new writing.

**Question:** Do you want `introduction.md` to say plainly that the three top-level pages are the summary and everything beneath them is the annex — and if you do, what does that cost you with a grader who then reads fifteen pages of annex as padding rather than as depth?

**CANDIDATE:** none. The repo's working rules state the output is defended live in a ~1h presentation, which makes the write-up a reference and the defence a deck — a coherent answer that the document never signals to the reader. The decision to signal it (or not) is yours; R-01, M-08 and M-19 are the mechanics either way.

**Answer:**




### A-05 — The RAG box-check

The brief names *"Text-to-SQL + RAG"*. `part_2/02` redefines RAG as two mechanisms; `part_2/04` argues for no retrieval index at all. Both are defensible and well argued. A grader checking boxes reads "no vector database" before reading why.

**Question:** What is the one sentence, in the summary layer, that a box-checking grader reads as "RAG: done" and that you can still defend verbatim when they ask where the index is?

**CANDIDATE (your own words, from `part_2/02-agent-flow.md` and `part_2/04-glossary-and-entities.md`):** *"RAG = two mechanisms (whole injection + live entity lookup)"* and *"injecting the whole corpus removes retrieval error and leaves selection error"*. Both already exist and both are yours. The open part is only placement — neither appears above the fold, and the repo's own rule (*lead with their construct, then extend it*) says the compliant reading has to arrive first.

**Answer:**




### A-06 — The first axis on which the minimal design becomes wrong

`intro/01` presents delete-by-default as pure gain and never names its cost. The CTO's private reaction to a six-service architecture is *"this is a design one person can defend, not one five engineers can operate."*

**Question:** Which arrives first — a second source system, a non-BigQuery step, or the second engineer — and which page already records the consequence?

**CANDIDATE (your own words, from `part_1/02-component-justification.md`):** the two reinstate conditions on that page *are* the answer — *"the producer refuses to emit the five-field split"* (Dataflow) and Composer arriving with a step outside BigQuery. You have already written down where the bet is recorded. Per the rule that reusing a committed argument beats writing a new one, the cheapest close is one cross-reference clause on `intro/01` rather than a new paragraph, which also keeps that page shorter rather than longer. Confirm and this becomes MECHANICAL.

**Answer:**




### A-07 — The two freed blockquote slots

C-09 removes a blockquote on `part_1/03` that is not an incident narrative; C-19 removes one on `part_2/06` for the same reason. The house cap is ~5-6 across the document, so both cuts return budget rather than spending it.

**Question:** Bank both, or spend one on the Part 2 mechanism that is otherwise most abstract?

**CANDIDATE (your own words, from `part_2/04-glossary-and-entities.md`):** the incident you already have in Part 2 — *a client won this morning, asked about at 15:00* — is the shape that works, and its reviewer calls it "the right one". If a slot is spent, the two abstract mechanisms with no narrative are the guardrail rejection path (R-41) and model drift (R-26). Banking both is also a defensible answer and costs nothing; the failure mode this backlog is guarding against is a review round that only adds.

**Answer:**




---

## 5. RECOMMENDED SCOPE

### The honest headline

**This document needs less work than 92 items implies.** Read the grades: eleven of eighteen pages grade A or B+ on the reviewers' own scale, `part_1/06`, `part_1/04` and `part_1/05` carry the rubric's BigQuery line by themselves with independently verified arithmetic, and six reviewers independently wrote a version of *"this is a dense page; there is no padding to find, only restatement."* The Part 1 A / Part 2 B split is ~70% reviewer severity: Part 1's blockers are prose overclaims, Part 2's are artifact numbers, and artifact numbers are the cheap ones. There is exactly one real deficit — Part 2 has no operational spine — and one real omission — model drift, a named rubric line at zero. Both are closed by two items, R-26 and R-33, totalling ~1h15.

### With six hours

Resolve the seven mutual cuts first (30m of reading, no edits) — they are free, and skipping them is the one way this backlog can make the document worse.

Then, in order:

1. **R-35 + R-39 + R-14 — the numbers that contradict Part 1 (2h).** `part_2/05`'s price table prices queries `part_1/05`'s DDL forbids; `part_2/06`'s ceiling refuses a question `part_2/01` calls first-class; Silver, the only unbounded line, is priced nowhere. A staff engineer who read Part 1 forty minutes earlier finds all three. Everything else in Part 2 is opinion; these are checkable.
2. **R-01 + M-19 + M-08 (45m).** The first screen currently scores zero against the rubric's first line, and the strongest sentence in the document sits one click behind it. ~150 words of hoisting from pages already written. `SYNTHESIS` calls this the highest leverage available anywhere, and it is.
3. **R-26 + R-33 (1h15).** Closes the rubric line at zero and gives Part 2 its only detector. One paragraph and one assertion.
4. **M-01 + M-02 + M-03 (1h15).** The ten-second checks: four different component counts, `no_bid` at 75-80%, "same-sized drop" against −$1.00 and −$1.20, 25 partitions where the page's own sentence gives 26. These cost nothing to fix and everything to be caught on.
5. **R-06 + R-22 + R-25 (45m).** Three overclaims that a reader dismantles using the document's own material: *"no process of ours can fail"*, `mode = ANY` enforcing a routing decision it cannot make, statelessness against the clarifying turn. R-22 matters beyond its sentence — `part_2/02` spends the same claim again to win the build-vs-buy verdict.
6. **C-01 (whatever is left).** Deletion-only pass over the Rejected tables — ~640 words, no argument removed. Brief it as deletion-only: nothing may be added.

That is six hours and it closes every High-severity item that changes what a reader concludes.

### What I would drop entirely, and why

- **D-01 (`architecture.png` re-render, half-day).** The largest single item in the backlog and the worst hour-for-hour trade here. It is real — 3464×1312 with three-line DDL labels is unreadable at docsify width — but the write-up is defended live in a ~1h presentation, where the diagram is on a screen you control at whatever zoom you like. **Do D-02 instead (15m):** the two edge corrections matter because one of them draws the agent an access the text spends a page refusing, and that is an argument error, not a rendering one. If there is a seventh hour, spend it here; not before.
- **The "add a mitigation" findings.** `part_1/00`'s payload-key drift assertion, its allowlist-binds-insiders clause, `part_1/01`'s `max_delivery_attempts` figure, `part_1/03`'s Pub/Sub-throughput kill on lambda, and `part_1/03`'s envelope-vs-payload sample assertion. Every one of them adds a mechanism to answer a question the page already handles honestly, and four of the five are on pages already graded A. Naming a weakness without a mitigation is a stronger live move than inventing one — these are spoken ammunition, not page content. This is precisely the failure mode the repo names: *"review rounds that only ever add."*
- **`part_2/01`'s interaction-term convention.** The formula is exact; the mirror-decomposition objection is a graduate-seminar point that costs a clause to pre-empt and a sentence to answer live. Answer it live.
- **`part_2/03`'s `net_revenue` measure.** Adds a column to close a gap that `gross_margin` plus the copilot's stated-definition rule already covers.
- **`part_1/05`'s grain-migration paragraph and `intro/01`'s "the method's own failure mode".** Both add prose to pages whose reviewers also asked them to get shorter. A-06 shows the second one is already answered in `part_1/02`'s own words; one cross-reference beats a new paragraph.
- **Everything under `intro/02` that is not a label or a missing cardinality row.** The assumptions are client-given and are not to be re-litigated. R-04 corrects what the *labels* claim about the brief, M-05 relocates a number already in the write-up, A-01 supplies one that is missing. The requirement values themselves stay untouched, and no item here proposes otherwise.

### One thing not to do

Do not restructure Part 2 on the strength of its letters. Two Part 2 reviewers wrote *"A-grade thinking"* inside a B block. Its design reasoning sits level with Part 1's; its artifacts and its operability do not. Fix four numbers and add one paragraph, and it grades level.
