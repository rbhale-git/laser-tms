"""Panel 3: Enclosure setpoint and ambient environment inputs."""
import streamlit as st


def render_ambient_panel() -> dict:
    """Render setpoint and ambient inputs, return values in SI.

    Returns dict with keys: T_setpoint_c, T_ambient_c, T_ambient_variation_c,
    ua_value, ua_mode.
    """
    # ── Group 1: Enclosure Setpoint (Regulated) ──────────
    with st.expander("ENCLOSURE SETPOINT", expanded=True):
        setpoint = st.number_input(
            "Setpoint temperature (°C)",
            value=23.0,
            min_value=10.0,
            max_value=40.0,
            step=0.5,
        )
        setpoint_f = setpoint * 9.0 / 5.0 + 32.0
        st.caption(f"{setpoint_f:.1f} °F")
        st.markdown(
            '<span class="eq-assume" style="font-size:0.78em">'
            "The temperature the cooling system actively maintains "
            "inside the enclosure (\u00b10.1 \u00b0C). Set this to match the "
            "average ambient so opening the lid causes minimal disturbance."
            "</span>",
            unsafe_allow_html=True,
        )

    # ── Group 2: Ambient Environment (Unregulated) ───────
    with st.expander("AMBIENT ENVIRONMENT", expanded=True):
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
                value=5.5,
                min_value=0.0,
                max_value=10.0,
                step=0.5,
                help="Peak amplitude of ambient temperature swing",
            )

        t_low = temp - variation
        t_high = temp + variation
        t_low_f = t_low * 9.0 / 5.0 + 32.0
        t_high_f = t_high * 9.0 / 5.0 + 32.0
        temp_f = temp * 9.0 / 5.0 + 32.0
        st.caption(f"{temp_f:.1f} °F")
        st.markdown(
            f"**Ambient range:** {t_low:.1f} °C to {t_high:.1f} °C "
            f"({t_low_f:.1f} °F to {t_high_f:.1f} °F)"
        )
        st.markdown(
            '<span class="eq-assume" style="font-size:0.78em">'
            "The surrounding lab temperature. This is a disturbance the "
            "system must counteract — it is not controlled."
            "</span>",
            unsafe_allow_html=True,
        )

        # ── UA coupling input ────────────────────────────
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
            st.markdown(
                '<span class="eq-assume" style="font-size:0.78em">'
                "Overall heat transfer coefficient between the enclosure "
                "and the lab. Combines conduction through walls, seals, "
                "and air infiltration into a single number. "
                "A higher UA means the enclosure is more thermally coupled "
                "to the room — harder to hold setpoint when ambient drifts. "
                "Typical range: 1\u20135 W/K for a well-insulated enclosure."
                "</span>",
                unsafe_allow_html=True,
            )
        else:
            ach = st.number_input(
                "Air changes per hour",
                value=0.5,
                min_value=0.0,
                step=0.1,
                help="Infiltration rate; converted to UA internally",
            )
            st.markdown(
                '<span class="eq-assume" style="font-size:0.78em">'
                "How many times per hour the enclosure air volume is "
                "replaced by outside lab air through leaks, seals, and "
                "cable pass-throughs. Converted to an equivalent UA value "
                "using the enclosure volume. "
                "Typical range: 0.1\u20131.0 ACH for a sealed enclosure."
                "</span>",
                unsafe_allow_html=True,
            )
            st.caption("Note: UA computed using enclosure volume from Panel 1")
            ua = ach  # Will be converted in app.py using actual volume

    return {
        "T_setpoint_c": setpoint,
        "T_ambient_c": temp,
        "T_ambient_variation_c": variation,
        "ua_value": ua,
        "ua_mode": ua_mode,
    }
