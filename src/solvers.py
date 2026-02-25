"""Steady-state thermal solvers for enclosure sizing.

All functions are pure — no UI dependency. Take SI values, return SI values.
Unit conversion is the caller's responsibility.

Physics reference:
  Airflow:  m_dot = Q / (c_p * ΔT_air)
  Coolant:  m_dot = Q / (c_p_water * ΔT_water)
  Coil temp: T_out = T_return - Q / (m_dot * c_p)
  Heater:   needed when UA*(T_set - T_amb) > Q_load
"""
from __future__ import annotations
from dataclasses import dataclass, field

from src.constants import AIR_CP, AIR_DENSITY, WATER_CP


@dataclass
class SolverResult:
    """Container for all solver outputs."""
    airflow_m3s: float = 0.0
    airflow_kgs: float = 0.0
    coolant_kgs: float = 0.0
    coil_leaving_temp_c: float = 0.0
    heater_required_w: float = 0.0
    coil_utilization_pct: float = 0.0
    warnings: list[str] = field(default_factory=list)


def solve_airflow(
    q_total_w: float,
    delta_t_air_c: float,
    air_cp: float = AIR_CP,
    air_density: float = AIR_DENSITY,
) -> SolverResult:
    """Solve required airflow to remove heat load.

    m_dot_air = Q / (c_p * ΔT_air)
    V_dot_air = m_dot_air / ρ
    """
    if delta_t_air_c == 0:
        raise ValueError("ΔT_air cannot be zero")
    m_dot = q_total_w / (air_cp * delta_t_air_c)
    v_dot = m_dot / air_density
    return SolverResult(airflow_m3s=v_dot, airflow_kgs=m_dot)


def solve_coolant_flow(
    q_total_w: float,
    delta_t_water_c: float,
    water_cp: float = WATER_CP,
) -> SolverResult:
    """Solve required coolant mass flow.

    m_dot_water = Q / (c_p_water * ΔT_water)
    """
    if delta_t_water_c == 0:
        raise ValueError("ΔT_water cannot be zero")
    m_dot = q_total_w / (water_cp * delta_t_water_c)
    return SolverResult(coolant_kgs=m_dot)


def solve_coil_leaving_temp(
    q_total_w: float,
    airflow_kgs: float,
    return_air_temp_c: float,
    air_cp: float = AIR_CP,
) -> SolverResult:
    """Solve coil leaving air temperature.

    T_coil_out = T_return - Q / (m_dot_air * c_p)
    """
    if airflow_kgs == 0:
        raise ValueError("Airflow mass rate cannot be zero")
    delta_t = q_total_w / (airflow_kgs * air_cp)
    t_out = return_air_temp_c - delta_t
    return SolverResult(coil_leaving_temp_c=t_out)


def solve_heater_requirement(
    q_load_w: float,
    ua_value: float,
    ambient_temp_c: float,
    setpoint_c: float,
) -> SolverResult:
    """Solve heater power needed when ambient cools enclosure below setpoint.

    Heat loss to ambient = UA * (T_setpoint - T_ambient)  [when T_set > T_amb]
    Net cooling surplus = heat_loss - Q_load
    If positive, heater is needed to compensate.
    """
    heat_loss_w = ua_value * (setpoint_c - ambient_temp_c)
    net_deficit = heat_loss_w - q_load_w
    heater_w = max(0.0, net_deficit)
    return SolverResult(heater_required_w=heater_w)


def compute_warnings(
    coil_utilization_pct: float,
    heater_required_w: float,
) -> list[str]:
    """Generate warning messages based on solver results."""
    warnings = []
    if coil_utilization_pct > 100.0:
        warnings.append(
            f"COOLING SATURATED: Coil utilization at {coil_utilization_pct:.0f}%. "
            "Increase coil capacity or reduce heat load."
        )
    elif coil_utilization_pct > 90.0:
        warnings.append(
            f"High coil utilization: {coil_utilization_pct:.0f}%. "
            "Limited cooling margin remaining."
        )
    if heater_required_w > 0.0:
        warnings.append(
            f"Heater required: {heater_required_w:.1f} W to maintain setpoint "
            "under current ambient conditions."
        )
    return warnings
