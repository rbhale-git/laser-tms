"""Panel 1: Enclosure geometry and thermal mass inputs."""
import streamlit as st
from src.units import ft_to_m, m_to_ft, ft3_to_m3, m3_to_ft3


def render_geometry_panel(use_imperial: bool) -> dict:
    """Render geometry inputs and return values in SI.

    Returns dict with keys: length_m, width_m, height_m, internal_thermal_mass.
    """
    with st.expander("GEOMETRY & PROPERTIES", expanded=True):
        if use_imperial:
            c1, c2, c3 = st.columns(3)
            with c1:
                length = st.number_input("Length (ft)", value=4.0, min_value=0.1, step=0.5)
            with c2:
                width = st.number_input("Width (ft)", value=10.0, min_value=0.1, step=0.5)
            with c3:
                height = st.number_input("Height (ft)", value=2.5, min_value=0.1, step=0.5)
            length_m = ft_to_m(length)
            width_m = ft_to_m(width)
            height_m = ft_to_m(height)
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                length_m = st.number_input("Length (m)", value=1.22, min_value=0.01, step=0.1, format="%.2f")
            with c2:
                width_m = st.number_input("Width (m)", value=3.05, min_value=0.01, step=0.1, format="%.2f")
            with c3:
                height_m = st.number_input("Height (m)", value=0.76, min_value=0.01, step=0.1, format="%.2f")

        volume_m3 = length_m * width_m * height_m

        vol_col1, vol_col2 = st.columns(2)
        with vol_col1:
            st.markdown(f"**Volume:** `{volume_m3:.3f}` m³")
        with vol_col2:
            st.markdown(f'<span class="unit-label">{m3_to_ft3(volume_m3):.1f} ft³</span>', unsafe_allow_html=True)

        internal_mass = st.slider(
            "Internal thermal mass (kJ/K)",
            min_value=0.0,
            max_value=200.0,
            value=50.0,
            step=5.0,
            help="Thermal mass of hardware inside enclosure (laser, optics, mounts)",
        )

    return {
        "length_m": length_m,
        "width_m": width_m,
        "height_m": height_m,
        "internal_thermal_mass": internal_mass * 1000.0,  # kJ → J
    }
