"""Unit tests for the scalar RK4 integrator."""
import math
import pytest
from src.sim.integrator import rk4_step


class TestRK4Step:
    def test_constant_derivative_exact(self):
        """f(t,y)=1 → after dt, y should be exactly y0 + dt."""
        f = lambda t, y: 1.0
        y_new = rk4_step(f, y=5.0, t=0.0, dt=0.5)
        assert y_new == pytest.approx(5.5)

    def test_exponential_decay_matches_analytic(self):
        """f(t,y)=-y → analytic solution is y0 * exp(-dt). RK4 should
        match to several decimal places for small dt."""
        f = lambda t, y: -y
        y0 = 1.0
        dt = 0.1
        y_new = rk4_step(f, y=y0, t=0.0, dt=dt)
        expected = y0 * math.exp(-dt)
        assert y_new == pytest.approx(expected, rel=1e-6)

    def test_more_accurate_than_euler(self):
        """For a nonlinear ODE f(t,y)=-y², RK4 error should be much smaller
        than Euler error at the same dt."""
        f = lambda t, y: -y * y
        y0 = 1.0
        dt = 0.1
        # Analytic solution: y(t) = 1 / (1 + t)
        analytic = 1.0 / (1.0 + dt)
        rk4_result = rk4_step(f, y=y0, t=0.0, dt=dt)
        euler_result = y0 + dt * f(0.0, y0)
        rk4_error = abs(rk4_result - analytic)
        euler_error = abs(euler_result - analytic)
        assert rk4_error < euler_error / 100.0
