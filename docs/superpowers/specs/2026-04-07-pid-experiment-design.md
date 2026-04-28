# PID Control Extension and Experiment Harness — Design

**Date:** 2026-04-07
**Branch:** `feat/separate-ambient-setpoint` (will branch off for implementation)
**Status:** Design — awaiting user approval before implementation plan

## Goal

Add a closed-loop, time-domain simulation capability to the existing steady-state thermal analyzer so the user can answer one specific question:

> **What CFM range does the fan have to command, under realistic disturbance scenarios, in order for a PID controller to hold the enclosure setpoint when the heat exchanger is held at a constant supply temperature?**

This is a procurement question. The deliverable is the *commanded CFM trace* (peak, mean, RMS, min, saturation %) under a fixed set of disturbance scenarios. Output feeds fan / HEPA filter sizing decisions.

## Non-goals (deferred to v2)

- Multi-sensor / spatial enclosure modeling. The "points of interest" idea is parked; v1 is single lumped node.
- Sensor noise, lag, or quantization (ideal sensor in v1).
- Auto-tuning (Ziegler–Nichols, relay feedback, etc.).
- Parameter sweeps / Monte Carlo over PID gains.
- Side-by-side comparison of all three scenarios in one view.
- Loading custom CSV traces for ambient or load.
- Validation mode that overlays measured thermocouple data.

These are intentionally postponed and explicitly out of scope for v1.

## Physical model

### Plant
Single lumped capacitance ODE:
```
C_e · dT_inside/dt = Q_load(t) − Q_cool(t) + UA · (T_amb(t) − T_inside)
```
- `C_e` = `Enclosure.thermal_capacitance` from existing model (`ρ·V·c_p + C_internal`).
- `Q_cool(t) = ρ · V_dot(t) · c_p · (T_inside − T_supply)`. Bilinear in `V_dot` and `T_inside`. Can go negative if `T_inside < T_supply`; this is physically correct (supply air heats a too-cold enclosure) and is left unclamped.
- `T_supply` is the constant heat-exchanger coil leaving temperature, default **18 °C**, user-configurable.

### Actuator
Fan modeled as first-order lag with hard physical clamps:
```
V_actual(t+dt) = V_actual(t) + (V_command − V_actual(t)) · (1 − exp(−dt / τ_fan))
V_actual ∈ [V_min, V_max]
```
- `τ_fan` default **3 s**.
- `V_min` default **30 CFM** (HEPA filter floor).
- `V_max` default **150 CFM** (well below the optical-sensitivity ceiling discussed in 2026-04-07 meeting).

### Sensor
Ideal in v1: `T_measured = T_inside`. No noise, no lag.

### Controller
Standard parallel PID with conditional-integration anti-windup:
- `error = T_inside − T_setpoint` (positive error → controller increases CFM).
- Output: `V_command = Kp·error + Ki·∫error dt + Kd · d(T_inside)/dt`.
- **Derivative on measurement**, not on error, to avoid setpoint kick.
- **Anti-windup**: skip the integral update on any tick where the unsaturated output is at/above `V_max` with positive error, or at/below `V_min` with negative error.
- **Initialization**: `controller.initialize(V_init)` sets `integral = V_init`. With `error=0` at t=0, the controller outputs exactly `V_init` (bumpless start).
- Default gains (placeholders, will retune after first full run): `Kp = 5 CFM/K`, `Ki = 0.5 CFM/(K·s)`, `Kd = 10 CFM·s/K`.
- All user-facing gains are positive numbers.

### Disturbance scenarios

| Name | Q_load profile | T_amb profile | Duration | dt |
|---|---|---|---|---|
| **A — Laser thermal cycling** | 3× (60 s ramp 0→100 W, 5 min hold, 60 s ramp 100→0 W, 5 min hold) | constant 23.5 °C | 33 min | 0.5 s |
| **B-sharp — Ambient step** | constant 100 W | 23.5 → 30 °C over 60 s, hold 15 min, 30 → 23.5 °C over 60 s, hold 15 min | 32 min | 0.5 s |
| **B-slow — Diurnal drift** | constant 100 W | half-sine 23.5 → 30 → 23.5 °C over 6 h, pre-sampled to ~100 piecewise-linear segments | 6 h | 5 s |

