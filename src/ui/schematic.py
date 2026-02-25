"""Interactive system schematic using Plotly.

Renders the thermal loop: enclosure → return air → coil → supply air → enclosure,
with ambient coupling and live value annotations.

Layout coordinates (x: 0-12, y: 0-8):
  - Enclosure box: (1,2) to (5.5,5.5)
  - Coil box: (8,2.5) to (10.5,5)
  - Return air arrow: top path y=6
  - Supply air arrow: bottom path y=1.5
  - Ambient: top center y=7.5
  - Coolant: below coil y=1.5
"""
import plotly.graph_objects as go


def render_schematic(
    enclosure_temp_c: float,
    supply_temp_c: float,
    return_temp_c: float,
    ambient_temp_c: float,
    chilled_water_temp_c: float,
    airflow_cfm: float,
    coolant_lpm: float,
    heat_load_w: float,
    ua_value: float,
) -> go.Figure:
    """Build and return a Plotly figure of the thermal system schematic."""
    fig = go.Figure()

    BG = "#0D1117"
    PANEL = "#161B22"
    TEAL = "#00D4AA"
    BLUE = "#58A6FF"
    TEXT = "#E6EDF3"
    SECONDARY = "#8B949E"
    AMBER = "#F0A830"

    # ── Enclosure box ──────────────────────────────────
    fig.add_shape(
        type="rect", x0=1, y0=2, x1=5.5, y1=5.5,
        line=dict(color=TEAL, width=2),
        fillcolor=PANEL,
    )
    fig.add_annotation(
        x=3.25, y=5.0, text="<b>ENCLOSURE</b>",
        font=dict(color=TEXT, size=13, family="DM Sans"),
        showarrow=False,
    )
    fig.add_annotation(
        x=3.25, y=4.15, text=f"T = {enclosure_temp_c:.1f} °C",
        font=dict(color=TEAL, size=15, family="JetBrains Mono"),
        showarrow=False,
    )
    fig.add_annotation(
        x=3.25, y=3.2, text=f"Q<sub>load</sub> = {heat_load_w:.0f} W",
        font=dict(color=AMBER, size=12, family="JetBrains Mono"),
        showarrow=False,
    )

    # ── Cooling coil box ───────────────────────────────
    fig.add_shape(
        type="rect", x0=8, y0=2.5, x1=10.5, y1=5,
        line=dict(color=BLUE, width=2),
        fillcolor=PANEL,
    )
    fig.add_annotation(
        x=9.25, y=4.5, text="<b>COIL / HX</b>",
        font=dict(color=TEXT, size=11, family="DM Sans"),
        showarrow=False,
    )
    fig.add_annotation(
        x=9.25, y=3.5, text=f"T<sub>out</sub> = {supply_temp_c:.1f} °C",
        font=dict(color=BLUE, size=11, family="JetBrains Mono"),
        showarrow=False,
    )

    # ── Return air path (top): enclosure → coil ────────
    # Horizontal arrow above both boxes
    fig.add_annotation(
        x=8, y=6.0, ax=5.5, ay=6.0,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=2, arrowsize=1.5,
        arrowcolor=SECONDARY, arrowwidth=2,
    )
    fig.add_annotation(
        x=6.75, y=6.4,
        text=f"Return air  {return_temp_c:.1f} °C",
        font=dict(color=SECONDARY, size=10, family="JetBrains Mono"),
        showarrow=False,
    )

    # ── Supply air path (bottom): coil → enclosure ─────
    fig.add_annotation(
        x=5.5, y=1.5, ax=8, ay=1.5,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=2, arrowsize=1.5,
        arrowcolor=TEAL, arrowwidth=2,
    )
    fig.add_annotation(
        x=6.75, y=1.0,
        text=f"Supply  {supply_temp_c:.1f} °C  ·  {airflow_cfm:.0f} CFM",
        font=dict(color=TEAL, size=10, family="JetBrains Mono"),
        showarrow=False,
    )

    # ── Ambient coupling (above enclosure) ─────────────
    fig.add_annotation(
        x=3.25, y=7.5,
        text=f"Ambient  {ambient_temp_c:.1f} °C",
        font=dict(color=SECONDARY, size=11, family="JetBrains Mono"),
        showarrow=False,
    )
    # Downward arrow from ambient to enclosure
    fig.add_annotation(
        x=3.25, y=5.5, ax=3.25, ay=7.0,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=3, arrowsize=1.2,
        arrowcolor=SECONDARY, arrowwidth=1.5,
    )
    fig.add_annotation(
        x=4.6, y=6.7,
        text=f"UA = {ua_value:.1f} W/K",
        font=dict(color=SECONDARY, size=9, family="JetBrains Mono"),
        showarrow=False,
    )

    # ── Coolant annotation (below coil) ────────────────
    fig.add_annotation(
        x=9.25, y=2.0,
        text=f"Coolant  {chilled_water_temp_c:.0f} °C  ·  {coolant_lpm:.2f} L/min",
        font=dict(color=BLUE, size=9, family="JetBrains Mono"),
        showarrow=False,
    )
    # Small arrow into coil from below
    fig.add_annotation(
        x=9.25, y=2.5, ax=9.25, ay=2.1,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=3, arrowsize=1,
        arrowcolor=BLUE, arrowwidth=1,
    )

    # ── Layout ─────────────────────────────────────────
    fig.update_layout(
        xaxis=dict(visible=False, range=[0, 12]),
        yaxis=dict(visible=False, range=[0, 8.2], scaleanchor="x"),
        plot_bgcolor=BG,
        paper_bgcolor=BG,
        margin=dict(l=5, r=5, t=5, b=5),
        height=380,
        font=dict(family="DM Sans"),
    )

    return fig
