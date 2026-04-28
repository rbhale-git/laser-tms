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


class TestRunExperiment:
    def test_no_disturbance_stays_at_setpoint(self):
        """Constant Q_load and T_amb at the equilibrium operating point.
        T_inside should remain at setpoint (within numerical tolerance) and
        V_actual should remain at V_init for the entire run."""
        from src.sim.experiment import run_experiment
        from src.sim.scenarios import Scenario, ScenarioPoint

        # Build a flat scenario at equilibrium with the test plant params:
        # V_eq = 100 / (1.19 * 1005 * 5) ≈ 0.016724 m³/s, well within fan range.
        flat = Scenario(
            name="flat", description="constant load and ambient",
            points=(
                ScenarioPoint(t_s=0.0,   q_load_w=100.0, t_amb_c=23.0),
                ScenarioPoint(t_s=120.0, q_load_w=100.0, t_amb_c=23.0),
            ),
            duration_s=120.0,
            timestep_s=1.0,
        )
        result = run_experiment(
            scenario=flat,
            plant_params=_plant(),
            fan_params=_fan(),
            controller=_pid(),
            t_setpoint_c=23.0,
        )
        assert result.t_inside_c[-1] == pytest.approx(23.0, abs=1e-4)
        assert result.v_dot_actual_m3s[-1] == pytest.approx(
            result.v_dot_actual_m3s[0], rel=1e-3,
        )
        assert not result.saturated.any()

    def test_small_ambient_step_recovers_to_setpoint(self):
        """A 1 °C ambient step should produce a small transient that the
        controller drives back near the setpoint by the end of a 30-minute run."""
        from src.sim.experiment import run_experiment
        from src.sim.scenarios import Scenario, ScenarioPoint

        s = Scenario(
            name="small_step", description="",
            points=(
                ScenarioPoint(t_s=0.0,    q_load_w=100.0, t_amb_c=23.0),
                ScenarioPoint(t_s=60.0,   q_load_w=100.0, t_amb_c=24.0),
                ScenarioPoint(t_s=1800.0, q_load_w=100.0, t_amb_c=24.0),
            ),
            duration_s=1800.0,
            timestep_s=1.0,
        )
        result = run_experiment(
            scenario=s,
            plant_params=_plant(),
            fan_params=_fan(),
            controller=_pid(),
            t_setpoint_c=23.0,
        )
        # Last 60 samples should all be very close to setpoint
        assert np.all(np.abs(result.t_inside_c[-60:] - 23.0) < 0.5)

    def test_returns_correct_array_shapes(self):
        """All output arrays must have the same length, equal to the
        number of timesteps in the scenario."""
        from src.sim.experiment import run_experiment
        from src.sim.scenarios import Scenario, ScenarioPoint

        s = Scenario(
            name="short", description="",
            points=(
                ScenarioPoint(t_s=0.0,  q_load_w=100.0, t_amb_c=23.0),
                ScenarioPoint(t_s=10.0, q_load_w=100.0, t_amb_c=23.0),
            ),
            duration_s=10.0,
            timestep_s=1.0,
        )
        result = run_experiment(
            scenario=s,
            plant_params=_plant(),
            fan_params=_fan(),
            controller=_pid(),
            t_setpoint_c=23.0,
        )
        n = 10  # int(10.0 / 1.0)
        assert len(result.t_s) == n
        assert len(result.t_inside_c) == n
        assert len(result.t_setpoint_c) == n
        assert len(result.t_amb_c) == n
        assert len(result.q_load_w) == n
        assert len(result.q_cool_w) == n
        assert len(result.v_dot_command_m3s) == n
        assert len(result.v_dot_actual_m3s) == n
        assert len(result.saturated) == n


