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
    "ranksep": "1.0",
    "splines": "spline",
}

DENIED = Edge(label="no IAM grant", color="firebrick", style="dashed")

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
        v3 = Decision("3. maximum_bytes_billed\nceiling the model cannot raise")

    with Cluster("fixed SQL — because a wrong explanation does not"):
        diagnose = PredefinedProcess(
            "diagnose_change(grain)\nsettled? → structural →\nrate effect vs mix effect"
        )

    resolve = PredefinedProcess("resolve_entity\nlive dimension values,\nnot a vector index")

    with Cluster("4. IAM — the only dataset the service account holds SELECT on"):
        v_opp = BigQuery("v_opportunity_hourly / _daily")
        v_ssp = BigQuery("v_ssp_hourly / _daily")
        quality = BigQuery("quality_hour")

    with Cluster("Outside the grant", graph_attr={"style": "dashed"}):
        raw = BigQuery("bronze_events · silver_events\ngold base tables")

    # ------------------------------------------------------------------ flow
    analyst >> Edge(label="question") >> api
    dictionary >> Edge(style="dotted") >> api
    api >> Edge(label="question + tools + dictionary") >> model

    model >> Edge(label="what — a number") >> v1
    v1 >> v2 >> v3
    model >> Edge(label="why — a cause") >> diagnose
    model >> Edge(label='"site Y"', style="dotted") >> resolve

    v3 >> v_opp
    v3 >> v_ssp
    diagnose >> Edge(label="reads the same views") >> v_opp
    diagnose >> v_ssp
    diagnose >> Edge(label="is the period settled?", style="dotted") >> quality
    resolve >> Edge(style="dotted") >> v_opp

    v3 >> DENIED >> raw

    v_opp >> Edge(label="answer + the SQL, shown", color="darkgreen") >> analyst
