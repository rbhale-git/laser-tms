"""Physics reference card — engineering handbook-style breakdown.

Renders below the system schematic. Shows governing equations with
live variable substitutions and a control variable glossary.
"""
import streamlit as st


def render_physics_card(
    q_total_w: float,
    delta_t_air_c: float,
    delta_t_water_c: float,
    ua_value: float,
    ambient_temp_c: float,
    setpoint_c: float,
    airflow_cfm: float,
    airflow_m3s: float,
    coolant_lpm: float,
    coil_leaving_temp_c: float,
    thermal_capacitance: float,
    volume_m3: float,
) -> None:
    """Render the physics breakdown card with live values and assumptions."""

    # ── Governing equations section ────────────────────
    st.markdown(
        '<div class="physics-card">'
        '<div class="physics-title">GOVERNING EQUATIONS</div>'

        # ── Energy balance ──────────────────────────────
        '<div class="eq-group">'
        '<div class="eq-label">Single-Node Energy Balance</div>'
        '<div class="eq-formula">'
        'C<sub>e</sub> &middot; dT<sub>e</sub>/dt = '
        'Q<sub>load</sub> + UA(T<sub>a</sub> &minus; T<sub>e</sub>) + '
        'm&#775;<sub>air</sub> &middot; c<sub>p</sub> &middot; '
        '(T<sub>sup</sub> &minus; T<sub>e</sub>)'
        '</div>'
        f'<div class="eq-note">'
        f'C<sub>e</sub> = {thermal_capacitance / 1000:.1f} kJ/K &nbsp;|&nbsp; '
        f'At steady state, dT<sub>e</sub>/dt = 0'
        f'</div>'
        '<div class="eq-assume">'
        '<span class="eq-assume-title">Assumes</span>'
        'Lumped capacitance — interior is spatially isothermal (no gradients) &middot; '
        'Heat loads uniformly distributed &middot; '
        'UA constant (independent of &Delta;T and flow velocity) &middot; '
        'Radiation negligible or linearised into UA &middot; '
        'Air well-mixed throughout enclosure volume'
        '</div>'
        '</div>'

        # ── Airflow sizing ──────────────────────────────
        '<div class="eq-group">'
        '<div class="eq-label">Required Airflow</div>'
        '<div class="eq-formula">'
        'm&#775;<sub>air</sub> = Q / (c<sub>p</sub> &middot; &Delta;T<sub>air</sub>)'
        '</div>'
        f'<div class="eq-sub">'
        f'= {q_total_w:.0f} / (1005 &middot; {delta_t_air_c:.1f})'
        f' &rarr; <span class="eq-result">{airflow_cfm:.1f} CFM</span>'
        f' ({airflow_m3s:.4f} m&sup3;/s)'
        f'</div>'
        '<div class="eq-assume">'
        '<span class="eq-assume-title">Assumes</span>'
        'Constant air properties (c<sub>p</sub> = 1005 J/kg&middot;K at standard lab conditions) &middot; '
        'Sensible heat only — no moisture condensation or latent load &middot; '
        'All heat load removed by airflow (no direct conduction bypass) &middot; '
        'Uniform temperature across supply and return cross-sections &middot; '
        'Incompressible, steady flow'
        '</div>'
        '</div>'

        # ── Coolant sizing ──────────────────────────────
        '<div class="eq-group">'
        '<div class="eq-label">Required Coolant Flow</div>'
        '<div class="eq-formula">'
        'm&#775;<sub>w</sub> = Q / (c<sub>p,w</sub> &middot; &Delta;T<sub>w</sub>)'
        '</div>'
        f'<div class="eq-sub">'
        f'= {q_total_w:.0f} / (4186 &middot; {delta_t_water_c:.1f})'
        f' &rarr; <span class="eq-result">{coolant_lpm:.2f} L/min</span>'
        f'</div>'
        '<div class="eq-assume">'
        '<span class="eq-assume-title">Assumes</span>'
        'Single-phase liquid — no boiling or phase change &middot; '
        'Constant c<sub>p,w</sub> = 4186 J/kg&middot;K (pure water; antifreeze additives will alter this) &middot; '
        'All enclosure heat rejected to coolant (no thermal bypass around coil) &middot; '
        'Coolant inlet temperature equals chilled water supply setpoint &middot; '
        'Pump heat addition negligible'
        '</div>'
        '</div>'

        # ── Coil leaving temp ───────────────────────────
        '<div class="eq-group">'
        '<div class="eq-label">Coil Leaving Air Temperature</div>'
        '<div class="eq-formula">'
        'T<sub>sup</sub> = T<sub>return</sub> '
        '&minus; Q / (m&#775;<sub>air</sub> &middot; c<sub>p</sub>)'
        '</div>'
        f'<div class="eq-sub">'
        f'= {ambient_temp_c:.1f} &minus; {delta_t_air_c:.1f}'
        f' = <span class="eq-result">{coil_leaving_temp_c:.1f} &deg;C</span>'
        f'</div>'
        '<div class="eq-assume">'
        '<span class="eq-assume-title">Assumes</span>'
        'Return air temperature equals enclosure setpoint (well-mixed interior) &middot; '
        'Sensible cooling only — no latent load at the coil &middot; '
        'Negligible duct heat gain between coil and enclosure inlet &middot; '
        'Coil approach temperature constraint is not binding (coil not saturated) &middot; '
        'Coil effectiveness sufficient to deliver the computed leaving temperature'
        '</div>'
        '</div>'

        # ── Ambient coupling ────────────────────────────
        '<div class="eq-group">'
        '<div class="eq-label">Ambient Heat Transfer</div>'
        '<div class="eq-formula">'
        'Q<sub>amb</sub> = UA &middot; (T<sub>a</sub> &minus; T<sub>e</sub>)'
        '</div>'
        f'<div class="eq-note">'
        f'UA = {ua_value:.1f} W/K &nbsp;|&nbsp; '
        f'Includes conduction + infiltration'
        f'</div>'
        '<div class="eq-assume">'
        '<span class="eq-assume-title">Assumes</span>'
        'Linear (Newtonian) heat transfer — UA independent of temperature difference &middot; '
        'Ambient temperature is spatially uniform around all enclosure surfaces &middot; '
        'UA is time-invariant (no insulation degradation, no exterior airflow variation) &middot; '
        'Air infiltration heat gain included in UA via the ACH input path &middot; '
        'Radiation treated as linearised and absorbed into the effective UA'
        '</div>'
        '</div>'

        '</div>',
        unsafe_allow_html=True,
    )

    # ── Control variable glossary ──────────────────────
    st.markdown(
        '<div class="physics-card" style="margin-top:0.5rem">'
        '<div class="physics-title">CONTROL VARIABLES</div>'
        '<table class="var-table">'
        '<tr>'
        '<td class="var-sym">Q<sub>load</sub></td>'
        '<td class="var-desc">Internal heat generation</td>'
        f'<td class="var-val">{q_total_w:.0f} W</td>'
        '<td class="var-control">Set by laser hardware</td>'
        '</tr>'
        '<tr>'
        '<td class="var-sym">&Delta;T<sub>air</sub></td>'
        '<td class="var-desc">Air temperature rise across enclosure</td>'
        f'<td class="var-val">{delta_t_air_c:.1f} &deg;C</td>'
        '<td class="var-control">Determines required airflow</td>'
        '</tr>'
        '<tr>'
        '<td class="var-sym">&Delta;T<sub>w</sub></td>'
        '<td class="var-desc">Coolant temperature rise across coil</td>'
        f'<td class="var-val">{delta_t_water_c:.1f} &deg;C</td>'
        '<td class="var-control">Determines required coolant flow</td>'
        '</tr>'
        '<tr>'
        '<td class="var-sym">UA</td>'
        '<td class="var-desc">Enclosure-to-ambient thermal coupling</td>'
        f'<td class="var-val">{ua_value:.1f} W/K</td>'
        '<td class="var-control">Enclosure insulation quality</td>'
        '</tr>'
        '<tr>'
        '<td class="var-sym">T<sub>a</sub></td>'
        '<td class="var-desc">Ambient (lab) temperature</td>'
        f'<td class="var-val">{ambient_temp_c:.1f} &deg;C</td>'
        '<td class="var-control">Lab HVAC setpoint</td>'
        '</tr>'
        '<tr>'
        '<td class="var-sym">C<sub>e</sub></td>'
        '<td class="var-desc">Enclosure thermal capacitance</td>'
        f'<td class="var-val">{thermal_capacitance / 1000:.1f} kJ/K</td>'
        '<td class="var-control">Hardware mass + air volume</td>'
        '</tr>'
        '<tr>'
        '<td class="var-sym">V</td>'
        '<td class="var-desc">Enclosure air volume</td>'
        f'<td class="var-val">{volume_m3:.3f} m&sup3;</td>'
        '<td class="var-control">Geometry (L &times; W &times; H)</td>'
        '</tr>'
        '</table>'
        '<div class="var-footnote">'
        'c<sub>p,air</sub> = 1005 J/(kg&middot;K) &nbsp;&nbsp; '
        '&rho;<sub>air</sub> = 1.19 kg/m&sup3; &nbsp;&nbsp; '
        'c<sub>p,water</sub> = 4186 J/(kg&middot;K)'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
