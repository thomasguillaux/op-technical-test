"""Part 1 master — raw event ingestion to availability for BI.

Hot path and cold path are the layout, not an annotation: everything left of
Bronze is Google-operated and stateless; everything right of it is SQL on a clock.

Renders to assets/architecture.png
"""

from diagrams import Cluster, Diagram, Edge
from diagrams.gcp.analytics import BigQuery, PubSub
from diagrams.gcp.operations import Logging, Monitoring
from diagrams.gcp.storage import GCS
from diagrams.onprem.client import Client, Users

GRAPH_ATTR = {
    "fontsize": "18",
    "bgcolor": "transparent",
    "labelloc": "t",
    "pad": "0.5",
    "nodesep": "0.6",
    "ranksep": "1.1",
    "splines": "spline",
}

with Diagram(
    "OptimusAds — event pipeline, ingestion to BI",
    filename="assets/architecture",
    outformat="png",
    show=False,
    direction="LR",
    graph_attr=GRAPH_ATTR,
):
    with Cluster("Upstream — out of scope", graph_attr={"style": "dashed"}):
        collector = Users("Collector\npublishes the envelope")

    # ---------------------------------------------------------------- hot path
    with Cluster("Hot path — seconds · nothing of ours runs here"):
        topic = PubSub("events topic\ndurable buffer")
        dlq = PubSub("dead-letter topic")
        bronze = BigQuery(
            "BRONZE · bronze_events · 90 days\nPARTITION BY DATE(publish_time)\n"
            "CLUSTER BY publisher_id, ssp_id, event_type"
        )
        archive = GCS("raw archive\nArchive class · indefinite")

    # --------------------------------------------------------------- cold path
    with Cluster("Cold path — Dataform · SQLX on a clock"):
        silver = BigQuery(
            "SILVER · silver_events · 13 months\nevery 30 min · MERGE ON event_id\n"
            "PARTITION BY event_day"
        )
        with Cluster("GOLD — every 4h, trailing 3 days"):
            gold_opp = BigQuery("gold_opportunity\ndenominator: auctions")
            gold_ssp = BigQuery("gold_ssp\ndenominator: bids + no_bids")
            quality = BigQuery("quality_day\nis this day complete?")

    with Cluster("Semantic layer — BigQuery views"):
        v_opp = BigQuery("v_opportunity\neCPM, fill rate, rpm")
        v_ssp = BigQuery("v_ssp\nresponse rate, win rate")

    bi = Client("BI dashboards · D-1\nYield copilot — Part 2")

    with Cluster("Alerting — the one thing Dataform does not ship"):
        logs = Logging("workflow\ninvocations")
        alert = Monitoring("log-based alert")
        team = Users("data team")

    # ------------------------------------------------------------------- edges
    collector >> Edge(label="~23k events/s") >> topic
    topic >> Edge(label="BigQuery subscription") >> bronze
    topic >> Edge(label="Cloud Storage subscription") >> archive
    topic >> Edge(label="schema violation", style="dashed", color="firebrick") >> dlq

    bronze >> Edge(label="watermark\nQUALIFY + MERGE") >> silver
    archive >> Edge(label="BigLake replay", style="dashed", color="darkgreen") >> bronze

    silver >> Edge(label="changed days\n∩ 3-day window") >> gold_opp
    silver >> gold_ssp
    silver >> Edge(label="hourly counts\nlateness p99") >> quality

    gold_opp >> v_opp
    gold_ssp >> v_ssp
    v_opp >> bi
    v_ssp >> bi
    quality >> Edge(style="dotted") >> bi

    silver >> Edge(style="dotted", color="gray") >> logs
    logs >> alert >> team
