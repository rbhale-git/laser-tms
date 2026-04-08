"""Unit tests for the fan actuator (first-order lag + clamp)."""
import math
import pytest
from src.sim.actuator import FanParams, fan_step


def _fan() -> FanParams:
    return FanParams(tau_s=3.0, v_dot_min_m3s=0.01, v_dot_max_m3s=0.10)


class TestFanStep:
    def test_no_change_when_command_equals_actual(self):
        params = _fan()
        v_new = fan_step(
            v_actual_m3s=0.05, v_command_m3s=0.05,
            dt_s=0.5, params=params,
        )
        assert v_new == pytest.approx(0.05)

    def test_first_order_lag_at_one_tau(self):
        """After dt = tau, response should be (1 - 1/e) ≈ 63.2% of step."""
        params = _fan()  # tau = 3 s
        v_new = fan_step(
            v_actual_m3s=0.0, v_command_m3s=0.10,
            dt_s=3.0, params=params,
        )
        expected = 0.10 * (1.0 - math.exp(-1.0))
        assert v_new == pytest.approx(expected, rel=1e-9)

    def test_clamps_above_max(self):
        params = _fan()
        v_new = fan_step(
            v_actual_m3s=0.09, v_command_m3s=1.0,  # huge command
            dt_s=10.0, params=params,                # long enough to settle
        )
        assert v_new == pytest.approx(0.10)

    def test_clamps_below_min(self):
        params = _fan()
        v_new = fan_step(
            v_actual_m3s=0.02, v_command_m3s=-1.0,  # huge negative command
            dt_s=10.0, params=params,
        )
        assert v_new == pytest.approx(0.01)

    def test_zero_dt_is_noop(self):
        params = _fan()
        v_new = fan_step(
            v_actual_m3s=0.05, v_command_m3s=0.10,
            dt_s=0.0, params=params,
        )
        assert v_new == pytest.approx(0.05)
