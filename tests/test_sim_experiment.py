"""Integration tests for the PID experiment harness."""
import numpy as np
import pytest

from src.sim.actuator import FanParams
from src.sim.controller import PIDController
from src.sim.experiment import (
    SimulationResult,
    validate_experiment_inputs,
)
from src.sim.plant import PlantParams
from src.sim.scenarios import laser_thermal_cycling


def _plant() -> PlantParams:
    return PlantParams(
        thermal_capacitance_j_per_k=53000.0,
        ua_value_w_per_k=2.0,
        air_cp=1005.0,
        air_density=1.19,
        t_supply_c=18.0,
    )


def _fan() -> FanParams:
    """Spec defaults: 30–150 CFM (HEPA floor to optical ceiling)."""
    from src.units import cfm_to_m3s
    return FanParams(
        tau_s=3.0,
        v_dot_min_m3s=cfm_to_m3s(30.0),
        v_dot_max_m3s=cfm_to_m3s(150.0),
    )


def _pid() -> PIDController:
    """Spec-derived gains: 5 CFM/K, 0.5 CFM/(K·s), 0 — converted to SI."""
    from src.units import cfm_to_m3s
    return PIDController(
        kp=cfm_to_m3s(5.0),
        ki=cfm_to_m3s(0.5),
        kd=0.0,
        setpoint=23.0,
        v_min=cfm_to_m3s(30.0),
        v_max=cfm_to_m3s(150.0),
    )


class TestSimulationResultDataclass:
    def test_construct_with_zero_length_arrays(self):
        r = SimulationResult(
            t_s=np.zeros(0),
            t_inside_c=np.zeros(0),
            t_setpoint_c=np.zeros(0),
            t_amb_c=np.zeros(0),
            q_load_w=np.zeros(0),
            q_cool_w=np.zeros(0),
            v_dot_command_m3s=np.zeros(0),
            v_dot_actual_m3s=np.zeros(0),
            saturated=np.zeros(0, dtype=bool),
        )
        assert len(r.t_s) == 0


class TestValidateExperimentInputs:
    def test_rejects_t_supply_above_setpoint(self):
        plant = PlantParams(
            thermal_capacitance_j_per_k=53000.0,
            ua_value_w_per_k=2.0,
            air_cp=1005.0,
            air_density=1.19,
            t_supply_c=25.0,                     # ABOVE setpoint
        )
        with pytest.raises(ValueError, match="supply"):
            validate_experiment_inputs(
                plant_params=plant, fan_params=_fan(),
                controller=_pid(), scenario=laser_thermal_cycling(),
                t_setpoint_c=23.0,
            )

    def test_rejects_negative_kp(self):
        from src.units import cfm_to_m3s
        pid = PIDController(
            kp=-1.0, ki=0.0001, kd=0.0,
            setpoint=23.0,
            v_min=cfm_to_m3s(30.0), v_max=cfm_to_m3s(150.0),
        )
        with pytest.raises(ValueError, match="gains"):
            validate_experiment_inputs(
                plant_params=_plant(), fan_params=_fan(),
                controller=pid, scenario=laser_thermal_cycling(),
                t_setpoint_c=23.0,
            )

    def test_rejects_v_max_le_v_min(self):
        fan = FanParams(tau_s=3.0, v_dot_min_m3s=0.05, v_dot_max_m3s=0.05)
        with pytest.raises(ValueError, match="max"):
            validate_experiment_inputs(
                plant_params=_plant(), fan_params=fan,
                controller=_pid(), scenario=laser_thermal_cycling(),
                t_setpoint_c=23.0,
            )

    def test_accepts_valid_inputs(self):
        # Should not raise
        validate_experiment_inputs(
            plant_params=_plant(), fan_params=_fan(),
            controller=_pid(), scenario=laser_thermal_cycling(),
            t_setpoint_c=23.0,
        )
