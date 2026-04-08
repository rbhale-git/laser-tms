"""Scalar Runge-Kutta 4 integrator for first-order ODEs y'=f(t,y).

Caller is responsible for closing over any time-varying inputs that
should be held constant across the four sub-steps (e.g., a controller
output that uses zero-order hold within one timestep).
"""
from __future__ import annotations
from typing import Callable


def rk4_step(
    f: Callable[[float, float], float],
    y: float,
    t: float,
    dt: float,
) -> float:
    """One RK4 step. Pure function."""
    k1 = f(t, y)
    k2 = f(t + dt / 2.0, y + k1 * dt / 2.0)
    k3 = f(t + dt / 2.0, y + k2 * dt / 2.0)
    k4 = f(t + dt, y + k3 * dt)
    return y + (k1 + 2.0 * k2 + 2.0 * k3 + k4) * dt / 6.0
