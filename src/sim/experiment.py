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


from src.sim.actuator import fan_step
from src.sim.integrator import rk4_step
from src.sim.plant import dT_inside_dt


def _initial_steady_state_v_dot(
    q_load_w: float,
    t_amb_c: float,
    t_setpoint_c: float,
    plant: PlantParams,
) -> float:
    """Closed-form steady-state CFM at T_inside = T_setpoint:
        Q_load + UA·(T_amb - T_setpoint)
        = ρ · V · cp · (T_setpoint - T_supply)
    """
    numerator = q_load_w + plant.ua_value_w_per_k * (t_amb_c - t_setpoint_c)
    denominator = (
        plant.air_density * plant.air_cp * (t_setpoint_c - plant.t_supply_c)
    )
    return numerator / denominator


def run_experiment(
    scenario: Scenario,
    plant_params: PlantParams,
    fan_params: FanParams,
    controller: PIDController,
    t_setpoint_c: float,
) -> SimulationResult:
    """Integrate the closed-loop system for scenario.duration_s and return
    arrays of every state variable.

    Initialization:
      - Compute the steady-state CFM for scenario.t=0 conditions.
      - Clamp to [v_min, v_max] (a warning will fire later if it had to clamp).
      - T_inside starts at t_setpoint_c (assume system was at equilibrium).
      - controller.initialize(V_init) for bumpless start.

    Loop (zero-order hold on V_actual inside RK4):
      1. Look up scenario(t).
      2. measurement = T_inside (ideal sensor).
      3. V_command = controller.step(measurement, dt).
      4. V_actual = fan_step(V_actual, V_command, dt, fan_params).
      5. T_inside = rk4_step(plant_ode_with_v_actual_held, T_inside, t, dt).
      6. Record sample.
    """
    validate_experiment_inputs(
        plant_params=plant_params, fan_params=fan_params,
        controller=controller, scenario=scenario, t_setpoint_c=t_setpoint_c,
    )

    dt = scenario.timestep_s
    n_steps = int(scenario.duration_s / dt)

    # Initialization
    q_load_init = scenario.q_load_at(0.0)
    t_amb_init = scenario.t_amb_at(0.0)
    v_init = _initial_steady_state_v_dot(
        q_load_w=q_load_init, t_amb_c=t_amb_init,
        t_setpoint_c=t_setpoint_c, plant=plant_params,
    )
    v_init = max(fan_params.v_dot_min_m3s, min(fan_params.v_dot_max_m3s, v_init))

    t_inside = t_setpoint_c
    v_actual = v_init
    controller.initialize(v_init)

    # Output buffers
    out_t = np.zeros(n_steps)
    out_t_inside = np.zeros(n_steps)
    out_t_setpoint = np.full(n_steps, t_setpoint_c)
    out_t_amb = np.zeros(n_steps)
    out_q_load = np.zeros(n_steps)
    out_q_cool = np.zeros(n_steps)
    out_v_command = np.zeros(n_steps)
    out_v_actual = np.zeros(n_steps)
    out_saturated = np.zeros(n_steps, dtype=bool)

    for i in range(n_steps):
        t = i * dt
        q_load = scenario.q_load_at(t)
        t_amb = scenario.t_amb_at(t)

        measurement = t_inside
        # Controller returns UNCLAMPED command; harness applies the clamp
        # for the actuator and detects saturation from the unclamped value.
        v_command_unclamped = controller.step(measurement, dt)
        v_command_for_actuator = max(
            fan_params.v_dot_min_m3s,
            min(fan_params.v_dot_max_m3s, v_command_unclamped),
        )
        v_actual = fan_step(v_actual, v_command_for_actuator, dt, fan_params)

        # Plant ODE with V_actual held constant across the four RK4 sub-steps
        v_actual_held = v_actual

        def _plant_ode(t_sub: float, T: float) -> float:
            return dT_inside_dt(
                t_inside_c=T,
                v_dot_m3s=v_actual_held,
                q_load_w=scenario.q_load_at(t_sub),
                t_amb_c=scenario.t_amb_at(t_sub),
                params=plant_params,
            )

        t_inside = rk4_step(_plant_ode, t_inside, t, dt)

        if not np.isfinite(t_inside):
            raise RuntimeError(
                f"Plant integration produced non-finite value at t={t:.1f}s."
            )

        # Compute Q_cool with the post-update T_inside (matches what we record)
        q_cool = (
            plant_params.air_density
            * v_actual
            * plant_params.air_cp
            * (t_inside - plant_params.t_supply_c)
        )

        out_t[i] = t
        out_t_inside[i] = t_inside
        out_t_amb[i] = t_amb
        out_q_load[i] = q_load
        out_q_cool[i] = q_cool
        # Record the UNCLAMPED command so the plot shows the controller's
        # intent (it can dip below v_min or above v_max during saturation).
        out_v_command[i] = v_command_unclamped
        out_v_actual[i] = v_actual
        # Strict comparison: v_command_unclamped exactly equal to a limit
        # is NOT saturated (only when it would have wanted past the limit).
        out_saturated[i] = (
            v_command_unclamped < fan_params.v_dot_min_m3s
            or v_command_unclamped > fan_params.v_dot_max_m3s
        )

    return SimulationResult(
        t_s=out_t,
        t_inside_c=out_t_inside,
        t_setpoint_c=out_t_setpoint,
        t_amb_c=out_t_amb,
        q_load_w=out_q_load,
        q_cool_w=out_q_cool,
        v_dot_command_m3s=out_v_command,
        v_dot_actual_m3s=out_v_actual,
        saturated=out_saturated,
    )


