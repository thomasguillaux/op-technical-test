"""Part 2 — the copilot flow, its guardrails, and what it cannot reach.

Three test bullets in one picture: the user/orchestrator/model/BigQuery flow,
the semantic layer as the only object the agent can name, and the guardrail
stack plus the layer choice — argued by showing what sits outside the grant.

Renders to assets/agent.png
"""

from diagrams import Cluster, Diagram, Edge
from diagrams.gcp.analytics import BigQuery
from diagrams.gcp.compute import Run
from diagrams.gcp.ml import VertexAI
from diagrams.onprem.client import Users
from diagrams.programming.flowchart import Decision, PredefinedProcess

GRAPH_ATTR = {
    "fontsize": "18",
    "bgcolor": "transparent",
    "labelloc": "t",
    "pad": "1.0",
    "nodesep": "0.5",
    # Labels sit under the node and spill past it, so adjacent ranks collide before the
    # nodes do. In LR this is the horizontal gap — it is set by the widest label, not the
    # widest icon.
    "ranksep": "1.8",
    "splines": "spline",
}

DENIED = Edge(label="no IAM grant", color="firebrick", style="dashed")

# The two return hops close a cycle each — analyst→api→model→analyst, and
# model→v1→v2→v3→v_opp→model. Graphviz ranks on a DAG, so it breaks a cycle by
# reversing an edge of its own choosing, and it picks analyst→api: the user lands
# mid-canvas with its question arrow pointing backwards. constraint=false draws the
# return without letting it vote on rank, which is what keeps the flow left-to-right.
RETURN = {"color": "darkgreen", "style": "dashed", "penwidth": "1.2", "constraint": "false"}

with Diagram(
    "OptimusAds — Yield copilot: flow, guardrails, blast radius",
    filename="assets/agent",
    outformat="png",
    show=False,
    direction="LR",
    graph_attr=GRAPH_ATTR,
):
    analyst = Users('Yield analyst\n"why did eCPM drop 20%?"')

    with Cluster("Orchestrator — our code"):
        api = Run("FastAPI\nassembles context")
        dictionary = PredefinedProcess(
            "metric dictionary\nINFORMATION_SCHEMA → prompt"
        )

    model = VertexAI("Gemini on Vertex AI\nselects a tool — writes no plan")

    with Cluster("run_query — free SQL, because a wrong number gets caught"):
        v1 = Decision("1. static validation\nsingle SELECT, allowlist,\ndate predicate required")
        v2 = Decision("2. dry run\nbytes estimated by the engine")

    # Both tools run SQL we wrote, so neither gets a box of its own — the caption that
    # was a cluster label lives in the node, and two fewer rectangles read faster.
    diagnose = PredefinedProcess(
        "diagnose_change(grain)\nfixed SQL, because a wrong\nexplanation is not caught\n"
        "settled? → structural →\nrate vs mix effect"
    )

    resolve = PredefinedProcess("resolve_entity\nlive dimension values,\nnot a vector index")

    # Layers 1 and 2 parse model-written SQL, so they are run_query-only. The ceiling is not:
    # a routine we wrote still runs over a period the model chose. Every path converges here,
    # which is also what makes the denial below identity-wide rather than run_query's alone.
    v3 = Decision("3. maximum_bytes_billed\nevery job — the model's SQL\nand its arguments")

    with Cluster("4. IAM — one dataset, authorized on Gold. The only SELECT grant"):
        v_opp = BigQuery("v_opportunity_hourly / _daily")
        v_ssp = BigQuery("v_ssp_hourly / _daily")
        quality = BigQuery("v_quality_hour")

    raw = BigQuery(
        "OUTSIDE THE GRANT\nbronze_events · silver_events\ngold base tables"
    )

    # ------------------------------------------------------------------ flow
    analyst >> api
    dictionary >> Edge(style="dotted") >> api
    api >> Edge(label="question + tools + dictionary") >> model

    model >> Edge(label="what — a number") >> v1
    v1 >> v2 >> v3
    model >> Edge(label="why — a cause") >> diagnose
    model >> Edge(label='"site Y"', style="dotted") >> resolve

    # Both tool paths converge on the ceiling, so the picture shows what the prose claims:
    # one execution seam, one grant, and the same views underneath either kind of SQL.
    diagnose >> v3
    resolve >> Edge(style="dotted") >> v3

    v3 >> v_opp
    v3 >> v_ssp
    v3 >> Edge(label="is the period settled?", style="dotted") >> quality

    v3 >> DENIED >> raw

    # The return path never lets the model touch either end directly, which is the same claim
    # the forward path makes. Rows come back from the executor, not from the view — drawing
    # v_opp >> model put a line through the IAM cluster next to the denial edge, reading as a
    # second way out of the grant. And the narration goes home via FastAPI, because one
    # stateless POST means the analyst's only correspondent is the orchestrator.
    v3 >> Edge(label="rows", **RETURN) >> model
    model >> Edge(label="narration", **RETURN) >> api
    api >> Edge(label="answer + SQL + rows + verdict", **RETURN) >> analyst
