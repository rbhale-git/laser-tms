# PID Control Extension Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a closed-loop, time-domain thermal simulation with PID-controlled fan CFM, three preset disturbance scenarios, and a Streamlit experiment tab that reports the CFM range needed to hold setpoint.

**Architecture:** Pure-functional simulation modules under `src/sim/` (plant ODE, fan actuator, PID controller, RK4 integrator, scenarios, experiment harness), a thin Streamlit panel that calls them, and an `app.py` refactor to wrap the existing layout in `st.tabs(["Steady State", "PID Experiment"])`. State lives only inside the controller, the actuator output, and the integrator state.

**Tech Stack:** Python 3.11+, numpy, pytest, Streamlit, Plotly. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-04-07-pid-experiment-design.md`

---

## Background — Codebase Orientation

If you're new to this project, here's what you need to know before starting:

- **Entry point:** `app.py` — a Streamlit single-page app that composes input panels, builds dataclass models, calls solvers, and renders results.
- **Source layout:** `src/` contains pure logic. `src/models.py` (dataclasses), `src/solvers.py` (pure functions returning numbers), `src/constants.py` (`AIR_CP=1005.0`, `AIR_DENSITY=1.19`, `M3S_TO_CFM=2118.88`, etc.), `src/units.py` (unit conversion helpers), `src/ui/*.py` (one Streamlit panel per file).
- **Tests:** `tests/test_*.py`, run with `pytest tests/ -q`. The existing 30 tests must keep passing throughout. Existing style is class-based grouping (`class TestSolveAirflow:` with method-per-test) and `pytest.approx` for float comparison.
- **Defaults:** `defaults.py` (at repo root, NOT in `src/`) provides factory functions for default model instances. The PID extension will add new factories here.
- **Branch:** all work happens on a new branch `feat/pid-experiment` created off the current `feat/separate-ambient-setpoint` branch (which already contains the design spec).
- **Imports:** existing code uses `from src.solvers import ...`, `from defaults import ...`, `from src.constants import AIR_CP, AIR_DENSITY`. Match this style.
- **Style:** dataclasses + pure functions, no class hierarchies, no abstract base classes, no metaclasses.

---

## File Structure

**Created (15 files):**

| Path | Responsibility |
|---|---|
| `src/sim/__init__.py` | Empty package marker |
| `src/sim/plant.py` | `PlantParams` dataclass, `dT_inside_dt` ODE function |
| `src/sim/actuator.py` | `FanParams` dataclass, `fan_step` first-order lag |
| `src/sim/controller.py` | `PIDController` dataclass with `initialize`/`step` |
| `src/sim/integrator.py` | `rk4_step` scalar Runge-Kutta integrator |
| `src/sim/scenarios.py` | `ScenarioPoint`, `Scenario`, three preset constructors |
| `src/sim/experiment.py` | `SimulationResult`, `validate_experiment_inputs`, `run_experiment`, `compute_summary`, `compute_experiment_warnings` |
| `src/ui/panel_pid_experiment.py` | Streamlit experiment tab UI + Plotly figures |
| `tests/test_sim_plant.py` | 5 unit tests for plant.py |
| `tests/test_sim_actuator.py` | 5 unit tests for actuator.py |
| `tests/test_sim_controller.py` | 5 unit tests for controller.py |
| `tests/test_sim_integrator.py` | 3 unit tests for integrator.py |
| `tests/test_sim_scenarios.py` | 5 unit tests for scenarios.py |
| `tests/test_sim_experiment.py` | 8 integration tests for experiment.py |
| `tests/test_sim_defaults.py` | 3 snapshot tests, one per preset scenario |

**Modified (2 files):**

| Path | Change |
|---|---|
| `defaults.py` | Add `default_plant_params`, `default_fan_params`, `default_pid_controller`, `default_t_supply_c`, `default_t_setpoint_c` |
| `app.py` | Wrap existing single-page layout in `st.tabs(["Steady State", "PID Experiment"])` and render the new panel in the second tab |

**Unchanged:** every other file in the project. The existing steady-state functionality is not touched.

---

## Task 1: Branch and package scaffold

**Files:**
- Create: `src/sim/__init__.py`

- [ ] **Step 1: Create the feature branch off the current branch**

```bash
git checkout feat/separate-ambient-setpoint
git pull --ff-only || true        # no remote yet, ignore failure
git checkout -b feat/pid-experiment
```

- [ ] **Step 2: Run the existing test suite as a baseline (must be green)**

```bash
pytest tests/ -q
```
Expected: `30 passed` in well under a second.

- [ ] **Step 3: Create the empty `src/sim/__init__.py` package marker**

Write the following file at `src/sim/__init__.py`:
```python
"""Time-domain simulation modules: plant ODE, fan actuator, PID controller,
RK4 integrator, scenario definitions, and the experiment harness.

All modules are pure (no Streamlit / no plotting / no I/O) so they can be
called from a script, notebook, or Streamlit panel interchangeably.
"""
```

- [ ] **Step 4: Verify nothing broke**

```bash
pytest tests/ -q
```
Expected: `30 passed`.

- [ ] **Step 5: Commit**

```bash
git add src/sim/__init__.py
git commit -m "feat: scaffold src/sim package for PID experiment extension"
```

---

## Task 2: Plant ODE module (TDD)

**Files:**
- Create: `src/sim/plant.py`
- Create: `tests/test_sim_plant.py`

- [ ] **Step 1: Write the failing test file**

Write the following file at `tests/test_sim_plant.py`:
```python
"""Unit tests for the lumped-capacitance plant ODE."""
import pytest
from src.sim.plant import PlantParams, dT_inside_dt


def _params(ua_value_w_per_k: float = 2.0) -> PlantParams:
    """Standard plant params for tests; UA can be overridden to isolate terms."""
    return PlantParams(
        thermal_capacitance_j_per_k=53000.0,
        ua_value_w_per_k=ua_value_w_per_k,
        air_cp=1005.0,
        air_density=1.19,
        t_supply_c=18.0,
    )


class TestPlantODE:
    def test_dT_dt_zero_at_equilibrium(self):
        """At T_inside=23, T_amb=23, Q_load=100, find V_dot s.t. dT/dt=0:
        Q_load + UA*(T_amb-T_inside) = ρ*V*cp*(T_inside-T_supply)
        100 + 0 = 1.19 * V * 1005 * 5 = 5979.75 * V
        V = 100 / 5979.75 ≈ 0.016724 m³/s
        """
        params = _params(ua_value_w_per_k=2.0)
        v_eq = 100.0 / (1.19 * 1005.0 * 5.0)
        rate = dT_inside_dt(
            t_inside_c=23.0,
            v_dot_m3s=v_eq,
            q_load_w=100.0,
            t_amb_c=23.0,
            params=params,
        )
        assert rate == pytest.approx(0.0, abs=1e-12)

    def test_dT_dt_positive_when_heated(self):
        """No cooling, no ambient coupling, positive Q_load → dT/dt > 0."""
        params = _params(ua_value_w_per_k=0.0)
        rate = dT_inside_dt(
            t_inside_c=23.0,
            v_dot_m3s=0.0,
            q_load_w=100.0,
            t_amb_c=23.0,
            params=params,
        )
        assert rate > 0.0

    def test_dT_dt_negative_when_overcooled(self):
        """No load, no ambient, positive cooling → dT/dt < 0."""
        params = _params(ua_value_w_per_k=0.0)
        rate = dT_inside_dt(
            t_inside_c=23.0,
            v_dot_m3s=0.05,
            q_load_w=0.0,
            t_amb_c=23.0,
            params=params,
        )
        assert rate < 0.0

    def test_q_cool_proportional_to_v_dot(self):
        """With UA=0 and Q_load=0, dT/dt is linear in V_dot."""
        params = _params(ua_value_w_per_k=0.0)
        rate1 = dT_inside_dt(
            t_inside_c=23.0, v_dot_m3s=0.01,
            q_load_w=0.0, t_amb_c=23.0, params=params,
        )
        rate2 = dT_inside_dt(
            t_inside_c=23.0, v_dot_m3s=0.02,
            q_load_w=0.0, t_amb_c=23.0, params=params,
        )
        assert rate2 == pytest.approx(2.0 * rate1)

    def test_q_cool_negative_when_supply_warmer_than_inside(self):
        """If T_inside < T_supply, the supply air HEATS the enclosure.
        Q_cool goes negative; dT/dt should reflect that (positive contribution
        from the cooling term)."""
        params = _params(ua_value_w_per_k=0.0)
        rate = dT_inside_dt(
            t_inside_c=15.0,         # below supply temp 18
            v_dot_m3s=0.05,
            q_load_w=0.0,
            t_amb_c=15.0,
            params=params,
        )
        assert rate > 0.0  # supply air is warmer → enclosure warms
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
pytest tests/test_sim_plant.py -q
```
Expected: `ModuleNotFoundError: No module named 'src.sim.plant'` (collection error). All 5 tests fail.

- [ ] **Step 3: Write the implementation**

Write the following file at `src/sim/plant.py`:
```python
"""Lumped-capacitance plant ODE for the enclosure thermal simulation.

  C_e · dT_inside/dt = Q_load(t) - Q_cool(t) + UA·(T_amb(t) - T_inside)

where Q_cool(t) = ρ · V_dot(t) · c_p · (T_inside - T_supply).

Q_cool can go negative if T_inside < T_supply (the supply air heats a
too-cold enclosure); this is physically correct and is left unclamped.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PlantParams:
    thermal_capacitance_j_per_k: float
    ua_value_w_per_k: float
    air_cp: float
    air_density: float
    t_supply_c: float


def dT_inside_dt(
    t_inside_c: float,
    v_dot_m3s: float,
    q_load_w: float,
    t_amb_c: float,
    params: PlantParams,
) -> float:
    """Time derivative of T_inside in K/s.

    All inputs in SI. Caller is responsible for evaluating Q_load(t) and
    T_amb(t) at the appropriate sub-step time when used inside RK4.
    """
    m_dot = params.air_density * v_dot_m3s
    q_cool = m_dot * params.air_cp * (t_inside_c - params.t_supply_c)
    q_amb = params.ua_value_w_per_k * (t_amb_c - t_inside_c)
    return (q_load_w - q_cool + q_amb) / params.thermal_capacitance_j_per_k
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
pytest tests/test_sim_plant.py -q
```
Expected: `5 passed`.

- [ ] **Step 5: Run the full suite to confirm nothing else broke**

```bash
pytest tests/ -q
```
Expected: `35 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/sim/plant.py tests/test_sim_plant.py
git commit -m "feat: add lumped-capacitance plant ODE for PID experiment"
```

---

## Task 3: Fan actuator module (TDD)

**Files:**
- Create: `src/sim/actuator.py`
- Create: `tests/test_sim_actuator.py`

- [ ] **Step 1: Write the failing test file**

Write the following file at `tests/test_sim_actuator.py`:
```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
pytest tests/test_sim_actuator.py -q
```
Expected: collection error / `ModuleNotFoundError: No module named 'src.sim.actuator'`.

- [ ] **Step 3: Write the implementation**

Write the following file at `src/sim/actuator.py`:
```python
"""Fan actuator: first-order lag toward command, then physical clamp.

  V_actual(t+dt) = V_actual(t) + (V_command - V_actual(t)) * (1 - exp(-dt/tau))
  V_actual ∈ [V_min, V_max]
"""
from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class FanParams:
    tau_s: float
    v_dot_min_m3s: float
    v_dot_max_m3s: float


def fan_step(
    v_actual_m3s: float,
    v_command_m3s: float,
    dt_s: float,
    params: FanParams,
) -> float:
    """One actuator tick. Pure function."""
    if dt_s <= 0.0:
        return v_actual_m3s
    response = 1.0 - math.exp(-dt_s / params.tau_s)
    v_new = v_actual_m3s + (v_command_m3s - v_actual_m3s) * response
    return max(params.v_dot_min_m3s, min(params.v_dot_max_m3s, v_new))
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
pytest tests/test_sim_actuator.py -q
```
Expected: `5 passed`.

- [ ] **Step 5: Run the full suite**

```bash
pytest tests/ -q
```
Expected: `40 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/sim/actuator.py tests/test_sim_actuator.py
git commit -m "feat: add first-order fan actuator with clamping"
```

---

## Task 4: PID controller module (TDD)

**Files:**
- Create: `src/sim/controller.py`
- Create: `tests/test_sim_controller.py`

- [ ] **Step 1: Write the failing test file**

Write the following file at `tests/test_sim_controller.py`:
```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
pytest tests/test_sim_controller.py -q
```
Expected: collection error / `ModuleNotFoundError: No module named 'src.sim.controller'`.

- [ ] **Step 3: Write the implementation**

Write the following file at `src/sim/controller.py`:
```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
pytest tests/test_sim_controller.py -q
```
Expected: `5 passed`.

- [ ] **Step 5: Run the full suite**

```bash
pytest tests/ -q
```
Expected: `45 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/sim/controller.py tests/test_sim_controller.py
git commit -m "feat: add PID controller with conditional-integration anti-windup"
```

---

## Task 5: RK4 integrator module (TDD)

**Files:**
- Create: `src/sim/integrator.py`
- Create: `tests/test_sim_integrator.py`

- [ ] **Step 1: Write the failing test file**

Write the following file at `tests/test_sim_integrator.py`:
```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
pytest tests/test_sim_integrator.py -q
```
Expected: collection error / `ModuleNotFoundError: No module named 'src.sim.integrator'`.

- [ ] **Step 3: Write the implementation**

Write the following file at `src/sim/integrator.py`:
```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
pytest tests/test_sim_integrator.py -q
```
Expected: `3 passed`.

- [ ] **Step 5: Run the full suite**

```bash
pytest tests/ -q
```
Expected: `48 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/sim/integrator.py tests/test_sim_integrator.py
git commit -m "feat: add scalar RK4 integrator"
```

---

## Task 6: Scenarios module (TDD)

**Files:**
- Create: `src/sim/scenarios.py`
- Create: `tests/test_sim_scenarios.py`

- [ ] **Step 1: Write the failing test file**

Write the following file at `tests/test_sim_scenarios.py`:
```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
pytest tests/test_sim_scenarios.py -q
```
Expected: collection error / `ModuleNotFoundError: No module named 'src.sim.scenarios'`.

- [ ] **Step 3: Write the implementation**

Write the following file at `src/sim/scenarios.py`:
```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
pytest tests/test_sim_scenarios.py -q
```
Expected: `5 passed`.

- [ ] **Step 5: Run the full suite**

```bash
pytest tests/ -q
```
Expected: `53 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/sim/scenarios.py tests/test_sim_scenarios.py
git commit -m "feat: add three preset disturbance scenarios with linear interpolation"
```

---

## Task 7: Experiment scaffolding — SimulationResult and validation (TDD)

**Files:**
- Create: `src/sim/experiment.py`
- Create: `tests/test_sim_experiment.py`

This task adds the `SimulationResult` dataclass and the `validate_experiment_inputs` function. The actual `run_experiment` and summary code will follow in Tasks 8 and 9.

- [ ] **Step 1: Write the failing test file (validation tests only for now; the
  rest of the file will be added in Tasks 8 and 9)**

Write the following file at `tests/test_sim_experiment.py`:
```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
pytest tests/test_sim_experiment.py -q
```
Expected: collection error / `ModuleNotFoundError: No module named 'src.sim.experiment'`.

- [ ] **Step 3: Write the experiment module scaffold (just `SimulationResult`
  and `validate_experiment_inputs`; `run_experiment`, `compute_summary`, and
  `compute_experiment_warnings` are added in Tasks 8 and 9)**

Write the following file at `src/sim/experiment.py`:
```python
"""PID experiment harness: validation, time-domain simulation, summary stats.

This module is the only one the UI panel calls to run an experiment.
Tasks 8 and 9 extend it with run_experiment, compute_summary, and
compute_experiment_warnings.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

from src.sim.actuator import FanParams
from src.sim.controller import PIDController
from src.sim.plant import PlantParams
from src.sim.scenarios import Scenario


@dataclass
class SimulationResult:
    t_s: np.ndarray
    t_inside_c: np.ndarray
    t_setpoint_c: np.ndarray   # constant array, kept for plotting convenience
    t_amb_c: np.ndarray
    q_load_w: np.ndarray
    q_cool_w: np.ndarray
    v_dot_command_m3s: np.ndarray
    v_dot_actual_m3s: np.ndarray
    saturated: np.ndarray      # bool


def validate_experiment_inputs(
    plant_params: PlantParams,
    fan_params: FanParams,
    controller: PIDController,
    scenario: Scenario,
    t_setpoint_c: float,
) -> None:
    """Raise ValueError on any invalid input. The UI panel catches these
    and renders a single error box."""
    errors: list[str] = []

    if plant_params.t_supply_c >= t_setpoint_c:
        errors.append(
            f"Coil supply temp ({plant_params.t_supply_c} °C) must be below "
            f"setpoint ({t_setpoint_c} °C) — cannot cool."
        )
    if fan_params.v_dot_max_m3s <= fan_params.v_dot_min_m3s:
        errors.append(
            f"Fan max ({fan_params.v_dot_max_m3s} m³/s) must exceed "
            f"min ({fan_params.v_dot_min_m3s} m³/s)."
        )
    if fan_params.v_dot_min_m3s < 0.0:
        errors.append("Fan min CFM cannot be negative.")
    if fan_params.tau_s <= 0.0:
        errors.append("Fan time constant must be positive.")
    if controller.kp < 0.0 or controller.ki < 0.0 or controller.kd < 0.0:
        errors.append(
            f"PID gains must be non-negative "
            f"(kp={controller.kp}, ki={controller.ki}, kd={controller.kd})."
        )
    if plant_params.thermal_capacitance_j_per_k <= 0.0:
        errors.append("Thermal capacitance must be positive.")
    if plant_params.ua_value_w_per_k < 0.0:
        errors.append("UA value cannot be negative.")
    if scenario.timestep_s <= 0.0 or scenario.duration_s <= 0.0:
        errors.append("Scenario timestep and duration must be positive.")
    if scenario.timestep_s > scenario.duration_s:
        errors.append(
            f"Scenario timestep ({scenario.timestep_s}) must be smaller "
            f"than duration ({scenario.duration_s})."
        )

    if errors:
        raise ValueError("\n".join(errors))
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
pytest tests/test_sim_experiment.py -q
```
Expected: `4 passed`.

- [ ] **Step 5: Run the full suite**

```bash
pytest tests/ -q
```
Expected: `57 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/sim/experiment.py tests/test_sim_experiment.py
git commit -m "feat: add SimulationResult dataclass and experiment input validation"
```

---

## Task 8: `run_experiment` integration loop (TDD)

**Files:**
- Modify: `src/sim/experiment.py` (add `run_experiment`)
- Modify: `tests/test_sim_experiment.py` (add closed-loop integration tests)

- [ ] **Step 1: Append the closed-loop tests to `tests/test_sim_experiment.py`**

Append the following classes to `tests/test_sim_experiment.py` (after the existing `TestValidateExperimentInputs` class):
```python
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
```

- [ ] **Step 2: Run the new tests to verify they fail**

```bash
pytest tests/test_sim_experiment.py::TestRunExperiment -q
```
Expected: `ImportError: cannot import name 'run_experiment'` (or similar). All 3 new tests fail.

- [ ] **Step 3: Append `run_experiment` to `src/sim/experiment.py`**

Append the following to `src/sim/experiment.py`:
```python
from src.sim.actuator import fan_step
from src.sim.integrator import rk4_step
from src.sim.plant import dT_inside_dt


def _initial_steady_state_v_dot(
    q_load_w: float,
    t_amb_c: float,
    t_setpoint_c: float,
    plant: PlantParams,
) -> float:
    """Closed-form steady-state CFM at T_inside = T_setpoint:
        Q_load + UA·(T_amb - T_setpoint)
        = ρ · V · cp · (T_setpoint - T_supply)
    """
    numerator = q_load_w + plant.ua_value_w_per_k * (t_amb_c - t_setpoint_c)
    denominator = (
        plant.air_density * plant.air_cp * (t_setpoint_c - plant.t_supply_c)
    )
    return numerator / denominator


def run_experiment(
    scenario: Scenario,
    plant_params: PlantParams,
    fan_params: FanParams,
    controller: PIDController,
    t_setpoint_c: float,
) -> SimulationResult:
    """Integrate the closed-loop system for scenario.duration_s and return
    arrays of every state variable.

    Initialization:
      - Compute the steady-state CFM for scenario.t=0 conditions.
      - Clamp to [v_min, v_max] (a warning will fire later if it had to clamp).
      - T_inside starts at t_setpoint_c (assume system was at equilibrium).
      - controller.initialize(V_init) for bumpless start.

    Loop (zero-order hold on V_actual inside RK4):
      1. Look up scenario(t).
      2. measurement = T_inside (ideal sensor).
      3. V_command = controller.step(measurement, dt).
      4. V_actual = fan_step(V_actual, V_command, dt, fan_params).
      5. T_inside = rk4_step(plant_ode_with_v_actual_held, T_inside, t, dt).
      6. Record sample.
    """
    validate_experiment_inputs(
        plant_params=plant_params, fan_params=fan_params,
        controller=controller, scenario=scenario, t_setpoint_c=t_setpoint_c,
    )

    dt = scenario.timestep_s
    n_steps = int(scenario.duration_s / dt)

    # Initialization
    q_load_init = scenario.q_load_at(0.0)
    t_amb_init = scenario.t_amb_at(0.0)
    v_init = _initial_steady_state_v_dot(
        q_load_w=q_load_init, t_amb_c=t_amb_init,
        t_setpoint_c=t_setpoint_c, plant=plant_params,
    )
    v_init = max(fan_params.v_dot_min_m3s, min(fan_params.v_dot_max_m3s, v_init))

    t_inside = t_setpoint_c
    v_actual = v_init
    controller.initialize(v_init)

    # Output buffers
    out_t = np.zeros(n_steps)
    out_t_inside = np.zeros(n_steps)
    out_t_setpoint = np.full(n_steps, t_setpoint_c)
    out_t_amb = np.zeros(n_steps)
    out_q_load = np.zeros(n_steps)
    out_q_cool = np.zeros(n_steps)
    out_v_command = np.zeros(n_steps)
    out_v_actual = np.zeros(n_steps)
    out_saturated = np.zeros(n_steps, dtype=bool)

    for i in range(n_steps):
        t = i * dt
        q_load = scenario.q_load_at(t)
        t_amb = scenario.t_amb_at(t)

        measurement = t_inside
        # Controller returns UNCLAMPED command; harness applies the clamp
        # for the actuator and detects saturation from the unclamped value.
        v_command_unclamped = controller.step(measurement, dt)
        v_command_for_actuator = max(
            fan_params.v_dot_min_m3s,
            min(fan_params.v_dot_max_m3s, v_command_unclamped),
        )
        v_actual = fan_step(v_actual, v_command_for_actuator, dt, fan_params)

        # Plant ODE with V_actual held constant across the four RK4 sub-steps
        v_actual_held = v_actual

        def _plant_ode(t_sub: float, T: float) -> float:
            return dT_inside_dt(
                t_inside_c=T,
                v_dot_m3s=v_actual_held,
                q_load_w=scenario.q_load_at(t_sub),
                t_amb_c=scenario.t_amb_at(t_sub),
                params=plant_params,
            )

        t_inside = rk4_step(_plant_ode, t_inside, t, dt)

        if not np.isfinite(t_inside):
            raise RuntimeError(
                f"Plant integration produced non-finite value at t={t:.1f}s."
            )

        # Compute Q_cool with the post-update T_inside (matches what we record)
        q_cool = (
            plant_params.air_density
            * v_actual
            * plant_params.air_cp
            * (t_inside - plant_params.t_supply_c)
        )

        out_t[i] = t
        out_t_inside[i] = t_inside
        out_t_amb[i] = t_amb
        out_q_load[i] = q_load
        out_q_cool[i] = q_cool
        # Record the UNCLAMPED command so the plot shows the controller's
        # intent (it can dip below v_min or above v_max during saturation).
        out_v_command[i] = v_command_unclamped
        out_v_actual[i] = v_actual
        # Strict comparison: v_command_unclamped exactly equal to a limit
        # is NOT saturated (only when it would have wanted past the limit).
        out_saturated[i] = (
            v_command_unclamped < fan_params.v_dot_min_m3s
            or v_command_unclamped > fan_params.v_dot_max_m3s
        )

    return SimulationResult(
        t_s=out_t,
        t_inside_c=out_t_inside,
        t_setpoint_c=out_t_setpoint,
        t_amb_c=out_t_amb,
        q_load_w=out_q_load,
        q_cool_w=out_q_cool,
        v_dot_command_m3s=out_v_command,
        v_dot_actual_m3s=out_v_actual,
        saturated=out_saturated,
    )
```

- [ ] **Step 4: Run the new tests to verify they pass**

```bash
pytest tests/test_sim_experiment.py::TestRunExperiment -q
```
Expected: `3 passed`.

- [ ] **Step 5: Run the full suite**

```bash
pytest tests/ -q
```
Expected: `60 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/sim/experiment.py tests/test_sim_experiment.py
git commit -m "feat: add closed-loop run_experiment with RK4 integration"
```

---

## Task 9: `compute_summary` and `compute_experiment_warnings` (TDD)

**Files:**
- Modify: `src/sim/experiment.py`
- Modify: `tests/test_sim_experiment.py`

- [ ] **Step 1: Append summary tests to `tests/test_sim_experiment.py`**

Append the following class to `tests/test_sim_experiment.py`:
```python
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
```

- [ ] **Step 2: Run the new tests to verify they fail**

```bash
pytest tests/test_sim_experiment.py::TestComputeSummary tests/test_sim_experiment.py::TestComputeExperimentWarnings -q
```
Expected: `ImportError: cannot import name 'compute_summary'`.

- [ ] **Step 3: Append `compute_summary` and `compute_experiment_warnings` to
  `src/sim/experiment.py`**

Append the following to `src/sim/experiment.py`:
```python
from src.units import m3s_to_cfm


def compute_summary(result: SimulationResult) -> dict[str, float]:
    """Returns peak/mean/RMS/min CFM, max excursion, settling time, saturation %.

    settling_time_s is the earliest time t* such that
    |T_inside(t) - T_setpoint| <= 0.5 °C for ALL t in [t*, end].
    Returns np.inf if no such t* exists.
    """
    cfm_command = np.array([m3s_to_cfm(v) for v in result.v_dot_command_m3s])
    excursion = np.abs(result.t_inside_c - result.t_setpoint_c)

    # Settling time: walk backwards to find the latest time the trace was
    # OUT of the band. The earliest settling time is the next sample after that.
    band = 0.5
    out_of_band = excursion > band
    if not np.any(out_of_band):
        settling_time_s = 0.0
    elif np.all(out_of_band):
        settling_time_s = float("inf")
    else:
        # Index of the last out-of-band sample
        last_bad = int(np.max(np.where(out_of_band)))
        if last_bad == len(result.t_s) - 1:
            settling_time_s = float("inf")
        else:
            settling_time_s = float(result.t_s[last_bad + 1])

    return {
        "peak_cfm": float(np.max(cfm_command)),
        "mean_cfm": float(np.mean(cfm_command)),
        "rms_cfm": float(np.sqrt(np.mean(cfm_command ** 2))),
        "min_commanded_cfm": float(np.min(cfm_command)),
        "max_excursion_c": float(np.max(excursion)),
        "settling_time_s": settling_time_s,
        "saturation_pct": float(100.0 * np.mean(result.saturated)),
    }


def compute_experiment_warnings(result: SimulationResult) -> list[str]:
    """Return human-readable warnings about a completed run.

    Warnings are NOT errors — the run produced a result. They flag suspicious
    or infeasible operating points to the user.
    """
    warnings: list[str] = []
    summary = compute_summary(result)

    if summary["saturation_pct"] > 50.0:
        warnings.append(
            f"Loop saturated {summary['saturation_pct']:.0f}% of run. "
            "Fan range is undersized for this scenario."
        )
    if summary["max_excursion_c"] > 1.0:
        warnings.append(
            f"Peak excursion from setpoint reached "
            f"{summary['max_excursion_c']:.2f} °C — controller cannot keep up."
        )
    if summary["settling_time_s"] == float("inf"):
        warnings.append("Loop never settled within ±0.5 °C of setpoint.")
    if (result.q_cool_w < 0).mean() > 0.05:
        n_negative = int((result.q_cool_w < 0).sum())
        warnings.append(
            f"Cooling power went negative for {n_negative} samples — "
            "supply air heated the enclosure. Check T_supply vs. T_inside."
        )
    if np.any(np.isnan(result.t_inside_c)):
        warnings.append(
            "Numerical instability: NaN in temperature trace. "
            "Reduce timestep or check inputs."
        )
    return warnings
```

- [ ] **Step 4: Run the new tests to verify they pass**

```bash
pytest tests/test_sim_experiment.py::TestComputeSummary tests/test_sim_experiment.py::TestComputeExperimentWarnings -q
```
Expected: `6 passed`.

- [ ] **Step 5: Run the full suite**

```bash
pytest tests/ -q
```
Expected: `66 passed`.

- [ ] **Step 6: Commit**

```bash
git add src/sim/experiment.py tests/test_sim_experiment.py
git commit -m "feat: add summary stats and experiment warnings"
```

---

## Task 10: Default factories in `defaults.py` and snapshot tests

**Files:**
- Modify: `defaults.py` (add 5 factory functions)
- Create: `tests/test_sim_defaults.py`

- [ ] **Step 1: Append the snapshot test file**

Write the following file at `tests/test_sim_defaults.py`:
```python
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
        # low-Q holds. ~50–60% saturation is expected and not a bug.
        assert summary["saturation_pct"] < 75.0

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
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
pytest tests/test_sim_defaults.py -q
```
Expected: `ImportError: cannot import name 'default_plant_params' from 'defaults'`.

- [ ] **Step 3: Append the new factory functions to `defaults.py`**

Append the following to `defaults.py` (after the existing `default_ambient` function):
```python
from src.constants import AIR_CP, AIR_DENSITY
from src.sim.actuator import FanParams
from src.sim.controller import PIDController
from src.sim.plant import PlantParams
from src.units import cfm_to_m3s


def default_t_setpoint_c() -> float:
    return 23.0


def default_t_supply_c() -> float:
    """Constant heat-exchanger coil leaving temperature."""
    return 18.0


def default_plant_params() -> PlantParams:
    enc = default_enclosure()
    amb = default_ambient()
    return PlantParams(
        thermal_capacitance_j_per_k=enc.thermal_capacitance,
        ua_value_w_per_k=amb.ua_value,
        air_cp=AIR_CP,
        air_density=AIR_DENSITY,
        t_supply_c=default_t_supply_c(),
    )


def default_fan_params() -> FanParams:
    return FanParams(
        tau_s=3.0,
        v_dot_min_m3s=cfm_to_m3s(30.0),    # HEPA filter floor
        v_dot_max_m3s=cfm_to_m3s(150.0),   # below optical-sensitivity ceiling
    )


def default_pid_controller() -> PIDController:
    """Spec-derived gains: 5 CFM/K, 0.5 CFM/(K·s), 10 CFM·s/K — converted to SI.
    Placeholders, will likely be retuned after observing first full runs."""
    return PIDController(
        kp=cfm_to_m3s(5.0),     # 5 CFM/K
        ki=cfm_to_m3s(0.5),     # 0.5 CFM/(K·s)
        kd=cfm_to_m3s(10.0),    # 10 CFM·s/K (numerically same factor)
        setpoint=default_t_setpoint_c(),
        v_min=cfm_to_m3s(30.0),
        v_max=cfm_to_m3s(150.0),
    )
```

- [ ] **Step 4: Run the snapshot tests to verify they pass**

```bash
pytest tests/test_sim_defaults.py -q
```
Expected: `3 passed`.

- [ ] **Step 5: Run the full suite**

```bash
pytest tests/ -q
```
Expected: `69 passed`.

- [ ] **Step 6: Commit**

```bash
git add defaults.py tests/test_sim_defaults.py
git commit -m "feat: add PID experiment default factories and snapshot tests"
```

---

## Task 11: Streamlit experiment panel

**Files:**
- Create: `src/ui/panel_pid_experiment.py`

This task has no automated tests (Streamlit UI is exercised manually in Task 13).

- [ ] **Step 1: Write the panel file**

Write the following file at `src/ui/panel_pid_experiment.py`:
```python
"""Streamlit panel for the PID experiment tab.

Renders scenario picker, advanced controls, run button, plots, summary stats,
and CSV download. Calls src.sim.experiment.run_experiment under the hood.
"""
from __future__ import annotations
import io
from datetime import datetime

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from defaults import (
    default_fan_params,
    default_pid_controller,
    default_t_setpoint_c,
    default_t_supply_c,
)
from src.constants import AIR_CP, AIR_DENSITY
from src.sim.actuator import FanParams
from src.sim.controller import PIDController
from src.sim.experiment import (
    SimulationResult,
    run_experiment,
    compute_summary,
    compute_experiment_warnings,
)
from src.sim.plant import PlantParams
from src.sim.scenarios import (
    laser_thermal_cycling,
    ambient_step,
    ambient_diurnal,
)
from src.units import cfm_to_m3s, m3s_to_cfm


SCENARIO_BUILDERS = {
    "A — Laser thermal cycling": laser_thermal_cycling,
    "B-sharp — Ambient step ±6.5 °C": ambient_step,
    "B-slow — Ambient diurnal half-sine (6 h)": ambient_diurnal,
}


def render_pid_experiment_panel(
    enclosure_thermal_capacitance_j_per_k: float,
    ua_value_w_per_k: float,
) -> None:
    """Render the PID experiment tab.

    The plant params are derived from the geometry/ambient panels in the
    Steady State tab so the user does not enter the same enclosure twice.
    """
    st.markdown(
        '<div class="section-header">PID EXPERIMENT</div>',
        unsafe_allow_html=True,
    )

    # ── Scenario picker ─────────────────────────────────────
    scenario_label = st.radio(
        "Disturbance scenario",
        options=list(SCENARIO_BUILDERS.keys()),
        index=0,
        horizontal=False,
    )

    # ── Advanced controls ───────────────────────────────────
    with st.expander("Advanced controller and plant parameters", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            kp = st.number_input("PID Kp", value=default_pid_controller().kp,
                                 min_value=0.0, step=0.0001, format="%.4f")
            ki = st.number_input("PID Ki", value=default_pid_controller().ki,
                                 min_value=0.0, step=0.0001, format="%.4f")
            kd = st.number_input("PID Kd", value=default_pid_controller().kd,
                                 min_value=0.0, step=0.0001, format="%.4f")
        with c2:
            tau_fan = st.number_input(
                "Fan time constant τ_fan (s)",
                value=default_fan_params().tau_s,
                min_value=0.1, step=0.5, format="%.1f",
            )
            t_supply = st.number_input(
                "Coil supply temp T_supply (°C)",
                value=default_t_supply_c(),
                min_value=0.0, max_value=30.0, step=0.5,
            )
            v_min_cfm = st.number_input(
                "Fan min CFM",
                value=m3s_to_cfm(default_fan_params().v_dot_min_m3s),
                min_value=0.0, step=5.0,
            )
            v_max_cfm = st.number_input(
                "Fan max CFM",
                value=m3s_to_cfm(default_fan_params().v_dot_max_m3s),
                min_value=1.0, step=10.0,
            )

    setpoint_c = default_t_setpoint_c()

    # ── Run button ──────────────────────────────────────────
    if st.button("Run experiment", type="primary"):
        scenario = SCENARIO_BUILDERS[scenario_label]()
        plant = PlantParams(
            thermal_capacitance_j_per_k=enclosure_thermal_capacitance_j_per_k,
            ua_value_w_per_k=ua_value_w_per_k,
            air_cp=AIR_CP,
            air_density=AIR_DENSITY,
            t_supply_c=t_supply,
        )
        fan = FanParams(
            tau_s=tau_fan,
            v_dot_min_m3s=cfm_to_m3s(v_min_cfm),
            v_dot_max_m3s=cfm_to_m3s(v_max_cfm),
        )
        pid = PIDController(
            kp=kp, ki=ki, kd=kd,
            setpoint=setpoint_c,
            v_min=cfm_to_m3s(v_min_cfm),
            v_max=cfm_to_m3s(v_max_cfm),
        )

        try:
            result = run_experiment(
                scenario=scenario,
                plant_params=plant,
                fan_params=fan,
                controller=pid,
                t_setpoint_c=setpoint_c,
            )
        except ValueError as e:
            st.error(f"Invalid inputs:\n{e}")
            return
        except RuntimeError as e:
            st.error(f"Simulation failed:\n{e}")
            return

        _render_result(result, fan, scenario.name)
    else:
        st.info("Configure parameters above (or accept defaults), then click Run.")


def _render_result(result: SimulationResult,
                   fan_params: FanParams,
                   scenario_name: str) -> None:
    summary = compute_summary(result)
    warnings = compute_experiment_warnings(result)

    if warnings:
        for w in warnings:
            st.warning(w)

    # ── Plot 1: temperatures ─────────────────────────────────
    fig_t = go.Figure()
    fig_t.add_trace(go.Scatter(
        x=result.t_s, y=result.t_inside_c, name="T_inside",
        line=dict(color="#00D4AA", width=2),
    ))
    fig_t.add_trace(go.Scatter(
        x=result.t_s, y=result.t_setpoint_c, name="T_setpoint",
        line=dict(color="#FF6B35", width=1, dash="dash"),
    ))
    fig_t.add_trace(go.Scatter(
        x=result.t_s, y=result.t_amb_c, name="T_ambient",
        line=dict(color="#7C8B9A", width=1),
    ))
    fig_t.update_layout(
        title="Temperatures (°C)",
        xaxis_title="time (s)", yaxis_title="°C",
        height=300, paper_bgcolor="#0D1117", plot_bgcolor="#0D1117",
        font=dict(color="#C9D1D9"),
    )
    st.plotly_chart(fig_t, use_container_width=True, theme=None)

    # ── Plot 2: fan CFM with limit bands ─────────────────────
    cmd_cfm = np.array([m3s_to_cfm(v) for v in result.v_dot_command_m3s])
    actual_cfm = np.array([m3s_to_cfm(v) for v in result.v_dot_actual_m3s])
    v_min_cfm = m3s_to_cfm(fan_params.v_dot_min_m3s)
    v_max_cfm = m3s_to_cfm(fan_params.v_dot_max_m3s)

    fig_v = go.Figure()
    # Shade outside the bands (above max and below min) so saturation is obvious
    y_top = max(cmd_cfm.max(), v_max_cfm) * 1.1
    y_bot = min(cmd_cfm.min(), v_min_cfm) * 0.9
    fig_v.add_hrect(y0=v_max_cfm, y1=y_top, fillcolor="#F0A830", opacity=0.10,
                    line_width=0)
    fig_v.add_hrect(y0=y_bot, y1=v_min_cfm, fillcolor="#F0A830", opacity=0.10,
                    line_width=0)
    fig_v.add_hline(y=v_max_cfm, line_dash="dash", line_color="#7C8B9A",
                    annotation_text="V_max")
    fig_v.add_hline(y=v_min_cfm, line_dash="dash", line_color="#7C8B9A",
                    annotation_text="V_min")
    fig_v.add_trace(go.Scatter(
        x=result.t_s, y=cmd_cfm, name="V_command",
        line=dict(color="#58A6FF", width=2),
    ))
    fig_v.add_trace(go.Scatter(
        x=result.t_s, y=actual_cfm, name="V_actual",
        line=dict(color="#00D4AA", width=1, dash="dot"),
    ))
    fig_v.update_layout(
        title="Fan airflow (CFM)",
        xaxis_title="time (s)", yaxis_title="CFM",
        height=300, paper_bgcolor="#0D1117", plot_bgcolor="#0D1117",
        font=dict(color="#C9D1D9"),
    )
    st.plotly_chart(fig_v, use_container_width=True, theme=None)

    # ── Plot 3: heat balance ─────────────────────────────────
    fig_q = go.Figure()
    fig_q.add_trace(go.Scatter(
        x=result.t_s, y=result.q_load_w, name="Q_load",
        line=dict(color="#F85149", width=2),
    ))
    fig_q.add_trace(go.Scatter(
        x=result.t_s, y=result.q_cool_w, name="Q_cool",
        line=dict(color="#58A6FF", width=2),
    ))
    fig_q.update_layout(
        title="Heat load vs cooling power (W)",
        xaxis_title="time (s)", yaxis_title="W",
        height=300, paper_bgcolor="#0D1117", plot_bgcolor="#0D1117",
        font=dict(color="#C9D1D9"),
    )
    st.plotly_chart(fig_q, use_container_width=True, theme=None)

    # ── Summary stats ────────────────────────────────────────
    st.markdown("### Summary statistics")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Peak CFM", f"{summary['peak_cfm']:.1f}")
        st.metric("Mean CFM", f"{summary['mean_cfm']:.1f}")
        st.metric("RMS CFM", f"{summary['rms_cfm']:.1f}")
    with c2:
        st.metric("Min commanded CFM", f"{summary['min_commanded_cfm']:.1f}")
        st.metric("Max |T_inside − SP|", f"{summary['max_excursion_c']:.2f} °C")
    with c3:
        if summary["settling_time_s"] == float("inf"):
            st.metric("Settle time (±0.5 °C)", "∞")
        else:
            st.metric("Settle time (±0.5 °C)", f"{summary['settling_time_s']:.0f} s")
        st.metric("Saturation %", f"{summary['saturation_pct']:.1f}%")

    # ── CSV download ─────────────────────────────────────────
    csv_buf = io.StringIO()
    csv_buf.write(
        "t_s,t_inside_c,t_setpoint_c,t_amb_c,q_load_w,q_cool_w,"
        "v_dot_command_cfm,v_dot_actual_cfm,saturated\n"
    )
    for i in range(len(result.t_s)):
        csv_buf.write(
            f"{result.t_s[i]:.4f},"
            f"{result.t_inside_c[i]:.6f},"
            f"{result.t_setpoint_c[i]:.6f},"
            f"{result.t_amb_c[i]:.6f},"
            f"{result.q_load_w[i]:.4f},"
            f"{result.q_cool_w[i]:.4f},"
            f"{m3s_to_cfm(result.v_dot_command_m3s[i]):.4f},"
            f"{m3s_to_cfm(result.v_dot_actual_m3s[i]):.4f},"
            f"{int(result.saturated[i])}\n"
        )
    st.download_button(
        label="⬇ Download CSV",
        data=csv_buf.getvalue(),
        file_name=f"experiment_{scenario_name}_"
                  f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )
```

- [ ] **Step 2: Run the full test suite to confirm nothing broke**

```bash
pytest tests/ -q
```
Expected: `69 passed`.

- [ ] **Step 3: Commit**

```bash
git add src/ui/panel_pid_experiment.py
git commit -m "feat: add Streamlit panel for PID experiment with plots and CSV download"
```

---

## Task 12: Wrap `app.py` in tabs

**Files:**
- Modify: `app.py`

The existing layout (sidebar + three columns) becomes the contents of the first tab. The new PID experiment panel becomes the second tab.

- [ ] **Step 1: Read the current `app.py` so you know what you're refactoring**

```bash
cat app.py
```
Take note of the existing structure: sidebar (lines ~42–93), then `col_inputs, col_schematic, col_results = st.columns([3, 5, 3])` (line 96), then the three column blocks.

- [ ] **Step 2: Modify `app.py`**

Edit `app.py` to wrap the existing three-column layout in `st.tabs(["Steady State", "PID Experiment"])`. Keep the sidebar OUTSIDE the tabs (it controls global solve mode and units, which apply to both tabs). The PID tab calls `render_pid_experiment_panel` with the enclosure thermal capacitance and UA value derived from the same input panels.

Open `app.py` and apply these specific changes:

(a) Add an import near the top, after the other ui imports:
```python
from src.ui.panel_pid_experiment import render_pid_experiment_panel
```

(b) Replace the line `col_inputs, col_schematic, col_results = st.columns([3, 5, 3])` and EVERYTHING below it (the existing column blocks) with:
```python
# ── Tabs: Steady State (existing) and PID Experiment (new) ──
tab_steady, tab_pid = st.tabs(["Steady State", "PID Experiment"])

with tab_steady:
    col_inputs, col_schematic, col_results = st.columns([3, 5, 3])

    with col_inputs:
        st.markdown(
            '<div class="section-header">SYSTEM PARAMETERS</div>',
            unsafe_allow_html=True,
        )
        geo = render_geometry_panel(use_imperial)
        loads_input = render_loads_panel()
        ambient_input = render_ambient_panel()
        cooling_input = render_cooling_panel(solve_mode)

    # ── Build models ───────────────────────────────────────
    enclosure = Enclosure(
        length_m=geo["length_m"],
        width_m=geo["width_m"],
        height_m=geo["height_m"],
        internal_thermal_mass=geo["internal_thermal_mass"],
    )

    loads = HeatLoads(
        baseline_load_w=loads_input["baseline_load_w"],
        additional_loads_w=loads_input["additional_loads_w"],
    )

    # Handle ACH → UA conversion if needed
    ua_value = ambient_input["ua_value"]
    if ambient_input.get("ua_mode") == "Air changes per hour (ACH)":
        ach = ambient_input["ua_value"]
        ua_value = ach * enclosure.volume_m3 * AIR_DENSITY * AIR_CP / 3600.0

    ambient = AmbientConditions(
        T_ambient_c=ambient_input["T_ambient_c"],
        T_setpoint_c=ambient_input["T_setpoint_c"],
        T_ambient_variation_c=ambient_input["T_ambient_variation_c"],
        ua_value=ua_value,
    )

    cooling = CoolingPlant(
        coil_approach_temp_c=cooling_input["coil_approach_temp_c"],
        coil_max_capacity_w=cooling_input["coil_max_capacity_w"],
        chilled_water_temp_c=cooling_input["chilled_water_temp_c"],
        delta_t_air_c=cooling_input["delta_t_air_c"],
        delta_t_water_c=cooling_input["delta_t_water_c"],
    )

    # ── Run solvers ────────────────────────────────────────
    q_total = loads.total_load_w

    air_result = solve_airflow(
        q_total_w=q_total, delta_t_air_c=cooling.delta_t_air_c,
    )

    coolant_result = solve_coolant_flow(
        q_total_w=q_total, delta_t_water_c=cooling.delta_t_water_c,
    )

    coil_result = solve_coil_leaving_temp(
        q_total_w=q_total,
        airflow_kgs=air_result.airflow_kgs,
        return_air_temp_c=ambient.T_setpoint_c,
    )

    heater_result = solve_heater_requirement(
        q_load_w=q_total,
        ua_value=ambient.ua_value,
        ambient_temp_c=ambient.T_ambient_low,
        setpoint_c=ambient.T_setpoint_c,
    )

    coil_utilization = (q_total / cooling.coil_max_capacity_w) * 100.0

    warnings = compute_warnings(
        coil_utilization_pct=coil_utilization,
        heater_required_w=heater_result.heater_required_w,
    )

    with col_schematic:
        st.markdown(
            '<div class="section-header">SYSTEM SCHEMATIC</div>',
            unsafe_allow_html=True,
        )
        cfm = m3s_to_cfm(air_result.airflow_m3s)
        lpm = kgs_to_lpm(coolant_result.coolant_kgs)

        fig = render_schematic(
            enclosure_temp_c=ambient.T_setpoint_c,
            supply_temp_c=coil_result.coil_leaving_temp_c,
            return_temp_c=ambient.T_setpoint_c,
            ambient_temp_c=ambient.T_ambient_c,
            chilled_water_temp_c=cooling.chilled_water_temp_c,
            airflow_cfm=cfm,
            coolant_lpm=lpm,
            heat_load_w=q_total,
            ua_value=ambient.ua_value,
        )
        st.plotly_chart(fig, use_container_width=True, theme=None)

        render_physics_card(
            q_total_w=q_total,
            delta_t_air_c=cooling.delta_t_air_c,
            delta_t_water_c=cooling.delta_t_water_c,
            ua_value=ambient.ua_value,
            ambient_temp_c=ambient.T_ambient_c,
            setpoint_c=ambient.T_setpoint_c,
            airflow_cfm=cfm,
            airflow_m3s=air_result.airflow_m3s,
            coolant_lpm=lpm,
            coil_leaving_temp_c=coil_result.coil_leaving_temp_c,
            thermal_capacitance=enclosure.thermal_capacitance,
            volume_m3=enclosure.volume_m3,
        )

    with col_results:
        render_results_panel(
            airflow_m3s=air_result.airflow_m3s,
            coolant_kgs=coolant_result.coolant_kgs,
            coil_utilization_pct=coil_utilization,
            heater_required_w=heater_result.heater_required_w,
            coil_leaving_temp_c=coil_result.coil_leaving_temp_c,
            warnings=warnings,
            solve_mode=solve_mode,
        )

with tab_pid:
    render_pid_experiment_panel(
        enclosure_thermal_capacitance_j_per_k=enclosure.thermal_capacitance,
        ua_value_w_per_k=ambient.ua_value,
    )
```

The key changes:
- Original three-column layout is now indented inside `with tab_steady:`.
- The `enclosure` and `ambient` model objects (built inside `tab_steady`) are reused inside `tab_pid` to share inputs across tabs. Streamlit re-runs the whole script on any input change, so both tabs see the latest values.
- No other behavior of the steady-state tab changes.

- [ ] **Step 3: Run the full test suite (existing solver tests must still pass)**

```bash
pytest tests/ -q
```
Expected: `69 passed`.

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: wrap app in tabs and mount PID experiment panel"
```

---

## Task 13: Manual smoke test

**Files:** none (no commits)

This is a manual verification step — the engineer must launch Streamlit and click around. There's no automated test for the UI in v1.

- [ ] **Step 1: Launch the app**

```bash
streamlit run app.py
```
Expected: browser opens to the app at `http://localhost:8501`.

- [ ] **Step 2: Verify the Steady State tab still works**

In the browser:
- Confirm the "Steady State" tab loads with the same layout as before (sidebar, three columns: SYSTEM PARAMETERS, SYSTEM SCHEMATIC, COMPUTED RESULTS).
- Move the geometry sliders, change the heat load, change ambient — confirm numbers update as before.
- Confirm no errors in the terminal where Streamlit is running.

- [ ] **Step 3: Switch to the PID Experiment tab**

- Click "PID Experiment" tab.
- Confirm scenario picker shows three options (A, B-sharp, B-slow).
- Confirm the "Advanced" expander is collapsed by default.
- Expand it and verify the inputs (Kp, Ki, Kd, τ_fan, T_supply, V_min CFM, V_max CFM).

- [ ] **Step 4: Run Scenario A and confirm output**

- Select "A — Laser thermal cycling" (default).
- Click "Run experiment".
- Confirm three plots render: temperatures, fan CFM, heat balance.
- Confirm the Summary statistics block shows seven numbers.
- Confirm there's a "⬇ Download CSV" button.
- The simulation should complete in well under a second.

- [ ] **Step 5: Run Scenario B-sharp and confirm**

- Select "B-sharp — Ambient step ±6.5 °C".
- Click "Run experiment".
- Confirm the temperatures plot shows T_amb stepping up at ~60 s, holding, then stepping back down.

- [ ] **Step 6: Run Scenario B-slow and confirm**

- Select "B-slow — Ambient diurnal half-sine (6 h)".
- Click "Run experiment".
- Confirm the temperatures plot shows T_amb tracing a smooth half-sine over 6 h on the time axis.

- [ ] **Step 7: Trigger an input validation error**

- Open the Advanced expander.
- Set "Coil supply temp T_supply (°C)" to 25.0 (above setpoint).
- Click "Run experiment".
- Expected: a red error box appears stating that supply temp must be below setpoint. No crash.

- [ ] **Step 8: Stop Streamlit (`Ctrl+C`)**

If all manual checks passed, this task is done. No commit (no files changed).

---

## Final commit summary

After Task 13, the branch should have these commits beyond the spec:

```
feat: scaffold src/sim package for PID experiment extension
feat: add lumped-capacitance plant ODE for PID experiment
feat: add first-order fan actuator with clamping
feat: add PID controller with conditional-integration anti-windup
feat: add scalar RK4 integrator
feat: add three preset disturbance scenarios with linear interpolation
feat: add SimulationResult dataclass and experiment input validation
feat: add closed-loop run_experiment with RK4 integration
feat: add summary stats and experiment warnings
feat: add PID experiment default factories and snapshot tests
feat: add Streamlit panel for PID experiment with plots and CSV download
feat: wrap app in tabs and mount PID experiment panel
```

**Final test count:** 30 (existing) + 31 (5+5+5+3+5+8 unit/integration) + 3 (snapshot) = **64 tests**, all passing in well under a second.

**Final file count:** 13 new files in `src/sim/` and `tests/`, 2 modified files (`defaults.py`, `app.py`), spec already committed in a prior commit.
