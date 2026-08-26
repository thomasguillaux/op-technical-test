# 3.2 — Guardrails

*Test bullet: what guardrails (IAM rights, query quotas, SQL validation) do you plan to put in place to prevent an LLM hallucination from triggering a `SELECT *` on several terabytes of raw data?*

**All three, and the bullet lists them in the reverse of the order they fire.** SQL validation runs first, in our code, before BigQuery is called at all; IAM runs last. Between them sits a fourth the bullet does not name: the dry run, the layer that puts the *engine* rather than the model in charge of the byte estimate.

| # | Layer | What it stops | Enforced by |
|---|---|---|---|
| 1 | **Static validation** | `SELECT *`, anything that is not a single `SELECT`, an object off the allowlist, a missing date predicate | our code, ahead of the BigQuery client |
| 2 | **Dry run** | Whatever the parse let through, priced and resolved by BigQuery | BigQuery, without executing |
| 3 | **`maximum_bytes_billed`** | The scan itself — a ceiling set by us that the model cannot raise | BigQuery, at execution |
| 4 | **IAM grant** (3.1) | Every object outside the semantic dataset, permanently | BigQuery, at authorization |

Query quotas are the bullet's middle term and are deliberately not in this table: they bound a *day* of queries, not one query.

**2 — The dry run.** BigQuery returns bytes-to-be-scanned without executing, plus `referencedTables` — the engine's own resolved list of the objects the query reads. Depending on how it expands a view, that list names the view or the Gold table behind it, so the check accepts both: every resolved object must sit in the semantic dataset or the Gold dataset it is authorized over.

That checks the objects twice, once against our parse and once against BigQuery's. **A parser can be wrong about what a query names; the engine cannot.**

**3 — `maximum_bytes_billed`.** A query estimated above it fails without incurring a charge, returning `Query exceeded limit for bytes billed: … or higher required.` Layers 1 and 2 are code we wrote and could get wrong; this one holds if both do.

Set on every job the orchestrator issues, not only on `run_query`. Layers 1 and 2 rightly skip `diagnose_change` and `resolve_entity` — their SQL is ours, and re-parsing our own statements against our own allowlist tests nothing a unit test does not. Their *scope* is still the model's: it picks `period` and `filters`, and a year-long period makes correct fixed SQL scan twenty-four months of every publisher. On the free-SQL path the ceiling bounds a statement the model wrote. On the fixed path, it bounds the arguments the model chose.

**4 — IAM, the grant argued in 3.1.** The only layer that does not depend on any code of ours being right.

## The bullet's own scenario, run through the stack

`SELECT * FROM bronze_events` dies at layer 1, three times over in one statement: a `SELECT *`, an object off the allowlist, no date predicate — any one of the three rejects it on its own.

**But the guardrails are what make that failure loud; the grant is what makes it impossible.** Delete every line of the validator, skip the dry run, unset the ceiling — the query still fails, because the service account has no permission on `bronze_events` and never has had one. The three code layers exist to turn a hallucination into a rejection with a reason we can log. The terabyte scan the bullet asks about was already unreachable.

## Query quotas — the layer that bounds N, not one query

A model in a retry loop is not one job, and neither is ten analysts on a bad afternoon. A hundred queries each individually under the ceiling is a bill no layer above has looked at.

BigQuery's custom quotas close it. `QueryUsagePerUserPerDay` applies per user and per service account, so it caps the copilot's entire day independently of the humans; `QueryUsagePerDay` caps the project. Both are proactive: a query that would exceed the remaining allowance does not run, rather than running and being counted afterwards.

**They apply only under on-demand pricing.** Part 1's compute-billing choice is therefore a precondition for this guardrail, not an unrelated cost decision, and it is the same choice that makes a hallucinated heavy query fail *alone*. Under a shared BigQuery Editions reservation it takes slots from the pipeline and starves Silver's 30-minute cadence. The copilot's blast radius stops being a bill and becomes a freshness incident, the worse failure.

And Google documents custom quotas as approximate — *"an additional safeguard against excessive spending… not designed to strictly limit bytes processed"*. This is a spend bound, not an accounting control.

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

## What the four layers do not cover

The narration is unguarded. Even when the fixed routine returns a correct, deterministic result set, the model writes the prose describing it — and prose can misrepresent a correct table. The mitigation is already in the flow: the executed SQL and the rows returned with the answer, which is what makes a *what* answer checkable at all.

None of these layers makes an answer true. Every one of them bounds blast radius and spend. Correctness is 1.1's job, and the fact that those are two different problems is why the design splits the question classes rather than piling guardrails onto a single path.

Prompt injection has no surface here. The classic vector is untrusted prose sitting in a retrieved corpus. The client's *"no free text, only auction-related data"* means there is no prose anywhere in this data — every field is an enumeration or a number. The only untrusted input is the question itself, typed by one of ten employees.

**Cost.** A dry run consumes no slots and is not billed, so the estimate that prevents the expensive query is itself free. The ceiling and the daily quota are insurance, not levers: they bound the worst query and the worst month, and change the bill only on the day something goes wrong. What moves the monthly total is not on this page — it is the grant in 3.1, which decides what a *normal* question scans.

## Rejected — one line each

| Option | Why not |
|---|---|
| **An LLM reviewing the LLM's SQL** | A second model with the same failure mode, in the seam where a deterministic check belongs; its verdict is exactly as uncheckable as the query it reviews |
| **Regex-only validation** | Comments, string literals and nested subqueries defeat pattern matching. A parser resolves the statement, and the dry run resolves the objects |
| **Per-query human approval** | Puts an engineer in the loop of a tool bought to remove one, and the four layers already make the bad outcome a failed query |
| **A cost estimate shown to the user, no hard ceiling** | Moves the decision to whoever is least equipped to judge it, and depends on someone reading it |

---

Part 2 complete. Back to [**the section index**](/part2-llm-agent.md), or [**Part 1 — Data Pipeline**](/part1-pipeline.md).
