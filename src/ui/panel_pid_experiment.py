"""Streamlit panel for the PID experiment tab.

Renders scenario picker, advanced controls, run button, plots, summary stats,
and CSV download. Calls src.sim.experiment.run_experiment under the hood.
"""
from __future__ import annotations
import io
from datetime import datetime

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from defaults import (
    default_fan_params,
    default_pid_controller,
    default_t_setpoint_c,
    default_t_supply_c,
)
from src.constants import AIR_CP, AIR_DENSITY
from src.sim.actuator import FanParams
from src.sim.controller import PIDController
from src.sim.experiment import (
    SimulationResult,
    run_experiment,
    compute_summary,
    compute_experiment_warnings,
)
from src.sim.plant import PlantParams
from src.sim.scenarios import (
    laser_thermal_cycling,
    ambient_step,
    ambient_diurnal,
)
from src.units import cfm_to_m3s, m3s_to_cfm


SCENARIO_BUILDERS = {
    "A — Laser thermal cycling": laser_thermal_cycling,
    "B-sharp — Ambient step ±6.5 °C": ambient_step,
    "B-slow — Ambient diurnal half-sine (6 h)": ambient_diurnal,
}

SCENARIO_DESCRIPTIONS = {
    "A — Laser thermal cycling": (
        "**Tests heat-load disturbance rejection.** 3 cycles of laser on "
        "(100 W, 5 min hold) / off (0 W, 5 min hold) with 60 s ramps between. "
        "Total ~33 min, dt = 0.5 s. Expect the fan to saturate low during "
        "the 0 W holds — equilibrium CFM there is below V_min."
    ),
    "B-sharp — Ambient step ±6.5 °C": (
        "**Tests fast ambient disturbance rejection.** T_amb steps "
        "23.5 → 30 °C in 60 s, holds 15 min, returns. Constant 100 W laser. "
        "Total ~32 min, dt = 0.5 s."
    ),
    "B-slow — Ambient diurnal half-sine (6 h)": (
        "**Tests slow ambient drift (day/night cycle).** T_amb traces a "
        "smooth half-sine 23.5 → 30 → 23.5 °C over 6 hours. Constant "
        "100 W laser. dt = 5 s."
    ),
}

HELP_KP = (
    "Proportional gain (m³/s per °C). How aggressively the fan responds "
    "to instantaneous error. Higher Kp → faster response but risks "
    "overshoot and oscillation. Default = 5 CFM/K converted to SI."
)
HELP_KI = (
    "Integral gain (m³/s per °C·s). Drives steady-state offset to zero "
    "by accumulating past error. Conditional-integration anti-windup is "
    "enabled (skips integration when actuator is saturated). "
    "Default = 0.5 CFM/(K·s)."
)
HELP_KD = (
    "Derivative gain (m³/s per °C/s). Damps oscillation by reacting to "
    "the rate of change of temperature. Computed on the measurement "
    "(not the error) to avoid setpoint-change kicks. "
    "Default = 10 CFM·s/K."
)
HELP_TAU_FAN = (
    "First-order fan lag time constant. Actual CFM reaches ~63% of a "
    "commanded change in τ seconds, ~95% in 3τ. Models inertia of fan "
    "blades and motor. Default = 3 s."
)
HELP_T_SUPPLY = (
    "Air temperature leaving the chilled-water coil and entering the "
    "enclosure. Must be below the 23 °C setpoint or the system cannot "
    "cool (validation will reject). Default = 18 °C."
)
HELP_V_MIN = (
    "Lower clamp on fan speed — typically the HEPA filter pressure-drop "
    "floor or a minimum circulation requirement. When the controller "
    "wants less than this, the fan pins here and the loop is 'saturated "
    "low'. Default = 30 CFM."
)
HELP_V_MAX = (
    "Upper clamp on fan speed — typically the turbulence / optical-"
    "sensitivity ceiling. When the controller wants more, the fan pins "
    "here and the loop is 'saturated high' (T_inside drifts above "
    "setpoint). Default = 150 CFM."
)


