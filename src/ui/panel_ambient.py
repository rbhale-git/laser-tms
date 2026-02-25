"""Panel 3: Ambient temperature and coupling inputs."""
import streamlit as st


def render_ambient_panel() -> dict:
    """Render ambient condition inputs and return values in SI.

    Returns dict with keys: temperature_c, variation_amplitude_c,
    variation_period_hr, ua_value.
    """
    with st.expander("AMBIENT CONDITIONS", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            temp = st.number_input(
                "Ambient temperature (°C)",
                value=23.5,
                min_value=-10.0,
                max_value=50.0,
                step=0.5,
            )
        with c2:
            variation = st.number_input(
                "Variation amplitude (±°C)",
                value=2.0,
                min_value=0.0,
                max_value=10.0,
                step=0.5,
                help="Peak amplitude of ambient temperature swing",
            )

        ua_mode = st.radio(
            "Ambient coupling input mode",
            ["Direct UA (W/K)", "Air changes per hour (ACH)"],
            horizontal=True,
        )

        if ua_mode == "Direct UA (W/K)":
            ua = st.number_input(
                "UA value (W/K)",
                value=2.0,
                min_value=0.0,
                step=0.5,
                help="Conduction + infiltration coupling to ambient",
            )
        else:
            ach = st.number_input(
                "Air changes per hour",
                value=0.5,
                min_value=0.0,
                step=0.1,
                help="Infiltration rate; converted to UA internally",
            )
            st.caption("Note: UA computed using enclosure volume from Panel 1")
            ua = ach  # Will be converted in app.py using actual volume

    return {
        "temperature_c": temp,
        "variation_amplitude_c": variation,
        "variation_period_hr": 24.0,
        "ua_value": ua,
        "ua_mode": ua_mode,
    }
