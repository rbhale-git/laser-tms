"""Disturbance scenarios for the PID experiment.

A Scenario is a piecewise-linear specification of Q_load(t) and T_amb(t)
over a fixed duration. Three presets are provided: laser thermal cycling,
ambient step, and ambient diurnal drift.
"""
from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioPoint:
    t_s: float
    q_load_w: float
    t_amb_c: float


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    points: tuple[ScenarioPoint, ...]
    duration_s: float
    timestep_s: float

    def q_load_at(self, t_s: float) -> float:
        return self._interp(t_s, lambda p: p.q_load_w)

    def t_amb_at(self, t_s: float) -> float:
        return self._interp(t_s, lambda p: p.t_amb_c)

    def _interp(self, t_s: float, attr) -> float:
        pts = self.points
        if t_s <= pts[0].t_s:
            return attr(pts[0])
        if t_s >= pts[-1].t_s:
            return attr(pts[-1])
        # Linear search is fine for the small number of points we use
        for i in range(len(pts) - 1):
            p0, p1 = pts[i], pts[i + 1]
            if p0.t_s <= t_s <= p1.t_s:
                if p1.t_s == p0.t_s:
                    return attr(p0)
                frac = (t_s - p0.t_s) / (p1.t_s - p0.t_s)
                return attr(p0) + frac * (attr(p1) - attr(p0))
        return attr(pts[-1])  # unreachable, defensive


def laser_thermal_cycling(t_amb_c: float = 23.5) -> Scenario:
    """Scenario A: 3 cycles of (60 s ramp 0→100 W, 5 min hold, 60 s ramp
    100→0 W, 5 min hold). Total ≈ 33 minutes, dt = 0.5 s.
    """
    cycle_duration = 60.0 + 300.0 + 60.0 + 300.0   # 720 s per cycle
    points: list[ScenarioPoint] = []
    t = 0.0
    for _ in range(3):
        # Ramp up from 0 to 100 over 60 s
        points.append(ScenarioPoint(t_s=t, q_load_w=0.0, t_amb_c=t_amb_c))
        t += 60.0
        points.append(ScenarioPoint(t_s=t, q_load_w=100.0, t_amb_c=t_amb_c))
        # Hold at 100 for 300 s
        t += 300.0
        points.append(ScenarioPoint(t_s=t, q_load_w=100.0, t_amb_c=t_amb_c))
        # Ramp down from 100 to 0 over 60 s
        t += 60.0
        points.append(ScenarioPoint(t_s=t, q_load_w=0.0, t_amb_c=t_amb_c))
        # Hold at 0 for 300 s
        t += 300.0
        points.append(ScenarioPoint(t_s=t, q_load_w=0.0, t_amb_c=t_amb_c))
    return Scenario(
        name="laser_thermal_cycling",
        description="3× (ramp 0→100 W in 60 s, hold 5 min, ramp 100→0 W in 60 s, hold 5 min)",
        points=tuple(points),
        duration_s=3.0 * cycle_duration,
        timestep_s=0.5,
    )


def ambient_step(q_load_w: float = 100.0) -> Scenario:
    """Scenario B-sharp: T_amb 23.5 → 30 °C over 60 s, hold 15 min,
    30 → 23.5 °C over 60 s, hold 15 min. ~32 min total, dt = 0.5 s.
    """
    points = (
        ScenarioPoint(t_s=0.0,    q_load_w=q_load_w, t_amb_c=23.5),
        ScenarioPoint(t_s=60.0,   q_load_w=q_load_w, t_amb_c=30.0),
        ScenarioPoint(t_s=960.0,  q_load_w=q_load_w, t_amb_c=30.0),    # 60 + 900
        ScenarioPoint(t_s=1020.0, q_load_w=q_load_w, t_amb_c=23.5),    # 960 + 60
        ScenarioPoint(t_s=1920.0, q_load_w=q_load_w, t_amb_c=23.5),    # 1020 + 900
    )
    return Scenario(
        name="ambient_step",
        description="T_amb 23.5→30 °C in 60 s, hold 15 min, 30→23.5 °C in 60 s, hold 15 min",
        points=points,
        duration_s=1920.0,
        timestep_s=0.5,
    )


def ambient_diurnal(q_load_w: float = 100.0) -> Scenario:
    """Scenario B-slow: T_amb half-sine 23.5 → 30 → 23.5 °C over 6 h.
    Pre-sampled into 100 piecewise-linear segments. dt = 5 s.
    """
    duration_s = 6.0 * 3600.0       # 21600 s
    n_samples = 101                  # 100 segments
    base = 23.5
    amplitude = 6.5                  # peak excursion
    pts: list[ScenarioPoint] = []
    for i in range(n_samples):
        t = duration_s * i / (n_samples - 1)
        # Half-sine: 0 at t=0, peak at t=duration/2, 0 at t=duration
        t_amb = base + amplitude * math.sin(math.pi * i / (n_samples - 1))
        pts.append(ScenarioPoint(t_s=t, q_load_w=q_load_w, t_amb_c=t_amb))
    return Scenario(
        name="ambient_diurnal",
        description="T_amb half-sine 23.5 → 30 → 23.5 °C over 6 h",
        points=tuple(pts),
        duration_s=duration_s,
        timestep_s=5.0,
    )
