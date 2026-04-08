"""Unit tests for scenario definitions and interpolation."""
import pytest
from src.sim.scenarios import (
    Scenario,
    ScenarioPoint,
    laser_thermal_cycling,
    ambient_step,
    ambient_diurnal,
)


class TestInterpolation:
    def test_linear_between_points(self):
        s = Scenario(
            name="linear", description="",
            points=(
                ScenarioPoint(t_s=0.0, q_load_w=0.0, t_amb_c=20.0),
                ScenarioPoint(t_s=10.0, q_load_w=100.0, t_amb_c=30.0),
            ),
            duration_s=10.0, timestep_s=1.0,
        )
        assert s.q_load_at(5.0) == pytest.approx(50.0)
        assert s.t_amb_at(5.0) == pytest.approx(25.0)

    def test_clamps_out_of_range(self):
        s = Scenario(
            name="clamp", description="",
            points=(
                ScenarioPoint(t_s=0.0, q_load_w=10.0, t_amb_c=20.0),
                ScenarioPoint(t_s=10.0, q_load_w=20.0, t_amb_c=25.0),
            ),
            duration_s=10.0, timestep_s=1.0,
        )
        assert s.q_load_at(-5.0) == pytest.approx(10.0)
        assert s.q_load_at(99.0) == pytest.approx(20.0)
        assert s.t_amb_at(-5.0) == pytest.approx(20.0)
        assert s.t_amb_at(99.0) == pytest.approx(25.0)


class TestPresets:
    def test_laser_cycling_endpoints(self):
        s = laser_thermal_cycling()
        assert s.q_load_at(0.0) == pytest.approx(0.0)
        # 60 s into the run we should be at the top of the first ramp
        assert s.q_load_at(60.0) == pytest.approx(100.0)
        # T_amb is constant
        assert s.t_amb_at(0.0) == pytest.approx(23.5)
        assert s.t_amb_at(s.duration_s) == pytest.approx(23.5)

    def test_ambient_step_initial_and_peak(self):
        s = ambient_step()
        assert s.t_amb_at(0.0) == pytest.approx(23.5)
        assert s.t_amb_at(60.0) == pytest.approx(30.0)
        assert s.q_load_at(0.0) == pytest.approx(100.0)

    def test_ambient_diurnal_peak_at_midpoint(self):
        s = ambient_diurnal()
        midpoint = s.duration_s / 2.0
        # Half-sine peak should be near 30 °C at the midpoint
        assert s.t_amb_at(midpoint) == pytest.approx(30.0, abs=0.1)
        assert s.t_amb_at(0.0) == pytest.approx(23.5, abs=0.1)
        assert s.t_amb_at(s.duration_s) == pytest.approx(23.5, abs=0.1)
