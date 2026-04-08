"""Fan actuator: first-order lag toward command, then physical clamp.

  V_actual(t+dt) = V_actual(t) + (V_command - V_actual(t)) * (1 - exp(-dt/tau))
  V_actual ∈ [V_min, V_max]
"""
from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class FanParams:
    tau_s: float
    v_dot_min_m3s: float
    v_dot_max_m3s: float


def fan_step(
    v_actual_m3s: float,
    v_command_m3s: float,
    dt_s: float,
    params: FanParams,
) -> float:
    """One actuator tick. Pure function."""
    if dt_s <= 0.0:
        return v_actual_m3s
    response = 1.0 - math.exp(-dt_s / params.tau_s)
    v_new = v_actual_m3s + (v_command_m3s - v_actual_m3s) * response
    return max(params.v_dot_min_m3s, min(params.v_dot_max_m3s, v_new))
