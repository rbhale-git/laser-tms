"""Unit tests for the PID controller with conditional-integration anti-windup."""
import pytest
from src.sim.controller import PIDController


class TestPIDController:
    def test_initialize_outputs_v_init(self):
        """After initialize(V_init), step() at the setpoint with no prior
        history should return exactly V_init (bumpless start)."""
        pid = PIDController(
            kp=2.0, ki=1.0, kd=0.5, setpoint=23.0,
            v_min=0.0, v_max=100.0,
        )
        pid.initialize(15.0)
        out = pid.step(measurement_c=23.0, dt_s=1.0)  # error = 0
        assert out == pytest.approx(15.0)

    def test_p_only_proportional_response(self):
        """With Ki=Kd=0 and integral preloaded to 0, output = Kp * error."""
        pid = PIDController(
            kp=3.0, ki=0.0, kd=0.0, setpoint=23.0,
            v_min=-100.0, v_max=100.0,
        )
        pid.initialize(0.0)
        # error = 25 - 23 = +2 → output = 3 * 2 + 0 = 6
        out = pid.step(measurement_c=25.0, dt_s=1.0)
        assert out == pytest.approx(6.0)

    def test_anti_windup_at_max(self):
        """Integral should NOT grow when output is saturated high and
        error is positive (would push further into saturation)."""
        pid = PIDController(
            kp=1.0, ki=10.0, kd=0.0, setpoint=23.0,
            v_min=0.0, v_max=10.0,
        )
        pid.initialize(10.0)        # integral = 10, at v_max already
        # error = 24 - 23 = +1 → tentative = 1 + 10 + 0 = 11 > v_max=10
        # Anti-windup: skip integral update
        pid.step(measurement_c=24.0, dt_s=1.0)
        assert pid.integral == pytest.approx(10.0)  # unchanged

    def test_anti_windup_at_min(self):
        """Symmetric: integral should NOT shrink when output is saturated
        low and error is negative."""
        pid = PIDController(
            kp=1.0, ki=10.0, kd=0.0, setpoint=23.0,
            v_min=0.0, v_max=10.0,
        )
        pid.initialize(0.0)         # integral = 0, at v_min already
        # error = 22 - 23 = -1 → tentative = -1 + 0 + 0 = -1 < v_min=0
        # Anti-windup: skip integral update
        pid.step(measurement_c=22.0, dt_s=1.0)
        assert pid.integral == pytest.approx(0.0)  # unchanged

    def test_derivative_on_measurement_no_setpoint_kick(self):
        """Changing the setpoint should NOT cause a derivative spike,
        because the derivative is on measurement (not error). The
        proportional term is allowed to respond."""
        pid = PIDController(
            kp=2.0, ki=0.0, kd=10.0, setpoint=23.0,
            v_min=-1000.0, v_max=1000.0,
        )
        pid.initialize(0.0)
        # First step: prev_measurement is None → d_meas = 0
        out1 = pid.step(measurement_c=23.0, dt_s=1.0)
        # Now move the setpoint up by 5. The measurement hasn't moved.
        pid.setpoint = 28.0
        # error = 23 - 28 = -5; d_meas = (23 - 23)/1 = 0
        # tentative = 2*-5 + 0 + 10*0 = -10
        # If derivative were on error, error jumped 0 → -5, contributing
        # 10 * -5/1 = -50, so cmd would be -60. We expect -10 only.
        out2 = pid.step(measurement_c=23.0, dt_s=1.0)
        assert out1 == pytest.approx(0.0)
        assert out2 == pytest.approx(-10.0)