def render_pid_experiment_panel(
    enclosure_thermal_capacitance_j_per_k: float,
    ua_value_w_per_k: float,
) -> None:
    """Render the PID experiment tab.

    The plant params are derived from the geometry/ambient panels in the
    Steady State tab so the user does not enter the same enclosure twice.
    """
    st.markdown(
        '<div class="section-header">PID EXPERIMENT</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "Closed-loop time-domain simulation. A PID controller modulates "
        "fan CFM to hold T_inside at the 23 °C setpoint against the "
        "chosen disturbance. Plant parameters (thermal mass, UA) come "
        "from the Geometry and Ambient panels in the Steady State tab — "
        "change them there to see how dynamics shift."
    )

    # ── Scenario picker ─────────────────────────────────────
    scenario_label = st.radio(
        "Disturbance scenario",
        options=list(SCENARIO_BUILDERS.keys()),
        index=0,
        horizontal=False,
        help=(
            "Each scenario stresses a different part of the loop: A "
            "exercises heat-load rejection, B-sharp tests fast ambient "
            "rejection, B-slow tests slow drift tracking."
        ),
    )
    st.caption(SCENARIO_DESCRIPTIONS[scenario_label])

    # ── Advanced controls ───────────────────────────────────
    with st.expander("Advanced controller and plant parameters", expanded=False):
        st.markdown(
            "**Controller gains** set how the PID loop responds to "
            "temperature error. **Plant parameters** set the physical "
            "limits of the fan and cooling coil. Hover the `?` next to "
            "each input for details."
        )
        c1, c2 = st.columns(2)
        with c1:
            kp = st.number_input(
                "PID Kp", value=default_pid_controller().kp,
                min_value=0.0, step=0.0001, format="%.4f",
                help=HELP_KP,
            )
            ki = st.number_input(
                "PID Ki", value=default_pid_controller().ki,
                min_value=0.0, step=0.0001, format="%.4f",
                help=HELP_KI,
            )
            kd = st.number_input(
                "PID Kd", value=default_pid_controller().kd,
                min_value=0.0, step=0.0001, format="%.4f",
                help=HELP_KD,
            )
        with c2:
            tau_fan = st.number_input(
                "Fan time constant τ_fan (s)",
                value=default_fan_params().tau_s,
                min_value=0.1, step=0.5, format="%.1f",
                help=HELP_TAU_FAN,
            )
            t_supply = st.number_input(
                "Coil supply temp T_supply (°C)",
                value=default_t_supply_c(),
                min_value=0.0, max_value=30.0, step=0.5,
                help=HELP_T_SUPPLY,
            )
            v_min_cfm = st.number_input(
                "Fan min CFM",
                value=m3s_to_cfm(default_fan_params().v_dot_min_m3s),
                min_value=0.0, step=5.0,
                help=HELP_V_MIN,
            )
            v_max_cfm = st.number_input(
                "Fan max CFM",
                value=m3s_to_cfm(default_fan_params().v_dot_max_m3s),
                min_value=1.0, step=10.0,
                help=HELP_V_MAX,
            )

    setpoint_c = default_t_setpoint_c()

    # ── Run button ──────────────────────────────────────────
    if st.button("Run experiment", type="primary"):
        scenario = SCENARIO_BUILDERS[scenario_label]()
        plant = PlantParams(
            thermal_capacitance_j_per_k=enclosure_thermal_capacitance_j_per_k,
            ua_value_w_per_k=ua_value_w_per_k,
            air_cp=AIR_CP,
            air_density=AIR_DENSITY,
            t_supply_c=t_supply,
        )
        fan = FanParams(
            tau_s=tau_fan,
            v_dot_min_m3s=cfm_to_m3s(v_min_cfm),
            v_dot_max_m3s=cfm_to_m3s(v_max_cfm),
        )
        pid = PIDController(
            kp=kp, ki=ki, kd=kd,
            setpoint=setpoint_c,
            v_min=cfm_to_m3s(v_min_cfm),
            v_max=cfm_to_m3s(v_max_cfm),
        )

        try:
            result = run_experiment(
                scenario=scenario,
                plant_params=plant,
                fan_params=fan,
                controller=pid,
                t_setpoint_c=setpoint_c,
            )
        except ValueError as e:
            st.error(f"Invalid inputs:\n{e}")
            return
        except RuntimeError as e:
            st.error(f"Simulation failed:\n{e}")
            return

        _render_result(result, fan, scenario.name)
    else:
        st.info("Configure parameters above (or accept defaults), then click Run.")