Scenarios are pure data (`Scenario` dataclass containing `tuple[ScenarioPoint, ...]`) with linear interpolation between sample points. Each preset is a function returning a fresh `Scenario`. Scenarios run independently — no combined runs in v1.

## Architecture

### Two-tier separation
- `src/sim/` — pure simulation logic. No Streamlit imports, no plotting. Reusable from a script or notebook.
- `src/ui/panel_pid_experiment.py` — thin Streamlit panel that builds inputs, calls `run_experiment()`, renders Plotly figures.
- `app.py` — wraps existing single-page layout in `st.tabs(["Steady State", "PID Experiment"])`. Existing steady-state tab is unchanged in behavior; only the outer container changes.

### Module layout
```
src/sim/
  __init__.py
  plant.py        # PlantParams, dT_inside_dt
  actuator.py     # FanParams, fan_step
  controller.py   # PIDController dataclass
  scenarios.py    # ScenarioPoint, Scenario, three preset constructors
  integrator.py   # rk4_step
  experiment.py   # SimulationResult, run_experiment, compute_summary,
                  # validate_experiment_inputs, compute_experiment_warnings
src/ui/
  panel_pid_experiment.py
app.py            # add st.tabs wrapper
tests/
  test_sim_plant.py
  test_sim_actuator.py
  test_sim_controller.py
  test_sim_integrator.py
  test_sim_scenarios.py
  test_sim_experiment.py
  test_sim_defaults.py
```

### State management
State lives in exactly three places:
1. `PIDController.integral` and `PIDController.prev_measurement` (mutated by `step()`).
2. `V_actual` local variable in `run_experiment()` (between fan-step calls).
3. `T_inside` local variable in `run_experiment()` (between RK4 calls).

Everything else is a pure function of inputs. No globals, no `st.session_state` in v1. Each Run-button click constructs fresh objects and integrates from t=0 — no cross-run state leakage.

## Component interfaces

### `src/sim/plant.py`

```python
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
) -> float: ...
```

### `src/sim/actuator.py`

```python
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
) -> float: ...
```

### `src/sim/controller.py`

```python
@dataclass
class PIDController:
    kp: float
    ki: float
    kd: float
    setpoint: float
    v_min: float
    v_max: float
    integral: float = 0.0
    prev_measurement: float | None = None

    def initialize(self, v_init_m3s: float) -> None: ...
    def step(self, measurement_c: float, dt_s: float) -> float: ...
```

### `src/sim/scenarios.py`

```python
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

    def q_load_at(self, t_s: float) -> float: ...
    def t_amb_at(self, t_s: float) -> float: ...

def laser_thermal_cycling(t_amb_c: float = 23.5) -> Scenario: ...
def ambient_step(q_load_w: float = 100.0) -> Scenario: ...
def ambient_diurnal(q_load_w: float = 100.0) -> Scenario: ...
```

Out-of-range times (`t < 0` or `t > duration_s`) clamp to the nearest endpoint rather than raise.

### `src/sim/integrator.py`

```python
def rk4_step(
    f: Callable[[float, float], float],
    y: float,
    t: float,
    dt: float,
) -> float: ...
```

Scalar-only (we have one state variable). Caller closes over `V_actual` so the plant ODE sees a held value across the four sub-steps (zero-order hold).

### `src/sim/experiment.py`

```python
@dataclass
class SimulationResult:
    t_s: np.ndarray
    t_inside_c: np.ndarray
    t_setpoint_c: np.ndarray   # constant
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
) -> None: ...   # raises ValueError on invalid input

def run_experiment(
    scenario: Scenario,
    plant_params: PlantParams,
    fan_params: FanParams,
    controller: PIDController,
    t_setpoint_c: float,
) -> SimulationResult: ...

def compute_summary(result: SimulationResult) -> dict[str, float]:
    """Returns: peak_cfm, mean_cfm, rms_cfm, min_commanded_cfm,
    max_excursion_c, settling_time_s, saturation_pct.

    settling_time_s is defined as the earliest time t* such that
    |T_inside(t) − T_setpoint| <= 0.5 °C for ALL t in [t*, duration_s].
    Returns np.inf if no such t* exists. Initial samples (before any
    disturbance has propagated) count toward 'settled' as long as the
    trace stays inside the band thereafter.
    """

def compute_experiment_warnings(result: SimulationResult) -> list[str]: ...
```

