"""Panel 2: Internal heat load inputs."""
import streamlit as st


def render_loads_panel() -> dict:
    """Render heat load inputs and return values in watts.

    Returns dict with keys: baseline_load_w, additional_loads_w.
    """
    with st.expander("HEAT LOADS", expanded=True):
        baseline = st.number_input(
            "Baseline load (W)",
            value=100.0,
            min_value=0.0,
            step=10.0,
            help="Primary heat source (e.g., laser system)",
        )
        additional = st.number_input(
            "Additional loads (W)",
            value=0.0,
            min_value=0.0,
            step=5.0,
            help="Sum of secondary heat sources (electronics, pumps, etc.)",
        )
        total = baseline + additional
        st.markdown(f"**Total load:** `{total:.1f}` W")

    return {
        "baseline_load_w": baseline,
        "additional_loads_w": additional,
    }
