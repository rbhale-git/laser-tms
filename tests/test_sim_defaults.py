"""Snapshot tests for the PID experiment defaults.

These tests assert loose plausible-range bounds on the summary stats
when each preset scenario runs at default parameters. Their job is to
fail loudly on a sign flip or unit error, NOT to nail exact numbers.
If a future change shifts a value by 5–10%, that's fine; but a 10×
shift means something broke.
"""
import pytest

from defaults import (
    default_plant_params,
    default_fan_params,
    default_pid_controller,
    default_t_setpoint_c,
)
from src.sim.experiment import run_experiment, compute_summary
from src.sim.scenarios import (
    laser_thermal_cycling,
    ambient_step,
    ambient_diurnal,
)


class TestPidExperimentDefaults:
    def test_laser_thermal_cycling_defaults(self):
        result = run_experiment(
            scenario=laser_thermal_cycling(),
            plant_params=default_plant_params(),
            fan_params=default_fan_params(),
            controller=default_pid_controller(),
            t_setpoint_c=default_t_setpoint_c(),
        )
        summary = compute_summary(result)
        assert 0.0 <= summary["peak_cfm"] <= 200.0
        assert summary["max_excursion_c"] < 5.0
        # Q_load=0 for ~half the run forces the fan to V_min during the
        # low-Q holds (equilibrium CFM ≈ 0.4, below V_min=30). With ramps
        # and integral wind-down this measures ~85% in practice. Bound is
        # set to flag a stuck-fan regression, not nail an exact value.
        assert summary["saturation_pct"] < 90.0

    def test_ambient_step_defaults(self):
        result = run_experiment(
            scenario=ambient_step(),
            plant_params=default_plant_params(),
            fan_params=default_fan_params(),
            controller=default_pid_controller(),
            t_setpoint_c=default_t_setpoint_c(),
        )
        summary = compute_summary(result)
        assert 0.0 <= summary["peak_cfm"] <= 200.0
        assert summary["max_excursion_c"] < 5.0
        assert summary["saturation_pct"] < 50.0

    def test_ambient_diurnal_defaults(self):
        result = run_experiment(
            scenario=ambient_diurnal(),
            plant_params=default_plant_params(),
            fan_params=default_fan_params(),
            controller=default_pid_controller(),
            t_setpoint_c=default_t_setpoint_c(),
        )
        summary = compute_summary(result)
        assert 0.0 <= summary["peak_cfm"] <= 200.0
        assert summary["max_excursion_c"] < 5.0
        assert summary["saturation_pct"] < 50.0
