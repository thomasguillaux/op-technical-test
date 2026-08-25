# 2.2 — Synonym & Metadata Management

*Test bullet: how do you structure the data dictionary (e.g., via dbt tags, data catalog, or vector database) so that the LLM correctly associates a user's informal language ("how much does site Y make us?") with the right technical entities (publisher_id, ad_unit, gross_revenue)?*

**The dictionary is metadata on the model — the test's first option, minus the dead runtime.** Table and column `description`s in the Dataform SQLX, versioned with the SQL they describe and injected into the prompt whole.

But the test's own example contains two lookups, and they need opposite mechanisms.

| In *"how much does site Y make us?"* | Cardinality | Volatility | Mechanism |
|---|---|---|---|
| *"site Y"* — an **entity** | Hundreds of publishers, far more ad units | Changes as business is won and lost | **Queried live** — the `resolve_entity` tool |
| *"make us"* — a **term** | A few dozen definitions | Changes only when the business changes a definition | **Injected whole** — no retrieval at all |

A single retrieval mechanism over both is what the vector-database option implies. It re-indexes a dimension table for the volatile half and adds retrieval risk to a corpus that already fits.

Retrieval over fifty items retrieves the wrong one sometimes; sending all fifty never does.

## The dictionary lives in the SQLX, because a prompt is not a source of truth

The definitions live where the metric is implemented, in the Dataform `config` block, changed in the same pull request as the SQL they describe. A prompt is a deploy artefact: editable in a file nobody who owns a metric reviews.

Dataform publishes them to BigQuery on every build. `INFORMATION_SCHEMA.COLUMN_FIELD_PATHS` exposes `description` beside `column_name`, and the prompt block assembled at hop 2 is generated from that query at request time. A metric definition cannot drift from the query implementing it, because they are the same file.

**Synonyms live inside the description text, because BigQuery has no field for them:**

> `gross_revenue` — *"what the inventory earned before OptimusAds' share. Also asked as: what a publisher makes, what a site earns, turnover, top line."*

## *"Make us"* is ambiguous, and no dictionary fixes it

Read literally, *"how much does site Y make **us**"* is net revenue — OptimusAds' retained share. The analyst almost always means gross, what the publisher's inventory earned. A synonym list cannot resolve that, because both readings are correct English and only one is intended.

So the mechanism is not a better dictionary. It is the rule from 2.1: the copilot states the definition it used.

> *"Site Y generated €12,400 yesterday — gross revenue, before our share."*

The dictionary makes the model's reading explicit. It does not guarantee the reading is right.

## `resolve_entity` is a query, not an index

`publisher_id` and `ad_unit_id` are already human-readable — the names the Yield team says out loud *are* the values in the column. The lookup needs no mapping table, only a fuzzy match against the live dimension values in the semantic views:

```sql
WITH names AS (
  SELECT DISTINCT publisher_id
  FROM v_opportunity_daily
  WHERE day >= CURRENT_DATE() - 30
),
scored AS (
  SELECT
    publisher_id,
    EDIT_DISTANCE(LOWER(publisher_id), LOWER(@name), max_distance => 4) AS distance
  FROM names
)
SELECT publisher_id, distance
FROM scored
WHERE distance < 4
   OR SOUNDEX(publisher_id) = SOUNDEX(@name)
ORDER BY distance
LIMIT 5
```

- **`max_distance => 4` with a filter of `< 4`, not `<= 4`.** `EDIT_DISTANCE` returns `max_distance` when the true distance exceeds it — that is what lets it stop early. A predicate at the cap therefore matches every name in the table. The cap is the performance knob. The filter sits one below it.
- **`SOUNDEX` catches what Levenshtein does not:** a name heard rather than read, misspelt by more than three characters but pronounced right.
- **Thirty days is the set of publishers currently transacting.** Widen it and churned names compete with live ones for the match.

**The tool returns ranked candidates, not an answer.** Where more than one scores close, the copilot asks which. Silently picking the nearest produces a confident, well-formed answer about the wrong client, indistinguishable from a right one. Asking costs one turn.

> **A publisher signed this morning, asked about at 15:00.** *"How much does site Y make us?"* resolves, because entity lookup reads the dimension values in the view rather than an index someone would have had to re-embed. A stale index answers *"I don't know that publisher"* about a client the sales team won this week — and nothing about that answer looks like a staleness bug.

**Cost.** The dictionary is a few thousand tokens on every request. `resolve_entity` scans one string column over a 30-day window of a Gold-derived view — cents. The cost worth naming appears on no bill. An embedding pipeline, an index and a re-indexing job are a component to operate and a staleness failure to notice, and neither is a line item.

## Rejected — one line each

| Option | Why not |
|---|---|
| **Vector database** | The client removed the last case for one: *"pas de texte libre, que des données liées aux enchères"*, so every field is an enumeration or a number and **semantic search has nothing to search.** If the dictionary ever does outgrow the context window, BigQuery's own `VECTOR_SEARCH` is the answer, not a separate database — the rule that removed every other standalone runtime |
| **A data catalog** | A catalog is a governance and discovery surface for *humans* at 200 tables and 40 analysts, where nobody holds the model in their head. **The LLM does not read a catalog:** something would have to export it into the prompt, which makes it an authoring tool for the dictionary rather than a replacement for it. And Dataform already publishes column descriptions into it, so it sits *downstream* of the SQLX |
| **dbt tags** | Dead with the dbt runtime, removed in Part 1. Dataform column descriptions are the equivalent and sit closer to the SQL |
| **A vector index over entity names** | A copy of a dimension table, with a staleness problem the dimension table does not have |
| **A hand-maintained synonym table** | A second source of truth for vocabulary, in a system that does not fail when it drifts from the first |
| **Letting the model guess the entity** | *"Site Y"* matching the wrong publisher produces a confident, well-formed answer about the wrong client — the failure class 1.1 exists to remove |

---

Next: [**3.1 — Gold, Through Its Views Only**](/part_2/05-query-layer.md)
