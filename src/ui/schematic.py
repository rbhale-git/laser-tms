"""Interactive system schematic using Plotly.

Renders the thermal loop: enclosure → return air → coil → supply air → enclosure,
with ambient coupling and live value annotations.
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

    # Enclosure box
    fig.add_shape(
        type="rect", x0=1, y0=1, x1=5, y1=4,
        line=dict(color=TEAL, width=2),
        fillcolor=PANEL,
    )
    fig.add_annotation(
        x=3, y=3.5, text="<b>ENCLOSURE</b>",
        font=dict(color=TEXT, size=14, family="DM Sans"),
        showarrow=False,
    )
    fig.add_annotation(
        x=3, y=2.8, text=f"T = {enclosure_temp_c:.1f} °C",
        font=dict(color=TEAL, size=16, family="JetBrains Mono"),
        showarrow=False,
    )
    fig.add_annotation(
        x=3, y=2.2, text=f"Q_load = {heat_load_w:.0f} W",
        font=dict(color=AMBER, size=12, family="JetBrains Mono"),
        showarrow=False,
    )

    # Cooling coil box
    fig.add_shape(
        type="rect", x0=7, y0=1.5, x1=9, y1=3.5,
        line=dict(color=BLUE, width=2),
        fillcolor=PANEL,
    )
    fig.add_annotation(
        x=8, y=3.0, text="<b>COIL</b>",
        font=dict(color=TEXT, size=12, family="DM Sans"),
        showarrow=False,
    )
    fig.add_annotation(
        x=8, y=2.2, text=f"T_out = {supply_temp_c:.1f} °C",
        font=dict(color=BLUE, size=11, family="JetBrains Mono"),
        showarrow=False,
    )

    # Return air arrow: enclosure → coil
    fig.add_annotation(
        x=7, y=3.8, ax=5, ay=3.8,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=2, arrowsize=1.5,
        arrowcolor=SECONDARY, arrowwidth=2,
    )
    fig.add_annotation(
        x=6, y=4.1, text=f"Return {return_temp_c:.1f} °C",
        font=dict(color=SECONDARY, size=10, family="JetBrains Mono"),
        showarrow=False,
    )

    # Supply air arrow: coil → enclosure
    fig.add_annotation(
        x=5, y=1.2, ax=7, ay=1.2,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=2, arrowsize=1.5,
        arrowcolor=TEAL, arrowwidth=2,
    )
    fig.add_annotation(
        x=6, y=0.9, text=f"Supply {supply_temp_c:.1f} °C  |  {airflow_cfm:.0f} CFM",
        font=dict(color=TEAL, size=10, family="JetBrains Mono"),
        showarrow=False,
    )

    # Ambient coupling
    fig.add_annotation(
        x=3, y=5.0, text=f"Ambient {ambient_temp_c:.1f} °C",
        font=dict(color=SECONDARY, size=11, family="JetBrains Mono"),
        showarrow=False,
    )
    fig.add_annotation(
        x=3, y=4.0, ax=3, ay=4.6,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=3, arrowsize=1,
        arrowcolor=SECONDARY, arrowwidth=1,
    )
    fig.add_annotation(
        x=3.8, y=4.5, text=f"UA = {ua_value:.1f} W/K",
        font=dict(color=SECONDARY, size=9, family="JetBrains Mono"),
        showarrow=False,
    )

    # Coolant annotation
    fig.add_annotation(
        x=8, y=1.1, text=f"Coolant: {chilled_water_temp_c:.0f} °C  |  {coolant_lpm:.2f} L/min",
        font=dict(color=BLUE, size=10, family="JetBrains Mono"),
        showarrow=False,
    )

    # Layout
    fig.update_layout(
        xaxis=dict(visible=False, range=[0, 10]),
        yaxis=dict(visible=False, range=[0, 5.5], scaleanchor="x"),
        plot_bgcolor=BG,
        paper_bgcolor=BG,
        margin=dict(l=0, r=0, t=10, b=10),
        height=320,
        font=dict(family="DM Sans"),
    )

    return fig