`run_experiment()` is the only function the UI panel calls for the simulation itself.

## Data flow

### Initialization (before the loop)

```
1. Read scenario t=0 conditions:
     Q_load_init = scenario.q_load_at(0.0)
     T_amb_init  = scenario.t_amb_at(0.0)

2. Solve initial steady-state CFM (closed form):
     V_init = (Q_load_init + UA·(T_amb_init − T_setpoint))
              / (ρ · c_p · (T_setpoint − T_supply))
     Clamp to [V_min, V_max] and emit a warning if clamped.

3. Set initial state:
     T_inside = T_setpoint
     V_actual = V_init
     controller.initialize(V_init)

4. Allocate output buffers (Python lists; converted to np.ndarray at end).
```

### Per-timestep loop

For `t` in `np.arange(0, scenario.duration_s, scenario.timestep_s)`:

```
STEP 1  q_load = scenario.q_load_at(t)
        t_amb  = scenario.t_amb_at(t)

STEP 2  measurement = T_inside              # ideal sensor

STEP 3  V_command = controller.step(measurement, dt)

STEP 4  V_actual = fan_step(V_actual, V_command, dt, fan_params)

STEP 5  def plant_ode(t_sub, T):
          return dT_inside_dt(
            t_inside_c=T,
            v_dot_m3s=V_actual,                  # captured, frozen across step
            q_load_w=scenario.q_load_at(t_sub),  # varies inside RK4
            t_amb_c=scenario.t_amb_at(t_sub),    # varies inside RK4
            params=plant_params,
          )
        T_inside = rk4_step(plant_ode, T_inside, t, dt)

STEP 6  q_cool_now = ρ · V_actual · c_p · (T_inside − T_supply)
        sat = (V_command <= V_min) or (V_command >= V_max)
        Append (t, T_inside, t_amb, q_load, q_cool_now,
                V_command, V_actual, sat) to output buffers.
```

### Termination

Convert output buffers to `np.ndarray`, return `SimulationResult`. Summary computation happens separately in `compute_summary()`.

### Subtleties

- **Zero-order hold on V_actual inside RK4**: the controller updates once per timestep (digital reality), so its output is constant across the four RK4 sub-steps. Disturbances (`q_load`, `t_amb`) are *known time functions* and are evaluated at each sub-step for accuracy.
- **Saturation flag uses `V_command`, not `V_actual`**: the question we want to answer is "did the controller *want* to push past the limit?" After first-order lag, `V_actual` may still be ramping and never quite reach `V_command` within one step.

## Error handling

### Hard errors (input validation, before run)

`validate_experiment_inputs()` raises `ValueError` on any of:

| Check | Message |
|---|---|
| `t_supply_c >= t_setpoint_c` | "Coil supply temp must be below setpoint — cannot cool." |
| `v_dot_max <= v_dot_min` | "Fan max CFM must exceed min CFM." |
| `v_dot_min < 0` | "Fan min CFM cannot be negative." |
| `tau_s <= 0` | "Fan time constant must be positive." |
| `kp < 0 or ki < 0 or kd < 0` | "PID gains must be non-negative." |
| `thermal_capacitance_j_per_k <= 0` | "Thermal capacitance must be positive." |
| `ua_value_w_per_k < 0` | "UA value cannot be negative." |
| `timestep_s <= 0 or duration_s <= 0` | "Scenario timestep and duration must be positive." |
| `timestep_s > duration_s` | "Timestep must be smaller than duration." |

The UI panel catches these, packages all messages into a single `st.error()` box, and aborts the run.

### Soft warnings (after run)

`compute_experiment_warnings()` returns a `list[str]`:

