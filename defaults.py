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
        coil_approach_temp_c=2.0,
        coil_max_capacity_w=500.0,
        chilled_water_temp_c=15.0,
        delta_t_air_c=5.0,
        delta_t_water_c=2.0,
    )


def default_ambient() -> AmbientConditions:
    return AmbientConditions(
        T_ambient_c=23.5,
        T_setpoint_c=23.0,
        T_ambient_variation_c=5.5,
        ua_value=2.0,
    )


from src.constants import AIR_CP, AIR_DENSITY
from src.sim.actuator import FanParams
from src.sim.controller import PIDController
from src.sim.plant import PlantParams
from src.units import cfm_to_m3s


def default_t_setpoint_c() -> float:
    return 23.0


def default_t_supply_c() -> float:
    """Constant heat-exchanger coil leaving temperature."""
    return 18.0


def default_plant_params() -> PlantParams:
    enc = default_enclosure()
    amb = default_ambient()
    return PlantParams(
        thermal_capacitance_j_per_k=enc.thermal_capacitance,
        ua_value_w_per_k=amb.ua_value,
        air_cp=AIR_CP,
        air_density=AIR_DENSITY,
        t_supply_c=default_t_supply_c(),
    )


def default_fan_params() -> FanParams:
    return FanParams(
        tau_s=3.0,
        v_dot_min_m3s=cfm_to_m3s(30.0),    # HEPA filter floor
        v_dot_max_m3s=cfm_to_m3s(150.0),   # below optical-sensitivity ceiling
    )


def default_pid_controller() -> PIDController:
    """Spec-derived gains: 5 CFM/K, 0.5 CFM/(K·s), 10 CFM·s/K — converted to SI.
    Placeholders, will likely be retuned after observing first full runs."""
    return PIDController(
        kp=cfm_to_m3s(5.0),     # 5 CFM/K
        ki=cfm_to_m3s(0.5),     # 0.5 CFM/(K·s)
        kd=cfm_to_m3s(10.0),    # 10 CFM·s/K (numerically same factor)
        setpoint=default_t_setpoint_c(),
        v_min=cfm_to_m3s(30.0),
        v_max=cfm_to_m3s(150.0),
    )
