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
    """Render the physics breakdown card with live values."""

    # ── Governing equations section ────────────────────
    st.markdown(
        '<div class="physics-card">'
        '<div class="physics-title">GOVERNING EQUATIONS</div>'
        #
        # Energy balance
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
        '</div>'
        #
        # Airflow sizing
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
        '</div>'
        #
        # Coolant sizing
        '<div class="eq-group">'
        '<div class="eq-label">Required Coolant Flow</div>'
        '<div class="eq-formula">'
        'm&#775;<sub>w</sub> = Q / (c<sub>p,w</sub> &middot; &Delta;T<sub>w</sub>)'
        '</div>'
        f'<div class="eq-sub">'
        f'= {q_total_w:.0f} / (4186 &middot; {delta_t_water_c:.1f})'
        f' &rarr; <span class="eq-result">{coolant_lpm:.2f} L/min</span>'
        f'</div>'
        '</div>'
        #
        # Coil leaving temp
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
        '</div>'
        #
        # Ambient coupling
        '<div class="eq-group">'
        '<div class="eq-label">Ambient Heat Transfer</div>'
        '<div class="eq-formula">'
        'Q<sub>amb</sub> = UA &middot; (T<sub>a</sub> &minus; T<sub>e</sub>)'
        '</div>'
        f'<div class="eq-note">'
        f'UA = {ua_value:.1f} W/K &nbsp;|&nbsp; '
        f'Includes conduction + infiltration'
        f'</div>'
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