from src.units import m3s_to_cfm


def compute_summary(result: SimulationResult) -> dict[str, float]:
    """Returns peak/mean/RMS/min CFM, max excursion, settling time, saturation %.

    settling_time_s is the earliest time t* such that
    |T_inside(t) - T_setpoint| <= 0.5 °C for ALL t in [t*, end].
    Returns np.inf if no such t* exists.
    """
    cfm_command = np.array([m3s_to_cfm(v) for v in result.v_dot_command_m3s])
    excursion = np.abs(result.t_inside_c - result.t_setpoint_c)

    # Settling time: walk backwards to find the latest time the trace was
    # OUT of the band. The earliest settling time is the next sample after that.
    band = 0.5
    out_of_band = excursion > band
    if not np.any(out_of_band):
        settling_time_s = 0.0
    elif np.all(out_of_band):
        settling_time_s = float("inf")
    else:
        # Index of the last out-of-band sample
        last_bad = int(np.max(np.where(out_of_band)))
        if last_bad == len(result.t_s) - 1:
            settling_time_s = float("inf")
        else:
            settling_time_s = float(result.t_s[last_bad + 1])

    return {
        "peak_cfm": float(np.max(cfm_command)),
        "mean_cfm": float(np.mean(cfm_command)),
        "rms_cfm": float(np.sqrt(np.mean(cfm_command ** 2))),
        "min_commanded_cfm": float(np.min(cfm_command)),
        "max_excursion_c": float(np.max(excursion)),
        "settling_time_s": settling_time_s,
        "saturation_pct": float(100.0 * np.mean(result.saturated)),
    }


def compute_experiment_warnings(result: SimulationResult) -> list[str]:
    """Return human-readable warnings about a completed run.

    Warnings are NOT errors — the run produced a result. They flag suspicious
    or infeasible operating points to the user.
    """
    warnings: list[str] = []
    summary = compute_summary(result)

    if summary["saturation_pct"] > 50.0:
        warnings.append(
            f"Loop saturated {summary['saturation_pct']:.0f}% of run. "
            "Fan range is undersized for this scenario."
        )
    if summary["max_excursion_c"] > 1.0:
        warnings.append(
            f"Peak excursion from setpoint reached "
            f"{summary['max_excursion_c']:.2f} °C — controller cannot keep up."
        )
    if summary["settling_time_s"] == float("inf"):
        warnings.append("Loop never settled within ±0.5 °C of setpoint.")
    if (result.q_cool_w < 0).mean() > 0.05:
        n_negative = int((result.q_cool_w < 0).sum())
        warnings.append(
            f"Cooling power went negative for {n_negative} samples — "
            "supply air heated the enclosure. Check T_supply vs. T_inside."
        )
    if np.any(np.isnan(result.t_inside_c)):
        warnings.append(
            "Numerical instability: NaN in temperature trace. "
            "Reduce timestep or check inputs."
        )
    return warnings