| Condition | Warning |
|---|---|
| `V_init` was clamped at init | "Initial steady-state CFM was outside fan limits — operating point unreachable." |
| `result.saturated.mean() > 0.5` | "Loop saturated more than 50% of run. Fan range is undersized." |
| `max_excursion_c > 1.0` | "Peak excursion from setpoint exceeded 1 °C." |
| `settling_time_s == np.inf` | "Loop never settled within ±0.5 °C of setpoint." |
| `(result.q_cool_w < 0).mean() > 0.05` (more than 5% of samples) | "Cooling power went negative — supply air heated the enclosure." |
| `np.any(np.isnan(result.t_inside_c))` | "Numerical instability: NaN in temperature trace." |

Displayed as a yellow info box above the plots in the panel.

### Defensive bounds

Inside `run_experiment()`, after each RK4 step:
```python
if not np.isfinite(T_inside):
    raise RuntimeError(
        f"Plant integration produced non-finite value at t={t:.1f}s..."
    )
```

The UI panel wraps `run_experiment()` in a top-level try/except that converts unexpected exceptions to `st.error()` with the traceback, rather than crashing the app.

### Streamlit re-run safety

- Each Run-button click constructs fresh objects.
- No `st.session_state` use in v1 — the panel function holds the last `SimulationResult` in a local variable. Streamlit re-runs (e.g., from sliders in another tab) re-render the panel but do not re-run the simulation; the simulation runs only when the user clicks Run.
- Until the user clicks Run, the plot area shows a placeholder.

## UI

### Tab structure

```python
# app.py
tab_steady, tab_pid = st.tabs(["Steady State", "PID Experiment"])
with tab_steady:
    # existing layout, unchanged in behavior
with tab_pid:
    render_pid_experiment_panel(geo, loads, ambient, cooling)
```

Inputs from the existing Geometry / Heat Loads / Cooling / Ambient panels are shared with the PID tab so the user doesn't enter the same enclosure twice.

### Experiment tab layout

```
┌─ Scenario picker (radio) ──────────────────────────────────┐
│  ◉ A: Laser thermal cycling (3× 0↔100 W)                   │
│  ○ B-sharp: Ambient step ±6.5 °C in 60 s                    │
│  ○ B-slow:  Ambient diurnal half-sine (6 h)                 │
└────────────────────────────────────────────────────────────┘

   [ ▶ Run experiment ]      [ ⬇ Download CSV ]   (CSV button
                                                  appears after run)

▼ Advanced (expander, collapsed by default)
   • PID gains: Kp, Ki, Kd
   • Fan time constant τ_fan
   • Coil supply temp T_supply
   • Fan limits V_dot_min, V_dot_max

──────────────── results (visible after Run) ────────────────

[Plot 1]  T_inside, T_setpoint, T_amb           (°C vs time)
[Plot 2]  Fan CFM command vs actual + bands     (CFM vs time,
                                                 V_min/V_max shaded)
[Plot 3]  Q_load and Q_cool                     (W vs time)

┌─ Summary stats ────────────────────────────────┐
│  Peak CFM:                XX.X CFM             │
│  Mean CFM:                XX.X CFM             │
│  RMS CFM:                 XX.X CFM             │
│  Min commanded CFM:       XX.X CFM             │
│  Max |T_inside − SP|:     X.XX °C              │
│  Time to settle (±0.5 °C): XX s                │
│  Saturation %:            X.X %                │
└────────────────────────────────────────────────┘

[Warnings, if any, in a yellow info box]
```

### Plotting

- All three plots are Plotly `Figure` objects rendered with `st.plotly_chart(fig, use_container_width=True, theme=None)` to match the existing schematic.
- Plots share the x-axis (time in seconds, automatically formatted to minutes/hours for long scenarios).
- Plot 2 draws two horizontal lines at `V_min` and `V_max` (dashed, muted color), with the region OUTSIDE those bounds (above `V_max`, below `V_min`) lightly fill-shaded. This makes it visually obvious when `V_command` clips.

### CSV download

