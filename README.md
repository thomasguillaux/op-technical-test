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
introduction.md, intro/       methodology + business assumptions (given, not derived)
part1-pipeline.md, part_1/    ingestion → BigQuery medallion model
part2-llm-agent.md, part_2/   copilot over the Part 1 Gold layer
CONTEXT.md                    domain vocabulary
diagrams_src/ → assets/       diagram sources (rendered with .venv/bin/python diagrams_src/<file>.py)
```

`_sidebar.md` drives navigation; the three top-level pages route into the numbered pages under `intro/`, `part_1/`, `part_2/`, which carry the actual arguments.
