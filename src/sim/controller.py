"""PID controller with conditional-integration anti-windup.

Sign convention: error = measurement - setpoint.
Positive error (T_inside above setpoint) → controller increases CFM.
All user-facing gains are positive numbers.

Derivative-on-measurement (not error) avoids setpoint kicks: when the
setpoint moves, only the proportional term responds; the derivative
sees no change in the measurement.

Anti-windup: skip the integral update on any tick where the unsaturated
output is at/above v_max with positive error, or at/below v_min with
negative error. This prevents the integral from "winding up" while the
actuator is pinned at a limit.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class PIDController:
    kp: float
    ki: float
    kd: float
    setpoint: float
    v_min: float
    v_max: float
    integral: float = 0.0
    prev_measurement: Optional[float] = None

    def initialize(self, v_init_m3s: float) -> None:
        """Set integral so that step() at the setpoint with no prior history
        returns exactly v_init_m3s (bumpless start)."""
        self.integral = v_init_m3s
        self.prev_measurement = None

    def step(self, measurement_c: float, dt_s: float) -> float:
        """One controller tick. Returns the UNCLAMPED commanded V_dot in m³/s.

        The experiment harness is responsible for applying the physical
        clamp before passing to the actuator and for recording whether the
        unclamped command exceeded the limits (saturation flag). Anti-windup
        uses the internally-stored v_min/v_max to detect saturation and
        skip the integral update when appropriate.
        """
        error = measurement_c - self.setpoint

        # Derivative on measurement (zero on first call)
        if self.prev_measurement is None:
            d_meas = 0.0
        else:
            d_meas = (measurement_c - self.prev_measurement) / dt_s
        self.prev_measurement = measurement_c

        # Tentative output BEFORE integral update
        tentative = self.kp * error + self.integral + self.kd * d_meas

        # Conditional integration: skip if saturated AND would push further
        push_high = tentative >= self.v_max and error > 0
        push_low = tentative <= self.v_min and error < 0
        if not (push_high or push_low):
            self.integral += self.ki * error * dt_s

        # Final output (UNCLAMPED — caller applies the physical clamp)
        return self.kp * error + self.integral + self.kd * d_meas
