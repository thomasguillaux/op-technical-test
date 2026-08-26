# 3.2 — Guardrails

*Test bullet: what guardrails (IAM rights, query quotas, SQL validation) do you plan to put in place to prevent an LLM hallucination from triggering a `SELECT *` on several terabytes of raw data?*

**All three the bullet names, in the reverse of the order it lists them — plus two it does not.** Static validation runs first, in our code, before BigQuery is called at all. Then a dry run, which puts the *engine* rather than the model in charge of the byte estimate. Then `maximum_bytes_billed`. Then the IAM grant, last and permanent. Query quotas sit beside this: they bound a day, not a query.

---

| # | Layer | What it stops | Enforced by |
|---|---|---|---|
| 1 | **Static validation** | `SELECT *`, anything that is not a single `SELECT`, an object off the allowlist, a missing date predicate | our code, ahead of the BigQuery client |
| 2 | **Dry run** | Whatever the parse let through, priced and resolved by BigQuery | BigQuery, without executing |
| 3 | **`maximum_bytes_billed`** | The scan itself — a ceiling set by us that the model cannot raise | BigQuery, at execution |
| 4 | **IAM grant** (3.1) | Every object outside the semantic dataset, permanently | BigQuery, at authorization |

Query quotas are the bullet's middle term and are deliberately not in this table: they bound a *day* of queries, not one query.

## Query quotas — the layer that bounds N, not one query

A model in a retry loop is not one job, and neither is ten analysts on a bad afternoon. A hundred queries each individually under the ceiling is a bill no layer above has looked at.

BigQuery's custom quotas close it. `QueryUsagePerUserPerDay` applies per user and per service account, so it caps the copilot's entire day independently of the humans; `QueryUsagePerDay` caps the project. Both are proactive: a query that would exceed the remaining allowance does not run, rather than running and being counted afterwards.

## The guarded execution path

```python
PROJECT, DATASET = "optimusads-analytics", "semantic"
ALLOWED = load_allowlist()
GOLD = f"{PROJECT}.gold"             # what those views read, and the only other dataset a job may touch
DATE_COLS = {"auction_hour", "day"}  # the partitioning column, at either grain
MAX_BYTES = 20 * 1024**3             # orders of magnitude above any legitimate question

def _fq(t: exp.Table) -> str:
    return f"{t.catalog or PROJECT}.{t.db or DATASET}.{t.name}"

def _is_star(p: exp.Expression) -> bool:
    # SELECT * and SELECT t.* — not COUNT(*), whose star is an argument, not a projection
    return isinstance(p, exp.Star) or (isinstance(p, exp.Column) and isinstance(p.this, exp.Star))

def validate(sql: str) -> None:
    statements = sqlglot.parse(sql, read="bigquery")
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise Rejected("one SELECT statement, and nothing else")
    tree = statements[0]
    for select in tree.find_all(exp.Select):          # subqueries included
        if any(_is_star(p) for p in select.expressions):
            raise Rejected("SELECT * is not allowed")
    ctes = {cte.alias for cte in tree.find_all(exp.CTE)}   # a CTE name is not an object
    for table in tree.find_all(exp.Table):
        if table.name not in ctes and _fq(table) not in ALLOWED:
            raise Rejected(f"{_fq(table)} is not on the allowlist")
    # any WHERE in the tree — the predicate that prunes sits where the view is read,
    # which is the innermost query, not necessarily the outermost one
    if not any(c.name in DATE_COLS
               for w in tree.find_all(exp.Where) for c in w.find_all(exp.Column)):
        raise Rejected("a predicate on the partitioning date column is required")

def execute(sql: str, client: bigquery.Client, params=None):
    return client.query(sql, bigquery.QueryJobConfig(
        maximum_bytes_billed=MAX_BYTES,
        query_parameters=params or [],
    )).result()

def run_query(sql: str, client: bigquery.Client):     # layers 1-2: model-written SQL only
    validate(sql)

    dry = client.query(sql, bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
    for t in dry.referenced_tables:                   # the engine's resolution, not our parse
        fq = f"{t.project}.{t.dataset_id}.{t.table_id}"
        if fq not in ALLOWED and f"{t.project}.{t.dataset_id}" != GOLD:
            raise Rejected(f"{fq} is outside the semantic dataset and Gold")
    if dry.total_bytes_processed > MAX_BYTES:
        raise Rejected(f"{dry.total_bytes_processed / 1024**3:.1f} GiB exceeds the ceiling")

    return execute(sql, client)
```

**Cost.** A dry run consumes no slots and is not billed, so the estimate that prevents the expensive query is itself free. The ceiling and the daily quota are insurance, not levers: they bound the worst query and the worst month, and change the bill only on the day something goes wrong. What moves the monthly total is the grant in 3.1, which decides what a *normal* question scans.

## Rejected — one line each

| Option | Why not |
|---|---|
| **An LLM reviewing the LLM's SQL** | A second model with the same failure mode, in the seam where a deterministic check belongs; its verdict is exactly as uncheckable as the query it reviews |
| **Regex-only validation** | Comments, string literals and nested subqueries defeat pattern matching. A parser resolves the statement, and the dry run resolves the objects |
| **Per-query human approval** | Puts an engineer in the loop of a tool bought to remove one, and the four layers already make the bad outcome a failed query |
| **A cost estimate shown to the user, no hard ceiling** | Moves the decision to whoever is least equipped to judge it, and depends on someone reading it |

---

Part 2 complete. Back to [**the introduction**](/introduction.md).
