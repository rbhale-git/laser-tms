"""PID experiment harness: validation, time-domain simulation, summary stats.

This module is the only one the UI panel calls to run an experiment.
Tasks 8 and 9 extend it with run_experiment, compute_summary, and
compute_experiment_warnings.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

from src.sim.actuator import FanParams
from src.sim.controller import PIDController
from src.sim.plant import PlantParams
from src.sim.scenarios import Scenario


@dataclass
class SimulationResult:
    t_s: np.ndarray
    t_inside_c: np.ndarray
    t_setpoint_c: np.ndarray   # constant array, kept for plotting convenience
    t_amb_c: np.ndarray
    q_load_w: np.ndarray
    q_cool_w: np.ndarray
    v_dot_command_m3s: np.ndarray
    v_dot_actual_m3s: np.ndarray
    saturated: np.ndarray      # bool


def validate_experiment_inputs(
    plant_params: PlantParams,
    fan_params: FanParams,
    controller: PIDController,
    scenario: Scenario,
    t_setpoint_c: float,
) -> None:
    """Raise ValueError on any invalid input. The UI panel catches these
    and renders a single error box."""
    errors: list[str] = []

    if plant_params.t_supply_c >= t_setpoint_c:
        errors.append(
            f"Coil supply temp ({plant_params.t_supply_c} °C) must be below "
            f"setpoint ({t_setpoint_c} °C) — cannot cool."
        )
    if fan_params.v_dot_max_m3s <= fan_params.v_dot_min_m3s:
        errors.append(
            f"Fan max ({fan_params.v_dot_max_m3s} m³/s) must exceed "
            f"min ({fan_params.v_dot_min_m3s} m³/s)."
        )
    if fan_params.v_dot_min_m3s < 0.0:
        errors.append("Fan min CFM cannot be negative.")
    if fan_params.tau_s <= 0.0:
        errors.append("Fan time constant must be positive.")
    if controller.kp < 0.0 or controller.ki < 0.0 or controller.kd < 0.0:
        errors.append(
            f"PID gains must be non-negative "
            f"(kp={controller.kp}, ki={controller.ki}, kd={controller.kd})."
        )
    if plant_params.thermal_capacitance_j_per_k <= 0.0:
        errors.append("Thermal capacitance must be positive.")
    if plant_params.ua_value_w_per_k < 0.0:
        errors.append("UA value cannot be negative.")
    if scenario.timestep_s <= 0.0 or scenario.duration_s <= 0.0:
        errors.append("Scenario timestep and duration must be positive.")
    if scenario.timestep_s > scenario.duration_s:
        errors.append(
            f"Scenario timestep ({scenario.timestep_s}) must be smaller "
            f"than duration ({scenario.duration_s})."
        )

    if errors:
        raise ValueError("\n".join(errors))
