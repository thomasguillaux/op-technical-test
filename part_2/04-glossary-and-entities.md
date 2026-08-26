# 2.2 — Synonym & Metadata Management

*Test bullet: how do you structure the data dictionary (e.g., via dbt tags, data catalog, or vector database) so that the LLM correctly associates a user's informal language ("how much does site Y make us?") with the right technical entities (publisher_id, ad_unit, gross_revenue)?*

**Two vocabularies, two mechanisms, split on volatility.** A few dozen metric definitions change only when the business changes them, so the dictionary is injected whole and never retrieved. Hundreds of publisher and ad-unit names change as business is won and lost, so they are resolved live against the dimension values themselves. A vector database is rejected because the client's data carries no free text for semantic search to search.

---

| In *"how much does site Y make us?"* | Cardinality | Volatility | Mechanism |
|---|---|---|---|
| *"site Y"* — an **entity** | Hundreds of publishers, far more ad units | Changes as business is won and lost | **Queried live** — the `resolve_entity` tool |
| *"make us"* — a **term** | A few dozen definitions | Changes only when the business changes a definition | **Injected whole** — no retrieval at all |

`resolve_entity`, in full:

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

**Cost.** The dictionary is a few thousand tokens on every request. `resolve_entity` scans one string column over a 30-day window of a Gold-derived view — cents. The cost of the rejected alternative is operational rather than billed: an embedding pipeline, an index and a re-indexing job are a component to operate and a staleness failure to notice.

## Rejected — one line each

| Option | Why not |
|---|---|
| **Vector database** | The client removed the last case for one: *"no free text, only auction-related data"*, so every field is an enumeration or a number and **semantic search has nothing to search.** If the dictionary ever does outgrow the context window, BigQuery's own `VECTOR_SEARCH` is the answer, not a separate database — the rule that removed every other standalone runtime |
| **A data catalog** | A catalog is a governance and discovery surface for *humans* at 200 tables and 40 analysts, where nobody holds the model in their head. **The LLM does not read a catalog:** something would have to export it into the prompt, which makes it an authoring tool for the dictionary rather than a replacement for it. And Dataform already publishes column descriptions into it, so it sits *downstream* of the SQLX |
| **dbt tags** | Dead with the dbt runtime, removed in Part 1. Dataform column descriptions are the equivalent and sit closer to the SQL |
| **A vector index over entity names** | A copy of a dimension table, with a staleness problem the dimension table does not have |
| **A hand-maintained synonym table** | A second source of truth for vocabulary, in a system that does not fail when it drifts from the first |
| **Letting the model guess the entity** | *"Site Y"* matching the wrong publisher produces a confident, well-formed answer about the wrong client — the failure class 1.1 exists to remove |

---

Next: [**3.1 — Gold, Through Its Views Only**](/part_2/05-query-layer.md)
