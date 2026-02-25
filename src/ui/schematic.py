"""Interactive system schematic using Plotly.

Renders the thermal loop: enclosure ↔ coil via return/supply air paths,
with ambient coupling above the enclosure and coolant below the coil.

Layout coordinates (x: 0–13, y: 0–10, no scaleanchor):
  Enclosure box  : (0.5, 2.5) → (5.5, 7.5)
  Coil box       : (8.5, 3.0) → (12.5, 7.0)
  Gap (x 5.5–8.5): return air arrow at y=6.5, supply air arrow at y=3.5
  Ambient        : above enclosure, arrow from y=9.2 → 7.5
  Coolant        : below coil, arrow from y=1.8 → 3.0
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

    BG       = "#0D1117"
    PANEL    = "#161B22"
    TEAL     = "#00D4AA"
    BLUE     = "#58A6FF"
    TEXT     = "#E6EDF3"
    MUTED    = "#8B949E"
    AMBER    = "#F0A830"
    DIVIDER  = "#30363D"

    # ── Subtle gap divider lines ────────────────────────
    for x in (5.5, 8.5):
        fig.add_shape(
            type="line", x0=x, y0=2.8, x1=x, y1=7.2,
            line=dict(color=DIVIDER, width=1, dash="dot"),
        )

    # ── Enclosure box ───────────────────────────────────
    fig.add_shape(
        type="rect", x0=0.5, y0=2.5, x1=5.5, y1=7.5,
        line=dict(color=TEAL, width=2.5),
        fillcolor=PANEL,
    )
    fig.add_annotation(
        x=3.0, y=7.05, text="<b>ENCLOSURE</b>",
        font=dict(color=TEXT, size=14, family="DM Sans"),
        showarrow=False,
    )
    fig.add_annotation(
        x=3.0, y=5.8, text=f"T = {enclosure_temp_c:.1f} °C",
        font=dict(color=TEAL, size=17, family="JetBrains Mono"),
        showarrow=False,
    )
    fig.add_annotation(
        x=3.0, y=4.55, text=f"Q<sub>load</sub> = {heat_load_w:.0f} W",
        font=dict(color=AMBER, size=13, family="JetBrains Mono"),
        showarrow=False,
    )
    fig.add_annotation(
        x=3.0, y=3.45, text=f"UA = {ua_value:.1f} W/K",
        font=dict(color=MUTED, size=11, family="JetBrains Mono"),
        showarrow=False,
    )

    # ── Coil / HX box ───────────────────────────────────
    fig.add_shape(
        type="rect", x0=8.5, y0=3.0, x1=12.5, y1=7.0,
        line=dict(color=BLUE, width=2.5),
        fillcolor=PANEL,
    )
    fig.add_annotation(
        x=10.5, y=6.55, text="<b>COIL / HX</b>",
        font=dict(color=TEXT, size=13, family="DM Sans"),
        showarrow=False,
    )
    fig.add_annotation(
        x=10.5, y=5.5, text=f"T<sub>sup</sub> = {supply_temp_c:.1f} °C",
        font=dict(color=BLUE, size=14, family="JetBrains Mono"),
        showarrow=False,
    )
    fig.add_annotation(
        x=10.5, y=4.4, text=f"CW = {chilled_water_temp_c:.0f} °C",
        font=dict(color=BLUE, size=12, family="JetBrains Mono"),
        showarrow=False,
    )

    # ── Return air: enclosure → coil (top of gap, y=6.5) ─
    fig.add_annotation(
        x=8.5, y=6.5, ax=5.5, ay=6.5,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=2, arrowsize=1.6,
        arrowcolor=MUTED, arrowwidth=2.5,
    )
    fig.add_annotation(
        x=7.0, y=7.05,
        text=f"Return  {return_temp_c:.1f} °C",
        font=dict(color=MUTED, size=11, family="JetBrains Mono"),
        showarrow=False,
    )

    # ── Supply air: coil → enclosure (bottom of gap, y=3.5) ─
    fig.add_annotation(
        x=5.5, y=3.5, ax=8.5, ay=3.5,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=2, arrowsize=1.6,
        arrowcolor=TEAL, arrowwidth=2.5,
    )
    fig.add_annotation(
        x=7.0, y=2.9,
        text=f"Supply  {supply_temp_c:.1f} °C  ·  {airflow_cfm:.0f} CFM",
        font=dict(color=TEAL, size=11, family="JetBrains Mono"),
        showarrow=False,
    )

    # ── Ambient coupling (above enclosure) ─────────────
    fig.add_annotation(
        x=3.0, y=7.5, ax=3.0, ay=9.1,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=3, arrowsize=1.4,
        arrowcolor=MUTED, arrowwidth=2,
    )
    fig.add_annotation(
        x=3.0, y=9.45,
        text=f"Ambient  {ambient_temp_c:.1f} °C",
        font=dict(color=MUTED, size=12, family="JetBrains Mono"),
        showarrow=False,
    )

    # ── Coolant supply (below coil) ─────────────────────
    fig.add_annotation(
        x=10.5, y=3.0, ax=10.5, ay=1.9,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=3, arrowsize=1.3,
        arrowcolor=BLUE, arrowwidth=2,
    )
    fig.add_annotation(
        x=10.5, y=1.45,
        text=f"Coolant  {chilled_water_temp_c:.0f} °C  ·  {coolant_lpm:.2f} L/min",
        font=dict(color=BLUE, size=11, family="JetBrains Mono"),
        showarrow=False,
    )

    # ── Layout ─────────────────────────────────────────
    fig.update_layout(
        xaxis=dict(visible=False, range=[0, 13]),
        yaxis=dict(visible=False, range=[0, 10]),
        plot_bgcolor=BG,
        paper_bgcolor=BG,
        margin=dict(l=5, r=5, t=5, b=5),
        height=420,
        font=dict(family="DM Sans"),
    )

    return fig
