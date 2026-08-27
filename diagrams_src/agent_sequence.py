"""Part 2 — one question, turn by turn.

The hop table on 1.2 lists the mechanism per hop; this draws the order and the
round trips, which a table cannot show: four calls to Gemini, three to BigQuery,
and the routing flip that lets the model stop calling tools and write.

Colour carries authorship, the same encoding as the tool table above it:
violet is a payload Gemini authored, teal is one we authored, grey is data
coming back. Rendered on the site's own palette — the write-up is light-only.

Renders to assets/agent-sequence.svg
"""

from pathlib import Path

# --------------------------------------------------------------------- palette
NAVY = "#090056"
VIOLET = "#6d28d9"   # the model authored this payload
TEAL = "#0f8f76"     # we authored this payload
GREY = "#6b6b85"     # rows coming back
FAINT = "#c9c5e8"

FONT = ("-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, "
        "Helvetica, Arial, sans-serif")

# --------------------------------------------------------------------- layout
LANES = ["Analyst", "FastAPI", "Gemini", "semantic views"]
LANE_X = [130, 400, 720, 1040]
LANE_W = 150

TOP = 22           # lane box top
BOX_H = 38
HEAD = TOP + BOX_H  # lifelines start here
FIRST = 96         # first message baseline
STEP = 42
PAD_BOTTOM = 40

WIDTH = 1180

# (source lane, target lane, label, kind)
#   kind: "model" — Gemini wrote it | "ours" — our code wrote it | "back" — rows
MESSAGES = [
    (0, 1, "POST /ask — one question",                  "back"),
    (1, 2, "contents[1] + tools + tool_config ANY",     "ours"),
    (2, 1, 'functionCall resolve_entity("Nortline")',   "model"),
    (1, 3, "our SQL: EDIT_DISTANCE + SOUNDEX",          "ours"),
    (3, 1, "1 candidate: northline",                    "back"),
    (1, 2, "contents[3] — + functionResponse",          "ours"),
    (2, 1, "functionCall check_quality(day, 08-26)",    "model"),
    (1, 3, "our SQL: v_quality_hour",                   "ours"),
    (3, 1, "24/24 hours settled",                       "back"),
    (1, 2, "contents[5]",                               "ours"),
    (2, 1, "functionCall diagnose_change(ecpm, …)",     "model"),
    (1, 3, "our SQL × 4 — one per dimension",           "ours"),
    (3, 1, "segments, rate and mix",                    "back"),
    (1, 2, "contents[7] + tool_config NONE",            "ours"),
    (2, 1, "prose — the only text part of the run",     "model"),
    (1, 0, "answer + SQL + rows + verdict",             "back"),
]

# The routing flip sits before this message: everything above it is the model
# being forced to call a tool, everything below is it being allowed to answer.
DIVIDER_BEFORE = 13

COLOR = {"model": VIOLET, "ours": TEAL, "back": GREY}
HEIGHT = FIRST + (len(MESSAGES) - 1) * STEP + PAD_BOTTOM


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build() -> str:
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'role="img" aria-label="One question through the copilot: the analyst posts to '
        f'FastAPI, which calls Gemini four times and BigQuery three times — resolve_entity, '
        f'check_quality and diagnose_change — then relaxes tool_config to NONE so the model '
        f'writes prose.">',
        "<defs>",
    ]
    for kind, color in COLOR.items():
        out.append(
            f'<marker id="ah-{kind}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{color}"/></marker>'
        )
    out.append("</defs>")
    out.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>')
    out.append(f'<g font-family="{FONT}">')

    # lanes
    bottom = HEIGHT - 16
    for name, x in zip(LANES, LANE_X):
        out.append(
            f'<rect x="{x - LANE_W // 2}" y="{TOP}" width="{LANE_W}" height="{BOX_H}" '
            f'rx="3" fill="#ffffff" stroke="{NAVY}" stroke-width="1.3"/>'
        )
        out.append(
            f'<text x="{x}" y="{TOP + 25}" text-anchor="middle" font-size="14" '
            f'font-weight="600" fill="{NAVY}">{esc(name)}</text>'
        )
        out.append(
            f'<line x1="{x}" y1="{HEAD}" x2="{x}" y2="{bottom}" stroke="{FAINT}" '
            f'stroke-width="1.2" stroke-dasharray="3 5"/>'
        )

    # messages
    for i, (src, dst, label, kind) in enumerate(MESSAGES):
        y = FIRST + i * STEP
        color = COLOR[kind]
        x0, x1 = LANE_X[src], LANE_X[dst]
        # stop short of the lifeline so the arrowhead is not sitting on it
        x1 += -6 if x1 > x0 else 6

        if i == DIVIDER_BEFORE:
            dy = y - 26
            out.append(
                f'<line x1="40" y1="{dy}" x2="{WIDTH - 40}" y2="{dy}" stroke="{FAINT}" '
                f'stroke-width="1" stroke-dasharray="2 6"/>'
            )
            out.append(
                f'<text x="{WIDTH - 40}" y="{dy + 15}" text-anchor="end" font-size="11" '
                f'letter-spacing="1.2" fill="{GREY}">'
                f'EXIT — ROUTING RELAXED TO NONE</text>'
            )

        weight = "600" if i == DIVIDER_BEFORE else "400"
        out.append(
            f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{color}" '
            f'stroke-width="1.4" marker-end="url(#ah-{kind})"/>'
        )
        out.append(
            f'<text x="{(x0 + x1) // 2}" y="{y - 9}" text-anchor="middle" font-size="13" '
            f'font-weight="{weight}" fill="{color}">{esc(label)}</text>'
        )

    out.append("</g></svg>")
    return "\n".join(out)


if __name__ == "__main__":
    target = Path(__file__).resolve().parent.parent / "assets" / "agent-sequence.svg"
    target.write_text(build(), encoding="utf-8")
    print(f"wrote {target}")