After a successful run, a `st.download_button` appears that exports a single CSV with columns:
```
t_s, t_inside_c, t_setpoint_c, t_amb_c, q_load_w, q_cool_w,
v_dot_command_cfm, v_dot_actual_cfm, saturated
```
Filename: `experiment_{scenario.name}_{timestamp}.csv`.

## Testing strategy

**~34 new tests across 7 files**, all under 1 s combined runtime, no new dev dependencies.

### Layer 1 — Pure-function unit tests

- `test_sim_plant.py` (5 tests): equilibrium, signs of dT/dt under heat/cool, Q_cool linearity in V_dot, sign of Q_cool when supply > inside.
- `test_sim_actuator.py` (5 tests): no-change-at-command, first-order lag at one tau (≈63%), clamps above/below, dt=0 no-op.
- `test_sim_controller.py` (5 tests): initialize outputs V_init, P-only proportional response, anti-windup at max, anti-windup at min, derivative on measurement no setpoint kick.
- `test_sim_integrator.py` (3 tests): RK4 exact for constant derivative, matches analytic for exponential decay, more accurate than Euler for nonlinear ODE.
- `test_sim_scenarios.py` (5 tests): laser cycling endpoints, ambient step initial/peak, diurnal peak at midpoint, linear interpolation, out-of-range clamping.

### Layer 2 — Closed-loop integration tests

`test_sim_experiment.py`:
- `test_no_disturbance_stays_at_setpoint` — most important single test in the suite.
- `test_small_ambient_step_recovers_to_setpoint`
- `test_peak_cfm_within_bounds`
- `test_run_returns_correct_array_shapes`
- `test_compute_summary_keys`
- `test_compute_summary_settling_time_inf_when_never_settles`
- `test_validation_rejects_t_supply_above_setpoint`
- `test_validation_rejects_negative_gains`

### Layer 3 — Defaults snapshot tests (regression guard)

`test_sim_defaults.py`:
- One test per preset scenario at default params, asserting loose plausible-range bounds on `peak_cfm`, `max_excursion_c`, `saturation_pct`.
- Ranges are deliberately loose — their job is to fail loudly on a sign flip or unit error, not to nail exact numbers.

### Not tested in v1
- Streamlit UI rendering (no `AppTest` framework).
- Plot output (we trust Plotly).
- Performance / timing (longest scenario is ~4320 steps, runs in well under a second).

### TDD note
The implementation plan that comes from `writing-plans` will sequence tests-first within each module (write `test_dT_dt_zero_at_equilibrium` before `dT_inside_dt`, etc.).

## Physics sanity check (for the user)

With current defaults (`C_e ≈ 53 kJ/K`, `UA = 2 W/K`, `Q_load = 100 W`, `T_supply = 18 °C`, `T_setpoint = 23 °C`), the plant is **extremely sluggish and naturally stable**:

- Open-loop time constant `τ = C_e/UA ≈ 7.4 hours`.
- A 100 W heat load on the unaided plant produces `dT/dt ≈ 0.0019 K/s` — ~9 minutes for a 1 K drift.
- At constant CFM, cooling is naturally proportional to `(T_inside − T_supply)`, so the loop has open-loop negative feedback before the PID even acts.

**Implication:** v1 simulation results are likely to confirm that *the system is forgiving and a modest fan range is sufficient*. That is itself a valuable procurement finding (Mohammad doesn't need an aggressive fan or sophisticated tuning), but it means experiment plots will look "uneventful" — small excursions, modest CFM swings — unless we deliberately stress the plant. Levers for stressing it later: lower `C_e`, higher `UA`, larger ambient steps, or aggressive `T_setpoint` changes.

## Open questions

None — all clarifying questions resolved during the brainstorming session.

## Out-of-scope items captured for v2

- Multi-sensor / spatial thermal model (revisit if real thermocouple data shows spatial gradients).
- Sensor noise / lag / quantization (needed for "validation against measured data" mode).
- Auto-tuning (Ziegler–Nichols, relay feedback, MPC).
- Side-by-side scenario comparison view.
- Custom CSV trace loading.
- Parameter sweeps / Monte Carlo over PID gains.
- "Combined worst case" scenario that runs the laser ramp on top of an ambient drift simultaneously.
