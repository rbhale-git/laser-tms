"""Preloaded default case: 100W laser in 4x10x2.5 ft enclosure.

Reference: Engineering Specification Section 7.
Expected steady-state outputs:
  - ΔT_air ≈ 5°C → required airflow ≈ 35-40 CFM
  - ΔT_water = 2°C → coolant ≈ 0.7 L/min
"""
from src.models import (
    Enclosure,
    HeatLoads,
    CoolingPlant,
    AmbientConditions,
    CoolingType,
)
from src.units import ft_to_m


def default_enclosure() -> Enclosure:
    return Enclosure(
        length_m=ft_to_m(4.0),
        width_m=ft_to_m(10.0),
        height_m=ft_to_m(2.5),
        internal_thermal_mass=50_000.0,  # 50 kJ/K
    )


def default_heat_loads() -> HeatLoads:
    return HeatLoads(baseline_load_w=100.0, additional_loads_w=0.0)


def default_cooling_plant() -> CoolingPlant:
    return CoolingPlant(
        cooling_type=CoolingType.AIR_COIL,
        coil_approach_temp_c=2.0,
        coil_max_capacity_w=500.0,
        chilled_water_temp_c=15.0,
        delta_t_air_c=5.0,
        delta_t_water_c=2.0,
    )


def default_ambient() -> AmbientConditions:
    return AmbientConditions(
        temperature_c=23.5,
        variation_amplitude_c=2.0,
        variation_period_hr=24.0,
        ua_value=2.0,
    )
