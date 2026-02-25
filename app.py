"""Quantum Enclosure Thermal Analyzer — Streamlit entry point.

Composes UI panels, builds models, calls solvers, displays results.
Run: streamlit run app.py
"""
import streamlit as st

from src.ui.theme import inject_theme
from src.ui.panel_geometry import render_geometry_panel
from src.ui.panel_loads import render_loads_panel
from src.ui.panel_ambient import render_ambient_panel
from src.ui.panel_cooling import render_cooling_panel
from src.ui.panel_results import render_results_panel
from src.ui.schematic import render_schematic
from src.models import (
    Enclosure, HeatLoads, CoolingPlant, AmbientConditions,
    CoolingType, SolveMode,
)
from src.solvers import (
    solve_airflow, solve_coolant_flow,
    solve_coil_leaving_temp, solve_heater_requirement,
    compute_warnings,
)
from src.units import m3s_to_cfm, kgs_to_lpm
from src.constants import AIR_CP, AIR_DENSITY

st.set_page_config(
    page_title="Quantum Enclosure Thermal Analyzer",
    layout="wide",
)
inject_theme()

# ── Title ──────────────────────────────────────────────
st.markdown(
    '<div class="main-title">QUANTUM ENCLOSURE THERMAL ANALYZER</div>',
    unsafe_allow_html=True,
)

# ── Sidebar: solve mode + unit toggle ──────────────────
with st.sidebar:
    st.markdown("### CONFIGURATION")
    solve_mode = st.selectbox(
        "Solve mode",
        options=[sm for sm in SolveMode],
        format_func=lambda sm: sm.value,
    )
    use_imperial = st.toggle("Imperial units", value=True)
    st.markdown("---")
    st.caption("Phase 1 — Steady-State Sizing")

# ── Input panels (left column) ─────────────────────────
left_col, right_col = st.columns([1, 2])

with left_col:
    geo = render_geometry_panel(use_imperial)
    loads_input = render_loads_panel()
    ambient_input = render_ambient_panel()
    cooling_input = render_cooling_panel(solve_mode)

# ── Build models ───────────────────────────────────────
enclosure = Enclosure(
    length_m=geo["length_m"],
    width_m=geo["width_m"],
    height_m=geo["height_m"],
    internal_thermal_mass=geo["internal_thermal_mass"],
)

loads = HeatLoads(
    baseline_load_w=loads_input["baseline_load_w"],
    additional_loads_w=loads_input["additional_loads_w"],
)

# Handle ACH → UA conversion if needed
ua_value = ambient_input["ua_value"]
if ambient_input.get("ua_mode") == "Air changes per hour (ACH)":
    ach = ambient_input["ua_value"]
    ua_value = ach * enclosure.volume_m3 * AIR_DENSITY * AIR_CP / 3600.0

ambient = AmbientConditions(
    temperature_c=ambient_input["temperature_c"],
    variation_amplitude_c=ambient_input["variation_amplitude_c"],
    variation_period_hr=ambient_input["variation_period_hr"],
    ua_value=ua_value,
)

cooling = CoolingPlant(
    cooling_type=CoolingType(cooling_input["cooling_type"]),
    coil_approach_temp_c=cooling_input["coil_approach_temp_c"],
    coil_max_capacity_w=cooling_input["coil_max_capacity_w"],
    chilled_water_temp_c=cooling_input["chilled_water_temp_c"],
    delta_t_air_c=cooling_input["delta_t_air_c"],
    delta_t_water_c=cooling_input["delta_t_water_c"],
)

# ── Run solvers ────────────────────────────────────────
q_total = loads.total_load_w

# Airflow
air_result = solve_airflow(
    q_total_w=q_total, delta_t_air_c=cooling.delta_t_air_c,
)

# Coolant
coolant_result = solve_coolant_flow(
    q_total_w=q_total, delta_t_water_c=cooling.delta_t_water_c,
)

# Coil leaving temp
coil_result = solve_coil_leaving_temp(
    q_total_w=q_total,
    airflow_kgs=air_result.airflow_kgs,
    return_air_temp_c=ambient.temperature_c,
)

# Heater requirement
heater_result = solve_heater_requirement(
    q_load_w=q_total,
    ua_value=ambient.ua_value,
    ambient_temp_c=ambient.temperature_c,
    setpoint_c=ambient.temperature_c,
)

# Coil utilization
coil_utilization = (q_total / cooling.coil_max_capacity_w) * 100.0

# Warnings
warnings = compute_warnings(
    coil_utilization_pct=coil_utilization,
    heater_required_w=heater_result.heater_required_w,
)

# ── Right column: schematic + results ──────────────────
with right_col:
    cfm = m3s_to_cfm(air_result.airflow_m3s)
    lpm = kgs_to_lpm(coolant_result.coolant_kgs)

    fig = render_schematic(
        enclosure_temp_c=ambient.temperature_c,
        supply_temp_c=coil_result.coil_leaving_temp_c,
        return_temp_c=ambient.temperature_c,
        ambient_temp_c=ambient.temperature_c,
        chilled_water_temp_c=cooling.chilled_water_temp_c,
        airflow_cfm=cfm,
        coolant_lpm=lpm,
        heat_load_w=q_total,
        ua_value=ambient.ua_value,
    )
    st.plotly_chart(fig, use_container_width=True, theme=None)

    render_results_panel(
        airflow_m3s=air_result.airflow_m3s,
        coolant_kgs=coolant_result.coolant_kgs,
        coil_utilization_pct=coil_utilization,
        heater_required_w=heater_result.heater_required_w,
        coil_leaving_temp_c=coil_result.coil_leaving_temp_c,
        warnings=warnings,
    )
