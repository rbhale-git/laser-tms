"""Lumped-capacitance plant ODE for the enclosure thermal simulation.

  C_e · dT_inside/dt = Q_load(t) - Q_cool(t) + UA·(T_amb(t) - T_inside)

where Q_cool(t) = ρ · V_dot(t) · c_p · (T_inside - T_supply).

Q_cool can go negative if T_inside < T_supply (the supply air heats a
too-cold enclosure); this is physically correct and is left unclamped.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PlantParams:
    thermal_capacitance_j_per_k: float
    ua_value_w_per_k: float
    air_cp: float
    air_density: float
    t_supply_c: float


def dT_inside_dt(
    t_inside_c: float,
    v_dot_m3s: float,
    q_load_w: float,
    t_amb_c: float,
    params: PlantParams,
) -> float:
    """Time derivative of T_inside in K/s.

    All inputs in SI. Caller is responsible for evaluating Q_load(t) and
    T_amb(t) at the appropriate sub-step time when used inside RK4.
    """
    m_dot = params.air_density * v_dot_m3s
    q_cool = m_dot * params.air_cp * (t_inside_c - params.t_supply_c)
    q_amb = params.ua_value_w_per_k * (t_amb_c - t_inside_c)
    return (q_load_w - q_cool + q_amb) / params.thermal_capacitance_j_per_k
