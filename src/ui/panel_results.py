"""Panel 6: Computed results display with metric cards and warnings."""
import streamlit as st
from src.models import SolveMode
from src.units import m3s_to_cfm, kgs_to_lpm, lpm_to_gpm


def render_results_panel(
    airflow_m3s: float,
    coolant_kgs: float,
    coil_utilization_pct: float,
    heater_required_w: float,
    coil_leaving_temp_c: float,
    warnings: list[str],
    solve_mode: SolveMode = SolveMode.AIRFLOW,
) -> None:
    """Render computed results as metric cards with dual-unit display.

    The card corresponding to the active solve_mode is highlighted in orange.
    """
    st.markdown(
        '<div class="section-header">COMPUTED RESULTS</div>',
        unsafe_allow_html=True,
    )

    cfm = m3s_to_cfm(airflow_m3s)
    lpm = kgs_to_lpm(coolant_kgs)
    gpm = lpm_to_gpm(lpm)

    # Determine which card to highlight
    highlight_airflow = solve_mode == SolveMode.AIRFLOW
    highlight_coolant = solve_mode == SolveMode.COOLANT
    highlight_coil = solve_mode == SolveMode.COIL_TEMP
    highlight_heater = solve_mode == SolveMode.HEATER

    # Top row: 2 metrics
    r1c1, r1c2 = st.columns(2)

    with r1c1:
        css_class = "metric-solving" if highlight_airflow else ""
        st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
        st.metric(
            label="REQUIRED AIRFLOW",
            value=f"{cfm:.1f} CFM",
            delta=f"{airflow_m3s:.4f} m\u00b3/s",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with r1c2:
        css_class = "metric-solving" if highlight_coolant else ""
        st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
        st.metric(
            label="COOLANT FLOW",
            value=f"{lpm:.2f} L/min",
            delta=f"{gpm:.3f} GPM",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Bottom row: 2 metrics
    r2c1, r2c2 = st.columns(2)

    with r2c1:
        # Coil utilization with color-coded wrapper
        # Solving highlight takes priority, otherwise error/warning state
        if highlight_coil:
            wrapper_class = "metric-solving"
        elif coil_utilization_pct > 100:
            wrapper_class = "metric-error"
        elif coil_utilization_pct > 90:
            wrapper_class = "metric-warning"
        else:
            wrapper_class = ""

        st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)
        st.metric(
            label="COIL UTILIZATION",
            value=f"{coil_utilization_pct:.0f}%",
            delta=(
                f"of {coil_utilization_pct / 100 * 500:.0f} W capacity"
                if coil_utilization_pct <= 100
                else "OVER CAPACITY"
            ),
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # Utilization bar
        if highlight_coil:
            bar_color = "#FF6B35"
        elif coil_utilization_pct > 100:
            bar_color = "#F85149"
        elif coil_utilization_pct > 90:
            bar_color = "#F0A830"
        else:
            bar_color = "#00D4AA"
        bar_width = min(coil_utilization_pct, 100)
        st.markdown(
            f'<div class="util-bar-track">'
            f'<div class="util-bar-fill" style="background:{bar_color};width:{bar_width}%"></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with r2c2:
        css_class = "metric-solving" if highlight_heater else ""
        st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
        st.metric(
            label="HEATER REQUIRED",
            value=f"{heater_required_w:.1f} W",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Coil leaving temp as a subtle readout
    st.markdown(
        f'<div style="margin-top:0.4rem">'
        f'<span class="unit-label">Coil leaving air temp: {coil_leaving_temp_c:.1f} \u00b0C</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Warnings
    if warnings:
        for w in warnings:
            if "SATURATED" in w.upper():
                st.error(w)
            elif "heater" in w.lower():
                st.info(w)
            else:
                st.warning(w)
