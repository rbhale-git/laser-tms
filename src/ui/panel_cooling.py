"""Panel 4: Cooling plant configuration inputs."""
import streamlit as st
from src.models import CoolingType, SolveMode


def render_cooling_panel(solve_mode: SolveMode) -> dict:
    """Render cooling plant inputs. Some fields are disabled based on solve mode.

    Returns dict with keys matching CoolingPlant fields.
    """
    with st.expander("COOLING PLANT", expanded=True):
        cooling_type = st.selectbox(
            "Cooling type",
            options=[ct.value for ct in CoolingType],
            format_func=lambda x: {
                "air_coil": "Air Coil",
                "liquid": "Liquid",
                "hybrid": "Hybrid",
            }[x],
        )

        c1, c2 = st.columns(2)
        with c1:
            approach = st.number_input(
                "Coil approach temp (\u00b0C)",
                value=2.0,
                min_value=0.1,
                step=0.5,
                help="Minimum temperature difference between coolant and air at coil exit",
            )
        with c2:
            max_cap = st.number_input(
                "Coil max capacity (W)",
                value=500.0,
                min_value=10.0,
                step=50.0,
                help="Maximum cooling power of the heat exchanger",
            )

        c3, c4 = st.columns(2)
        with c3:
            chilled_water_temp = st.number_input(
                "Chilled water supply (\u00b0C)",
                value=15.0,
                min_value=0.0,
                max_value=30.0,
                step=1.0,
            )
        with c4:
            solving_coolant = solve_mode == SolveMode.COOLANT
            label = "Coolant \u0394T (\u00b0C)"
            if solving_coolant:
                st.markdown(
                    f'{label} <span class="solved-badge">SOLVING</span>',
                    unsafe_allow_html=True,
                )
            delta_t_water = st.number_input(
                label,
                value=2.0,
                min_value=0.1,
                step=0.5,
                disabled=solving_coolant,
                label_visibility="collapsed" if solving_coolant else "visible",
            )

        solving_airflow = solve_mode == SolveMode.AIRFLOW
        label_air = "Air-side \u0394T (\u00b0C)"
        if solving_airflow:
            st.markdown(
                f'{label_air} <span class="solved-badge">SOLVING</span>',
                unsafe_allow_html=True,
            )
        delta_t_air = st.number_input(
            label_air,
            value=5.0,
            min_value=0.1,
            step=0.5,
            disabled=solving_airflow,
            label_visibility="collapsed" if solving_airflow else "visible",
        )

    return {
        "cooling_type": cooling_type,
        "coil_approach_temp_c": approach,
        "coil_max_capacity_w": max_cap,
        "chilled_water_temp_c": chilled_water_temp,
        "delta_t_air_c": delta_t_air,
        "delta_t_water_c": delta_t_water,
    }
