"""Panel 6: Computed results display with metric cards and warnings."""
import streamlit as st
from src.units import m3s_to_cfm, kgs_to_lpm, lpm_to_gpm


def render_results_panel(
    airflow_m3s: float,
    coolant_kgs: float,
    coil_utilization_pct: float,
    heater_required_w: float,
    coil_leaving_temp_c: float,
    warnings: list[str],
) -> None:
    """Render computed results as metric cards with dual-unit display."""
    st.markdown(
        '<div class="section-header">COMPUTED RESULTS</div>',
        unsafe_allow_html=True,
    )

    cfm = m3s_to_cfm(airflow_m3s)
    lpm = kgs_to_lpm(coolant_kgs)
    gpm = lpm_to_gpm(lpm)

    # Top row: 2 metrics
    r1c1, r1c2 = st.columns(2)

    with r1c1:
        st.metric(
            label="REQUIRED AIRFLOW",
            value=f"{cfm:.1f} CFM",
            delta=f"{airflow_m3s:.4f} m\u00b3/s",
        )

    with r1c2:
        st.metric(
            label="COOLANT FLOW",
            value=f"{lpm:.2f} L/min",
            delta=f"{gpm:.3f} GPM",
        )

    # Bottom row: 2 metrics
    r2c1, r2c2 = st.columns(2)

    with r2c1:
        # Coil utilization with color-coded wrapper
        if coil_utilization_pct > 100:
            st.markdown('<div class="metric-error">', unsafe_allow_html=True)
        elif coil_utilization_pct > 90:
            st.markdown('<div class="metric-warning">', unsafe_allow_html=True)
        else:
            st.markdown("<div>", unsafe_allow_html=True)
        st.metric(
            label="COIL UTILIZATION",
            value=f"{coil_utilization_pct:.0f}%",
            delta=f"of {coil_utilization_pct / 100 * 500:.0f} W capacity" if coil_utilization_pct <= 100 else "OVER CAPACITY",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # Utilization bar
        bar_color = "#00D4AA"
        if coil_utilization_pct > 100:
            bar_color = "#F85149"
        elif coil_utilization_pct > 90:
            bar_color = "#F0A830"
        bar_width = min(coil_utilization_pct, 100)
        st.markdown(
            f'<div class="util-bar-track">'
            f'<div class="util-bar-fill" style="background:{bar_color};width:{bar_width}%"></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with r2c2:
        st.metric(
            label="HEATER REQUIRED",
            value=f"{heater_required_w:.1f} W",
        )

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