class TestComputeSummary:
    def _flat_result(self, t_inside_value: float = 23.0,
                     v_command_value: float = 0.04) -> SimulationResult:
        """Build a fake SimulationResult representing a perfectly steady run."""
        n = 100
        return SimulationResult(
            t_s=np.linspace(0.0, 100.0, n),
            t_inside_c=np.full(n, t_inside_value),
            t_setpoint_c=np.full(n, 23.0),
            t_amb_c=np.full(n, 23.0),
            q_load_w=np.full(n, 100.0),
            q_cool_w=np.full(n, 100.0),
            v_dot_command_m3s=np.full(n, v_command_value),
            v_dot_actual_m3s=np.full(n, v_command_value),
            saturated=np.zeros(n, dtype=bool),
        )

    def test_returns_expected_keys(self):
        from src.sim.experiment import compute_summary
        summary = compute_summary(self._flat_result())
        assert set(summary.keys()) == {
            "peak_cfm", "mean_cfm", "rms_cfm", "min_commanded_cfm",
            "max_excursion_c", "settling_time_s", "saturation_pct",
        }

    def test_peak_matches_max_command(self):
        from src.sim.experiment import compute_summary
        from src.units import m3s_to_cfm
        n = 50
        commands = np.linspace(0.02, 0.08, n)
        r = SimulationResult(
            t_s=np.arange(n, dtype=float),
            t_inside_c=np.full(n, 23.0),
            t_setpoint_c=np.full(n, 23.0),
            t_amb_c=np.full(n, 23.0),
            q_load_w=np.full(n, 100.0),
            q_cool_w=np.full(n, 100.0),
            v_dot_command_m3s=commands,
            v_dot_actual_m3s=commands,
            saturated=np.zeros(n, dtype=bool),
        )
        summary = compute_summary(r)
        assert summary["peak_cfm"] == pytest.approx(m3s_to_cfm(0.08))
        assert summary["min_commanded_cfm"] == pytest.approx(m3s_to_cfm(0.02))

    def test_settling_time_zero_when_already_in_band(self):
        from src.sim.experiment import compute_summary
        # T_inside is exactly at setpoint everywhere → settled from t=0
        summary = compute_summary(self._flat_result(t_inside_value=23.0))
        assert summary["settling_time_s"] == pytest.approx(0.0)

    def test_settling_time_inf_when_never_settles(self):
        from src.sim.experiment import compute_summary
        # T_inside is constantly 5 °C above setpoint → never settles
        n = 100
        r = SimulationResult(
            t_s=np.linspace(0.0, 100.0, n),
            t_inside_c=np.full(n, 28.0),       # always 5 °C high
            t_setpoint_c=np.full(n, 23.0),
            t_amb_c=np.full(n, 23.0),
            q_load_w=np.full(n, 100.0),
            q_cool_w=np.full(n, 100.0),
            v_dot_command_m3s=np.full(n, 0.04),
            v_dot_actual_m3s=np.full(n, 0.04),
            saturated=np.zeros(n, dtype=bool),
        )
        summary = compute_summary(r)
        assert summary["settling_time_s"] == np.inf
        assert summary["max_excursion_c"] == pytest.approx(5.0)


class TestComputeExperimentWarnings:
    def test_high_saturation_warning(self):
        from src.sim.experiment import compute_experiment_warnings
        n = 100
        r = SimulationResult(
            t_s=np.linspace(0.0, 100.0, n),
            t_inside_c=np.full(n, 23.0),
            t_setpoint_c=np.full(n, 23.0),
            t_amb_c=np.full(n, 23.0),
            q_load_w=np.full(n, 100.0),
            q_cool_w=np.full(n, 100.0),
            v_dot_command_m3s=np.full(n, 0.04),
            v_dot_actual_m3s=np.full(n, 0.04),
            saturated=np.ones(n, dtype=bool),  # saturated 100% of run
        )
        warnings = compute_experiment_warnings(r)
        assert any("saturat" in w.lower() for w in warnings)

    def test_no_warnings_for_clean_run(self):
        from src.sim.experiment import compute_experiment_warnings
        warnings = compute_experiment_warnings(
            TestComputeSummary()._flat_result()
        )
        assert warnings == []
