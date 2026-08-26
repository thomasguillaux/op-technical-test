# Technical Test — Data Engineer

GCP scalability design (**Part 1**) and LLM agent integration (**Part 2**), for a programmatic-advertising analytics platform anonymised here as **OptimusAds**: ~2B bid-stream events/day, hundreds of publishers, a 10-person Yield team.

Every decision is argued on the page that makes it — requirement satisfied, alternative beaten, rejected options in a table. No decision log outside the write-up.

## Read it

```
python3 -m http.server 3000
```

then open `http://localhost:3000` — it's a [docsify](https://docsify.js.org) site, `index.html` renders the Markdown pages live, no build step.

Or read the Markdown directly, starting from [`introduction.md`](introduction.md).

## Structure

```
introduction.md               the eight arguments the design rests on
intro/                        methodology + business assumptions (given, not derived)
part_1/  01 … 06              ingestion → BigQuery medallion model, one page per test bullet
part_2/  01 … 06              copilot over the Part 1 Gold layer, one page per test bullet
CONTEXT.md                    domain vocabulary
diagrams_src/ → assets/       diagram sources (rendered with .venv/bin/python diagrams_src/<file>.py)
```

`_sidebar.md` drives navigation. There is no routing layer: every page opens with its own claim and carries its own argument, so a page reached from search stands alone.