def _render_result(result: SimulationResult,
                   fan_params: FanParams,
                   scenario_name: str) -> None:
    summary = compute_summary(result)
    warnings = compute_experiment_warnings(result)

    if warnings:
        for w in warnings:
            st.warning(w)

    # ── Plot 1: temperatures ─────────────────────────────────
    fig_t = go.Figure()
    fig_t.add_trace(go.Scatter(
        x=result.t_s, y=result.t_inside_c, name="T_inside",
        line=dict(color="#00D4AA", width=2),
    ))
    fig_t.add_trace(go.Scatter(
        x=result.t_s, y=result.t_setpoint_c, name="T_setpoint",
        line=dict(color="#FF6B35", width=1, dash="dash"),
    ))
    fig_t.add_trace(go.Scatter(
        x=result.t_s, y=result.t_amb_c, name="T_ambient",
        line=dict(color="#7C8B9A", width=1),
    ))
    fig_t.update_layout(
        title="Temperatures (°C)",
        xaxis_title="time (s)", yaxis_title="°C",
        height=300, paper_bgcolor="#0D1117", plot_bgcolor="#0D1117",
        font=dict(color="#C9D1D9"),
    )
    st.plotly_chart(fig_t, use_container_width=True, theme=None)

    # ── Plot 2: fan CFM with limit bands ─────────────────────
    cmd_cfm = np.array([m3s_to_cfm(v) for v in result.v_dot_command_m3s])
    actual_cfm = np.array([m3s_to_cfm(v) for v in result.v_dot_actual_m3s])
    v_min_cfm = m3s_to_cfm(fan_params.v_dot_min_m3s)
    v_max_cfm = m3s_to_cfm(fan_params.v_dot_max_m3s)

    fig_v = go.Figure()
    # Shade outside the bands (above max and below min) so saturation is obvious
    y_top = max(cmd_cfm.max(), v_max_cfm) * 1.1
    y_bot = min(cmd_cfm.min(), v_min_cfm) * 0.9
    fig_v.add_hrect(y0=v_max_cfm, y1=y_top, fillcolor="#F0A830", opacity=0.10,
                    line_width=0)
    fig_v.add_hrect(y0=y_bot, y1=v_min_cfm, fillcolor="#F0A830", opacity=0.10,
                    line_width=0)
    fig_v.add_hline(y=v_max_cfm, line_dash="dash", line_color="#7C8B9A",
                    annotation_text="V_max")
    fig_v.add_hline(y=v_min_cfm, line_dash="dash", line_color="#7C8B9A",
                    annotation_text="V_min")
    fig_v.add_trace(go.Scatter(
        x=result.t_s, y=cmd_cfm, name="V_command",
        line=dict(color="#58A6FF", width=2),
    ))
    fig_v.add_trace(go.Scatter(
        x=result.t_s, y=actual_cfm, name="V_actual",
        line=dict(color="#00D4AA", width=1, dash="dot"),
    ))
    fig_v.update_layout(
        title="Fan airflow (CFM)",
        xaxis_title="time (s)", yaxis_title="CFM",
        height=300, paper_bgcolor="#0D1117", plot_bgcolor="#0D1117",
        font=dict(color="#C9D1D9"),
    )
    st.plotly_chart(fig_v, use_container_width=True, theme=None)

    # ── Plot 3: heat balance ─────────────────────────────────
    fig_q = go.Figure()
    fig_q.add_trace(go.Scatter(
        x=result.t_s, y=result.q_load_w, name="Q_load",
        line=dict(color="#F85149", width=2),
    ))
    fig_q.add_trace(go.Scatter(
        x=result.t_s, y=result.q_cool_w, name="Q_cool",
        line=dict(color="#58A6FF", width=2),
    ))
    fig_q.update_layout(
        title="Heat load vs cooling power (W)",
        xaxis_title="time (s)", yaxis_title="W",
        height=300, paper_bgcolor="#0D1117", plot_bgcolor="#0D1117",
        font=dict(color="#C9D1D9"),
    )
    st.plotly_chart(fig_q, use_container_width=True, theme=None)

    # ── Summary stats ────────────────────────────────────────
    st.markdown("### Summary statistics")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Peak CFM", f"{summary['peak_cfm']:.1f}")
        st.metric("Mean CFM", f"{summary['mean_cfm']:.1f}")
        st.metric("RMS CFM", f"{summary['rms_cfm']:.1f}")
    with c2:
        st.metric("Min commanded CFM", f"{summary['min_commanded_cfm']:.1f}")
        st.metric("Max |T_inside − SP|", f"{summary['max_excursion_c']:.2f} °C")
    with c3:
        if summary["settling_time_s"] == float("inf"):
            st.metric("Settle time (±0.5 °C)", "∞")
        else:
            st.metric("Settle time (±0.5 °C)", f"{summary['settling_time_s']:.0f} s")
        st.metric("Saturation %", f"{summary['saturation_pct']:.1f}%")

    # ── CSV download ─────────────────────────────────────────
    csv_buf = io.StringIO()
    csv_buf.write(
        "t_s,t_inside_c,t_setpoint_c,t_amb_c,q_load_w,q_cool_w,"
        "v_dot_command_cfm,v_dot_actual_cfm,saturated\n"
    )
    for i in range(len(result.t_s)):
        csv_buf.write(
            f"{result.t_s[i]:.4f},"
            f"{result.t_inside_c[i]:.6f},"
            f"{result.t_setpoint_c[i]:.6f},"
            f"{result.t_amb_c[i]:.6f},"
            f"{result.q_load_w[i]:.4f},"
            f"{result.q_cool_w[i]:.4f},"
            f"{m3s_to_cfm(result.v_dot_command_m3s[i]):.4f},"
            f"{m3s_to_cfm(result.v_dot_actual_m3s[i]):.4f},"
            f"{int(result.saturated[i])}\n"
        )
    st.download_button(
        label="⬇ Download CSV",
        data=csv_buf.getvalue(),
        file_name=f"experiment_{scenario_name}_"
                  f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )
