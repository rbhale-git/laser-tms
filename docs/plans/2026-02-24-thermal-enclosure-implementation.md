# Thermal Enclosure Analyzer — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an MVP Streamlit dashboard that computes steady-state thermal sizing for a quantum lab enclosure with "Precision Instrument" dark UI aesthetic.

**Architecture:** Layered model/solver/UI. Pure Python physics (no Streamlit dependency), dataclass models, explicit solve mode selection. Streamlit UI with custom CSS for dark instrument theme, Plotly for system schematic.

**Tech Stack:** Python 3.11+, Streamlit, Plotly, NumPy, pytest

**Design doc:** `docs/plans/2026-02-24-thermal-enclosure-design.md`

---

### Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `src/__init__.py`
- Create: `src/ui/__init__.py`
- Create: `tests/__init__.py`
- Create: `.streamlit/config.toml`
- Create: `.gitignore`

**Step 1: Create requirements.txt**

```
streamlit>=1.30.0
plotly>=5.18.0
numpy>=1.26.0
pytest>=7.4.0
```

**Step 2: Create package init files**

`src/__init__.py` — empty file
`src/ui/__init__.py` — empty file
`tests/__init__.py` — empty file

**Step 3: Create Streamlit dark theme config**

`.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#00D4AA"
backgroundColor = "#0D1117"
secondaryBackgroundColor = "#161B22"
textColor = "#E6EDF3"
font = "sans serif"

[server]
headless = true
```

**Step 4: Create .gitignore**

```
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
dist/
build/
.venv/
venv/
```

**Step 5: Install dependencies**

Run: `pip install -r requirements.txt`

**Step 6: Commit**

```bash
git add requirements.txt src/__init__.py src/ui/__init__.py tests/__init__.py .streamlit/config.toml .gitignore
git commit -m "chore: scaffold project structure and dependencies"
```

---

### Task 2: Constants Module

**Files:**
- Create: `src/constants.py`

**Step 1: Write constants**

```python
"""Physical constants and conversion factors for thermal analysis."""

# Air properties at ~20-25°C, 1 atm
AIR_CP = 1005.0        # J/(kg·K) - specific heat capacity
AIR_DENSITY = 1.19      # kg/m³ - density at ~23°C

# Water properties at ~15-20°C
WATER_CP = 4186.0       # J/(kg·K) - specific heat capacity
WATER_DENSITY = 998.0    # kg/m³

# Length conversions
FT_TO_M = 0.3048
M_TO_FT = 1.0 / FT_TO_M

# Volume conversions
FT3_TO_M3 = FT_TO_M ** 3
M3_TO_FT3 = M_TO_FT ** 3

# Flow conversions
M3S_TO_CFM = 2118.88    # 1 m³/s ≈ 2119 CFM
CFM_TO_M3S = 1.0 / M3S_TO_CFM

# Liquid flow conversions
KGS_TO_LPM_WATER = 60.0 / WATER_DENSITY * 1000.0  # kg/s → L/min
LPM_TO_GPM = 0.264172   # L/min → US gallons/min
GPM_TO_LPM = 1.0 / LPM_TO_GPM

# Temperature (offsets only — °C and K have same scale)
# No conversion needed for ΔT; only for absolute if needed
CELSIUS_TO_KELVIN_OFFSET = 273.15
```

**Step 2: Commit**

```bash
git add src/constants.py
git commit -m "feat: add physical constants and conversion factors"
```

---

### Task 3: Unit Conversion Helpers + Tests (TDD)

**Files:**
- Create: `src/units.py`
- Create: `tests/test_units.py`

**Step 1: Write the failing tests**

`tests/test_units.py`:
```python
"""Tests for unit conversion helpers."""
import pytest
from src.units import (
    ft_to_m, m_to_ft,
    ft3_to_m3, m3_to_ft3,
    cfm_to_m3s, m3s_to_cfm,
    kgs_to_lpm, lpm_to_gpm, gpm_to_lpm,
)


class TestLengthConversions:
    def test_ft_to_m(self):
        assert ft_to_m(1.0) == pytest.approx(0.3048, rel=1e-4)

    def test_m_to_ft(self):
        assert m_to_ft(1.0) == pytest.approx(3.28084, rel=1e-4)

    def test_ft_m_roundtrip(self):
        original = 10.0
        assert m_to_ft(ft_to_m(original)) == pytest.approx(original, rel=1e-9)


class TestVolumeConversions:
    def test_ft3_to_m3(self):
        # 100 ft³ ≈ 2.8317 m³
        assert ft3_to_m3(100.0) == pytest.approx(2.8317, rel=1e-3)

    def test_m3_ft3_roundtrip(self):
        original = 2.83
        assert m3_to_ft3(ft3_to_m3(m3_to_ft3(original))) == pytest.approx(
            m3_to_ft3(original), rel=1e-9
        )


class TestFlowConversions:
    def test_cfm_to_m3s(self):
        # 40 CFM ≈ 0.01888 m³/s
        assert cfm_to_m3s(40.0) == pytest.approx(0.01888, rel=1e-2)

    def test_m3s_to_cfm(self):
        assert m3s_to_cfm(1.0) == pytest.approx(2118.88, rel=1e-3)

    def test_cfm_roundtrip(self):
        original = 38.0
        assert m3s_to_cfm(cfm_to_m3s(original)) == pytest.approx(original, rel=1e-9)


class TestLiquidFlowConversions:
    def test_kgs_to_lpm(self):
        # 0.012 kg/s water ≈ 0.72 L/min
        assert kgs_to_lpm(0.012) == pytest.approx(0.72, rel=2e-2)

    def test_lpm_to_gpm(self):
        # 1 L/min ≈ 0.264 GPM
        assert lpm_to_gpm(1.0) == pytest.approx(0.264172, rel=1e-3)

    def test_gpm_lpm_roundtrip(self):
        original = 0.72
        assert gpm_to_lpm(lpm_to_gpm(original)) == pytest.approx(original, rel=1e-9)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_units.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.units'`

**Step 3: Write minimal implementation**

`src/units.py`:
```python
"""SI ↔ Imperial unit conversion helpers.

All functions are pure — no side effects. Internal calculations always use SI.
These helpers convert user-facing values to/from SI.
"""
from src.constants import (
    FT_TO_M, M_TO_FT,
    FT3_TO_M3, M3_TO_FT3,
    CFM_TO_M3S, M3S_TO_CFM,
    KGS_TO_LPM_WATER,
    LPM_TO_GPM, GPM_TO_LPM,
)


# Length
def ft_to_m(ft: float) -> float:
    return ft * FT_TO_M

def m_to_ft(m: float) -> float:
    return m * M_TO_FT


# Volume
def ft3_to_m3(ft3: float) -> float:
    return ft3 * FT3_TO_M3

def m3_to_ft3(m3: float) -> float:
    return m3 * M3_TO_FT3


# Airflow
def cfm_to_m3s(cfm: float) -> float:
    return cfm * CFM_TO_M3S

def m3s_to_cfm(m3s: float) -> float:
    return m3s * M3S_TO_CFM


# Liquid flow (water)
def kgs_to_lpm(kgs: float) -> float:
    return kgs * KGS_TO_LPM_WATER

def lpm_to_gpm(lpm: float) -> float:
    return lpm * LPM_TO_GPM

def gpm_to_lpm(gpm: float) -> float:
    return gpm * GPM_TO_LPM
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_units.py -v`
Expected: All 10 tests PASS

**Step 5: Commit**

```bash
git add src/units.py tests/test_units.py
git commit -m "feat: add unit conversion helpers with tests"
```

---

### Task 4: Data Models

**Files:**
- Create: `src/models.py`

**Step 1: Write data models**

```python
"""Dataclass models for thermal enclosure system components.

All values stored in SI units internally.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

from src.constants import AIR_CP, AIR_DENSITY


class CoolingType(Enum):
    AIR_COIL = "air_coil"
    LIQUID = "liquid"
    HYBRID = "hybrid"


class SolveMode(Enum):
    AIRFLOW = "Solve airflow given Q and ΔT_air"
    COOLANT = "Solve coolant flow given Q and ΔT_water"
    COIL_TEMP = "Solve coil leaving air temperature"
    HEATER = "Solve heater requirement"


@dataclass
class Enclosure:
    length_m: float
    width_m: float
    height_m: float
    air_density: float = AIR_DENSITY
    air_cp: float = AIR_CP
    internal_thermal_mass: float = 50000.0  # J/K

    @property
    def volume_m3(self) -> float:
        return self.length_m * self.width_m * self.height_m

    @property
    def thermal_capacitance(self) -> float:
        """C_e = ρ·V·c_p + C_internal (J/K)."""
        return (
            self.air_density * self.volume_m3 * self.air_cp
            + self.internal_thermal_mass
        )


@dataclass
class HeatLoads:
    baseline_load_w: float = 100.0
    additional_loads_w: float = 0.0

    @property
    def total_load_w(self) -> float:
        return self.baseline_load_w + self.additional_loads_w


@dataclass
class CoolingPlant:
    cooling_type: CoolingType = CoolingType.AIR_COIL
    coil_approach_temp_c: float = 2.0
    coil_max_capacity_w: float = 500.0
    chilled_water_temp_c: float = 15.0
    delta_t_air_c: float = 5.0
    delta_t_water_c: float = 2.0


@dataclass
class AmbientConditions:
    temperature_c: float = 23.5
    variation_amplitude_c: float = 2.0
    variation_period_hr: float = 24.0
    ua_value: float = 2.0  # W/K
```

**Step 2: Commit**

```bash
git add src/models.py
git commit -m "feat: add dataclass models for enclosure system"
```

---

### Task 5: Defaults Module

**Files:**
- Create: `defaults.py`

**Step 1: Write defaults**

```python
"""Preloaded default case: 100W laser in 4×10×2.5 ft enclosure.

Reference: Engineering Specification Section 7.
Expected steady-state outputs:
  - ΔT_air ≈ 5°C → required airflow ≈ 35–40 CFM
  - ΔT_water = 2°C → coolant ≈ 0.7 L/min
"""
from src.models import (
    Enclosure,
    HeatLoads,
    CoolingPlant,
    AmbientConditions,
    CoolingType,
)
from src.units import ft_to_m


def default_enclosure() -> Enclosure:
    return Enclosure(
        length_m=ft_to_m(4.0),
        width_m=ft_to_m(10.0),
        height_m=ft_to_m(2.5),
        internal_thermal_mass=50_000.0,  # 50 kJ/K
    )


def default_heat_loads() -> HeatLoads:
    return HeatLoads(baseline_load_w=100.0, additional_loads_w=0.0)


def default_cooling_plant() -> CoolingPlant:
    return CoolingPlant(
        cooling_type=CoolingType.AIR_COIL,
        coil_approach_temp_c=2.0,
        coil_max_capacity_w=500.0,
        chilled_water_temp_c=15.0,
        delta_t_air_c=5.0,
        delta_t_water_c=2.0,
    )


def default_ambient() -> AmbientConditions:
    return AmbientConditions(
        temperature_c=23.5,
        variation_amplitude_c=2.0,
        variation_period_hr=24.0,
        ua_value=2.0,
    )
```

**Step 2: Commit**

```bash
git add defaults.py
git commit -m "feat: add preloaded 100W default case"
```

---

### Task 6: Steady-State Solvers + Tests (TDD)

**Files:**
- Create: `src/solvers.py`
- Create: `tests/test_solvers.py`

**Step 1: Write the failing tests**

`tests/test_solvers.py`:
```python
"""Tests for steady-state thermal solvers.

Reference values from Engineering Specification Section 7:
  - 100 W load, ΔT_air=5°C → airflow ≈ 35–40 CFM
  - 100 W load, ΔT_water=2°C → coolant ≈ 0.7 L/min
"""
import pytest
from src.solvers import (
    solve_airflow,
    solve_coolant_flow,
    solve_coil_leaving_temp,
    solve_heater_requirement,
    compute_warnings,
    SolverResult,
)
from src.models import CoolingPlant, CoolingType
from src.constants import AIR_CP, AIR_DENSITY, WATER_CP
from src.units import m3s_to_cfm, kgs_to_lpm


class TestSolveAirflow:
    """m_dot = Q / (c_p * ΔT_air), then convert to CFM."""

    def test_100w_5c_delta(self):
        result = solve_airflow(q_total_w=100.0, delta_t_air_c=5.0)
        cfm = m3s_to_cfm(result.airflow_m3s)
        # Spec says 35–40 CFM
        assert 35.0 <= cfm <= 42.0

    def test_analytical_value(self):
        # m_dot = 100 / (1005 * 5) = 0.019900 kg/s
        # V_dot = 0.019900 / 1.19 = 0.016723 m³/s
        result = solve_airflow(q_total_w=100.0, delta_t_air_c=5.0)
        expected_m3s = 100.0 / (AIR_CP * 5.0) / AIR_DENSITY
        assert result.airflow_m3s == pytest.approx(expected_m3s, rel=1e-6)

    def test_zero_load(self):
        result = solve_airflow(q_total_w=0.0, delta_t_air_c=5.0)
        assert result.airflow_m3s == pytest.approx(0.0)

    def test_small_delta_t_large_flow(self):
        result = solve_airflow(q_total_w=100.0, delta_t_air_c=1.0)
        cfm = m3s_to_cfm(result.airflow_m3s)
        assert cfm > 150.0  # Much higher flow for small ΔT


class TestSolveCoolantFlow:
    """m_dot_water = Q / (c_p_water * ΔT_water)."""

    def test_100w_2c_delta(self):
        result = solve_coolant_flow(q_total_w=100.0, delta_t_water_c=2.0)
        lpm = kgs_to_lpm(result.coolant_kgs)
        # Spec says ~0.7 L/min
        assert lpm == pytest.approx(0.72, rel=5e-2)

    def test_analytical_value(self):
        # m_dot = 100 / (4186 * 2) = 0.011945 kg/s
        result = solve_coolant_flow(q_total_w=100.0, delta_t_water_c=2.0)
        expected_kgs = 100.0 / (WATER_CP * 2.0)
        assert result.coolant_kgs == pytest.approx(expected_kgs, rel=1e-6)


class TestSolveCoilLeavingTemp:
    """T_coil_out = T_return - Q / (m_dot_air * c_p)."""

    def test_known_case(self):
        # 100W, airflow for 5°C ΔT → coil leaves 5°C below return
        m_dot_kgs = 100.0 / (AIR_CP * 5.0)
        result = solve_coil_leaving_temp(
            q_total_w=100.0,
            airflow_kgs=m_dot_kgs,
            return_air_temp_c=23.5,
        )
        assert result.coil_leaving_temp_c == pytest.approx(18.5, rel=1e-3)


class TestSolveHeaterRequirement:
    """Heater needed when ambient cooling exceeds load."""

    def test_no_heater_needed(self):
        # Ambient above setpoint, load is positive — no heater
        result = solve_heater_requirement(
            q_load_w=100.0,
            ua_value=2.0,
            ambient_temp_c=23.5,
            setpoint_c=23.5,
        )
        assert result.heater_required_w == pytest.approx(0.0)

    def test_heater_needed_cold_ambient(self):
        # Ambient well below setpoint, low internal load
        # Heat loss = UA * (T_set - T_amb) = 2.0 * (23.5 - 15.0) = 17.0 W
        # Net = Q_load - heat_loss = 10.0 - 17.0 = -7.0 → need 7W heater
        result = solve_heater_requirement(
            q_load_w=10.0,
            ua_value=2.0,
            ambient_temp_c=15.0,
            setpoint_c=23.5,
        )
        assert result.heater_required_w == pytest.approx(7.0, rel=1e-3)


class TestComputeWarnings:
    def test_no_warnings_nominal(self):
        warnings = compute_warnings(
            coil_utilization_pct=50.0,
            heater_required_w=0.0,
        )
        assert len(warnings) == 0

    def test_coil_warning_high_utilization(self):
        warnings = compute_warnings(
            coil_utilization_pct=92.0,
            heater_required_w=0.0,
        )
        assert any("utilization" in w.lower() for w in warnings)

    def test_coil_error_saturated(self):
        warnings = compute_warnings(
            coil_utilization_pct=105.0,
            heater_required_w=0.0,
        )
        assert any("saturated" in w.lower() for w in warnings)

    def test_heater_warning(self):
        warnings = compute_warnings(
            coil_utilization_pct=10.0,
            heater_required_w=15.0,
        )
        assert any("heater" in w.lower() for w in warnings)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_solvers.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.solvers'`

**Step 3: Write the solver implementation**

`src/solvers.py`:
```python
"""Steady-state thermal solvers for enclosure sizing.

All functions are pure — no UI dependency. Take SI values, return SI values.
Unit conversion is the caller's responsibility.

Physics reference:
  Airflow:  m_dot = Q / (c_p * ΔT_air)
  Coolant:  m_dot = Q / (c_p_water * ΔT_water)
  Coil temp: T_out = T_return - Q / (m_dot * c_p)
  Heater:   needed when UA*(T_set - T_amb) > Q_load
"""
from __future__ import annotations
from dataclasses import dataclass, field

from src.constants import AIR_CP, AIR_DENSITY, WATER_CP


@dataclass
class SolverResult:
    """Container for all solver outputs."""
    airflow_m3s: float = 0.0
    airflow_kgs: float = 0.0
    coolant_kgs: float = 0.0
    coil_leaving_temp_c: float = 0.0
    heater_required_w: float = 0.0
    coil_utilization_pct: float = 0.0
    warnings: list[str] = field(default_factory=list)


def solve_airflow(
    q_total_w: float,
    delta_t_air_c: float,
    air_cp: float = AIR_CP,
    air_density: float = AIR_DENSITY,
) -> SolverResult:
    """Solve required airflow to remove heat load.

    m_dot_air = Q / (c_p * ΔT_air)
    V_dot_air = m_dot_air / ρ
    """
    if delta_t_air_c == 0:
        raise ValueError("ΔT_air cannot be zero")
    m_dot = q_total_w / (air_cp * delta_t_air_c)
    v_dot = m_dot / air_density
    return SolverResult(airflow_m3s=v_dot, airflow_kgs=m_dot)


def solve_coolant_flow(
    q_total_w: float,
    delta_t_water_c: float,
    water_cp: float = WATER_CP,
) -> SolverResult:
    """Solve required coolant mass flow.

    m_dot_water = Q / (c_p_water * ΔT_water)
    """
    if delta_t_water_c == 0:
        raise ValueError("ΔT_water cannot be zero")
    m_dot = q_total_w / (water_cp * delta_t_water_c)
    return SolverResult(coolant_kgs=m_dot)


def solve_coil_leaving_temp(
    q_total_w: float,
    airflow_kgs: float,
    return_air_temp_c: float,
    air_cp: float = AIR_CP,
) -> SolverResult:
    """Solve coil leaving air temperature.

    T_coil_out = T_return - Q / (m_dot_air * c_p)
    """
    if airflow_kgs == 0:
        raise ValueError("Airflow mass rate cannot be zero")
    delta_t = q_total_w / (airflow_kgs * air_cp)
    t_out = return_air_temp_c - delta_t
    return SolverResult(coil_leaving_temp_c=t_out)


def solve_heater_requirement(
    q_load_w: float,
    ua_value: float,
    ambient_temp_c: float,
    setpoint_c: float,
) -> SolverResult:
    """Solve heater power needed when ambient cools enclosure below setpoint.

    Heat loss to ambient = UA * (T_setpoint - T_ambient)  [when T_set > T_amb]
    Net cooling surplus = heat_loss - Q_load
    If positive, heater is needed to compensate.
    """
    heat_loss_w = ua_value * (setpoint_c - ambient_temp_c)
    net_deficit = heat_loss_w - q_load_w
    heater_w = max(0.0, net_deficit)
    return SolverResult(heater_required_w=heater_w)


def compute_warnings(
    coil_utilization_pct: float,
    heater_required_w: float,
) -> list[str]:
    """Generate warning messages based on solver results."""
    warnings = []
    if coil_utilization_pct > 100.0:
        warnings.append(
            f"COOLING SATURATED: Coil utilization at {coil_utilization_pct:.0f}%. "
            "Increase coil capacity or reduce heat load."
        )
    elif coil_utilization_pct > 90.0:
        warnings.append(
            f"High coil utilization: {coil_utilization_pct:.0f}%. "
            "Limited cooling margin remaining."
        )
    if heater_required_w > 0.0:
        warnings.append(
            f"Heater required: {heater_required_w:.1f} W to maintain setpoint "
            "under current ambient conditions."
        )
    return warnings
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_solvers.py -v`
Expected: All 11 tests PASS

**Step 5: Commit**

```bash
git add src/solvers.py tests/test_solvers.py
git commit -m "feat: add steady-state thermal solvers with tests"
```

---

### Task 7: Default Case Validation Test (TDD)

**Files:**
- Create: `tests/test_defaults.py`

**Step 1: Write the test**

```python
"""Validate preloaded 100W default case against spec sanity checks.

Engineering Specification Section 7:
  - ΔT_air ≈ 5°C → required airflow ≈ 35–40 CFM
  - ΔT_water = 2°C → coolant ≈ 0.7 L/min
"""
import pytest
from defaults import (
    default_enclosure,
    default_heat_loads,
    default_cooling_plant,
    default_ambient,
)
from src.solvers import solve_airflow, solve_coolant_flow, solve_heater_requirement
from src.units import m3s_to_cfm, kgs_to_lpm


class TestDefaultCase:
    def test_enclosure_volume(self):
        enc = default_enclosure()
        # 4×10×2.5 ft = 100 ft³ ≈ 2.83 m³
        assert enc.volume_m3 == pytest.approx(2.83, rel=1e-2)

    def test_airflow_sanity(self):
        loads = default_heat_loads()
        cooling = default_cooling_plant()
        result = solve_airflow(
            q_total_w=loads.total_load_w,
            delta_t_air_c=cooling.delta_t_air_c,
        )
        cfm = m3s_to_cfm(result.airflow_m3s)
        assert 35.0 <= cfm <= 42.0, f"Expected 35-40 CFM, got {cfm:.1f}"

    def test_coolant_flow_sanity(self):
        loads = default_heat_loads()
        cooling = default_cooling_plant()
        result = solve_coolant_flow(
            q_total_w=loads.total_load_w,
            delta_t_water_c=cooling.delta_t_water_c,
        )
        lpm = kgs_to_lpm(result.coolant_kgs)
        assert lpm == pytest.approx(0.72, rel=5e-2), f"Expected ~0.7 L/min, got {lpm:.3f}"

    def test_no_heater_at_nominal_ambient(self):
        loads = default_heat_loads()
        ambient = default_ambient()
        result = solve_heater_requirement(
            q_load_w=loads.total_load_w,
            ua_value=ambient.ua_value,
            ambient_temp_c=ambient.temperature_c,
            setpoint_c=ambient.temperature_c,
        )
        assert result.heater_required_w == pytest.approx(0.0)
```

**Step 2: Run tests**

Run: `pytest tests/test_defaults.py -v`
Expected: All 4 tests PASS

**Step 3: Commit**

```bash
git add tests/test_defaults.py
git commit -m "test: validate 100W default case against spec"
```

---

### Task 8: Custom CSS Theme

**Files:**
- Create: `src/ui/theme.py`

**Step 1: Write the theme CSS injection**

```python
"""Precision Instrument dark theme CSS for Streamlit.

Injected via st.markdown(unsafe_allow_html=True).
Colors, typography, and metric card styling.
"""

GOOGLE_FONTS = """
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet">
"""

CUSTOM_CSS = """
<style>
    /* ── Global ────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=DM+Sans:wght@400;500;700&display=swap');

    .stApp {
        font-family: 'DM Sans', sans-serif;
    }

    /* ── Panel containers ──────────────────────────── */
    div[data-testid="stExpander"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    div[data-testid="stExpander"] summary span {
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 0.85rem;
        color: #8B949E;
    }

    /* ── Metric cards ──────────────────────────────── */
    div[data-testid="stMetric"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-top: 3px solid #00D4AA;
        border-radius: 8px;
        padding: 1rem;
    }
    div[data-testid="stMetric"] label {
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-size: 0.75rem;
        color: #8B949E;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 1.6rem;
        color: #E6EDF3;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: #58A6FF;
    }

    /* ── Warning metric (amber top border) ─────────── */
    .metric-warning div[data-testid="stMetric"] {
        border-top-color: #F0A830;
    }

    /* ── Error metric (red top border) ─────────────── */
    .metric-error div[data-testid="stMetric"] {
        border-top-color: #F85149;
    }

    /* ── Sidebar styling ───────────────────────────── */
    section[data-testid="stSidebar"] {
        background-color: #0D1117;
        border-right: 1px solid #30363D;
    }

    /* ── Title bar ─────────────────────────────────── */
    .main-title {
        font-family: 'DM Sans', sans-serif;
        font-weight: 700;
        font-size: 1.3rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #E6EDF3;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #30363D;
        margin-bottom: 1rem;
    }

    /* ── Number inputs (JetBrains Mono) ────────────── */
    input[type="number"], div[data-testid="stNumberInput"] input {
        font-family: 'JetBrains Mono', monospace;
    }

    /* ── Unit labels ───────────────────────────────── */
    .unit-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: #58A6FF;
    }

    /* ── Hide Streamlit branding ───────────────────── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""


def inject_theme():
    """Call this at the top of app.py to apply the Precision Instrument theme."""
    import streamlit as st
    st.markdown(GOOGLE_FONTS, unsafe_allow_html=True)
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
```

**Step 2: Commit**

```bash
git add src/ui/theme.py
git commit -m "feat: add Precision Instrument dark theme CSS"
```

---

### Task 9: UI Panel — Geometry (Panel 1)

**Files:**
- Create: `src/ui/panel_geometry.py`

**Step 1: Write the panel**

```python
"""Panel 1: Enclosure geometry and thermal mass inputs."""
import streamlit as st
from src.units import ft_to_m, m_to_ft, ft3_to_m3, m3_to_ft3


def render_geometry_panel(use_imperial: bool) -> dict:
    """Render geometry inputs and return values in SI.

    Returns dict with keys: length_m, width_m, height_m, internal_thermal_mass.
    """
    with st.expander("GEOMETRY & PROPERTIES", expanded=True):
        if use_imperial:
            c1, c2, c3 = st.columns(3)
            with c1:
                length = st.number_input("Length (ft)", value=4.0, min_value=0.1, step=0.5)
            with c2:
                width = st.number_input("Width (ft)", value=10.0, min_value=0.1, step=0.5)
            with c3:
                height = st.number_input("Height (ft)", value=2.5, min_value=0.1, step=0.5)
            length_m = ft_to_m(length)
            width_m = ft_to_m(width)
            height_m = ft_to_m(height)
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                length_m = st.number_input("Length (m)", value=1.22, min_value=0.01, step=0.1, format="%.2f")
            with c2:
                width_m = st.number_input("Width (m)", value=3.05, min_value=0.01, step=0.1, format="%.2f")
            with c3:
                height_m = st.number_input("Height (m)", value=0.76, min_value=0.01, step=0.1, format="%.2f")

        volume_m3 = length_m * width_m * height_m

        # Display volume in both units
        vol_col1, vol_col2 = st.columns(2)
        with vol_col1:
            st.markdown(f"**Volume:** `{volume_m3:.3f}` m³")
        with vol_col2:
            st.markdown(f'<span class="unit-label">{m3_to_ft3(volume_m3):.1f} ft³</span>', unsafe_allow_html=True)

        internal_mass = st.slider(
            "Internal thermal mass (kJ/K)",
            min_value=0.0,
            max_value=200.0,
            value=50.0,
            step=5.0,
            help="Thermal mass of hardware inside enclosure (laser, optics, mounts)",
        )

    return {
        "length_m": length_m,
        "width_m": width_m,
        "height_m": height_m,
        "internal_thermal_mass": internal_mass * 1000.0,  # kJ → J
    }
```

**Step 2: Commit**

```bash
git add src/ui/panel_geometry.py
git commit -m "feat: add geometry input panel"
```

---

### Task 10: UI Panel — Heat Loads (Panel 2)

**Files:**
- Create: `src/ui/panel_loads.py`

**Step 1: Write the panel**

```python
"""Panel 2: Internal heat load inputs."""
import streamlit as st


def render_loads_panel() -> dict:
    """Render heat load inputs and return values in watts.

    Returns dict with keys: baseline_load_w, additional_loads_w.
    """
    with st.expander("HEAT LOADS", expanded=True):
        baseline = st.number_input(
            "Baseline load (W)",
            value=100.0,
            min_value=0.0,
            step=10.0,
            help="Primary heat source (e.g., laser system)",
        )
        additional = st.number_input(
            "Additional loads (W)",
            value=0.0,
            min_value=0.0,
            step=5.0,
            help="Sum of secondary heat sources (electronics, pumps, etc.)",
        )
        total = baseline + additional
        st.markdown(f"**Total load:** `{total:.1f}` W")

    return {
        "baseline_load_w": baseline,
        "additional_loads_w": additional,
    }
```

**Step 2: Commit**

```bash
git add src/ui/panel_loads.py
git commit -m "feat: add heat loads input panel"
```

---

### Task 11: UI Panel — Ambient Conditions (Panel 3)

**Files:**
- Create: `src/ui/panel_ambient.py`

**Step 1: Write the panel**

```python
"""Panel 3: Ambient temperature and coupling inputs."""
import streamlit as st


def render_ambient_panel() -> dict:
    """Render ambient condition inputs and return values in SI.

    Returns dict with keys: temperature_c, variation_amplitude_c,
    variation_period_hr, ua_value.
    """
    with st.expander("AMBIENT CONDITIONS", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            temp = st.number_input(
                "Ambient temperature (°C)",
                value=23.5,
                min_value=-10.0,
                max_value=50.0,
                step=0.5,
            )
        with c2:
            variation = st.number_input(
                "Variation amplitude (±°C)",
                value=2.0,
                min_value=0.0,
                max_value=10.0,
                step=0.5,
                help="Peak amplitude of ambient temperature swing",
            )

        ua_mode = st.radio(
            "Ambient coupling input mode",
            ["Direct UA (W/K)", "Air changes per hour (ACH)"],
            horizontal=True,
        )

        if ua_mode == "Direct UA (W/K)":
            ua = st.number_input(
                "UA value (W/K)",
                value=2.0,
                min_value=0.0,
                step=0.5,
                help="Conduction + infiltration coupling to ambient",
            )
        else:
            ach = st.number_input(
                "Air changes per hour",
                value=0.5,
                min_value=0.0,
                step=0.1,
                help="Infiltration rate; converted to UA internally",
            )
            # UA ≈ ACH * V * ρ * cp / 3600
            # This is a placeholder — volume comes from geometry panel
            # For now, use a reference volume; app.py will recompute
            st.caption("Note: UA computed using enclosure volume from Panel 1")
            ua = ach  # Will be converted in app.py using actual volume

    return {
        "temperature_c": temp,
        "variation_amplitude_c": variation,
        "variation_period_hr": 24.0,
        "ua_value": ua,
        "ua_mode": ua_mode,
    }
```

**Step 2: Commit**

```bash
git add src/ui/panel_ambient.py
git commit -m "feat: add ambient conditions input panel"
```

---

### Task 12: UI Panel — Cooling Plant (Panel 4)

**Files:**
- Create: `src/ui/panel_cooling.py`

**Step 1: Write the panel**

```python
"""Panel 4: Cooling plant configuration inputs."""
import streamlit as st
from src.models import CoolingType, SolveMode


def render_cooling_panel(solve_mode: SolveMode) -> dict:
    """Render cooling plant inputs. Some fields are disabled based on solve mode.

    Returns dict with keys matching CoolingPlant fields.
    """
    with st.expander("COOLING PLANT", expanded=True):
        cooling_type = st.selectbox(
            "Cooling type",
            options=[ct.value for ct in CoolingType],
            format_func=lambda x: {"air_coil": "Air Coil", "liquid": "Liquid", "hybrid": "Hybrid"}[x],
        )

        c1, c2 = st.columns(2)
        with c1:
            approach = st.number_input(
                "Coil approach temp (°C)",
                value=2.0,
                min_value=0.1,
                step=0.5,
                help="Minimum temperature difference between coolant and air at coil exit",
            )
        with c2:
            max_cap = st.number_input(
                "Coil max capacity (W)",
                value=500.0,
                min_value=10.0,
                step=50.0,
                help="Maximum cooling power of the heat exchanger",
            )

        c3, c4 = st.columns(2)
        with c3:
            chilled_water_temp = st.number_input(
                "Chilled water supply (°C)",
                value=15.0,
                min_value=0.0,
                max_value=30.0,
                step=1.0,
            )
        with c4:
            delta_t_water = st.number_input(
                "Coolant ΔT (°C)",
                value=2.0,
                min_value=0.1,
                step=0.5,
                disabled=(solve_mode == SolveMode.COOLANT),
                help="Disabled when solve mode is 'Solve coolant flow'",
            )

        # ΔT_air: editable unless we're solving for airflow
        delta_t_air = st.number_input(
            "Air-side ΔT (°C)",
            value=5.0,
            min_value=0.1,
            step=0.5,
            disabled=(solve_mode == SolveMode.AIRFLOW),
            help="Disabled when solve mode is 'Solve airflow'",
        )

    return {
        "cooling_type": cooling_type,
        "coil_approach_temp_c": approach,
        "coil_max_capacity_w": max_cap,
        "chilled_water_temp_c": chilled_water_temp,
        "delta_t_air_c": delta_t_air,
        "delta_t_water_c": delta_t_water,
    }
```

**Step 2: Commit**

```bash
git add src/ui/panel_cooling.py
git commit -m "feat: add cooling plant input panel"
```

---

### Task 13: UI Panel — Results (Panel 6)

**Files:**
- Create: `src/ui/panel_results.py`

**Step 1: Write the results panel**

```python
"""Panel 6: Computed results display with metric cards and warnings."""
import streamlit as st
from src.units import m3s_to_cfm, kgs_to_lpm, lpm_to_gpm


def render_results_panel(
    airflow_m3s: float,
    coolant_kgs: float,
    coil_utilization_pct: float,
    heater_required_w: float,
    coil_leaving_temp_c: float,
    warnings: list[str],
) -> None:
    """Render computed results as metric cards with dual-unit display."""
    st.markdown("### RESULTS")

    # Derived display values
    cfm = m3s_to_cfm(airflow_m3s)
    lpm = kgs_to_lpm(coolant_kgs)
    gpm = lpm_to_gpm(lpm)

    # Metric cards row
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            label="REQUIRED AIRFLOW",
            value=f"{cfm:.1f} CFM",
            delta=f"{airflow_m3s:.4f} m³/s",
        )

    with c2:
        st.metric(
            label="COOLANT FLOW",
            value=f"{lpm:.2f} L/min",
            delta=f"{gpm:.3f} GPM",
        )

    with c3:
        # Color-code utilization
        if coil_utilization_pct > 100:
            st.markdown('<div class="metric-error">', unsafe_allow_html=True)
        elif coil_utilization_pct > 90:
            st.markdown('<div class="metric-warning">', unsafe_allow_html=True)
        else:
            st.markdown("<div>", unsafe_allow_html=True)
        st.metric(
            label="COIL UTILIZATION",
            value=f"{coil_utilization_pct:.0f}%",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # Utilization bar
        bar_color = "#00D4AA"
        if coil_utilization_pct > 100:
            bar_color = "#F85149"
        elif coil_utilization_pct > 90:
            bar_color = "#F0A830"
        bar_width = min(coil_utilization_pct, 100)
        st.markdown(
            f'<div style="background:#30363D;border-radius:4px;height:8px;width:100%">'
            f'<div style="background:{bar_color};border-radius:4px;height:8px;width:{bar_width}%"></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with c4:
        st.metric(
            label="HEATER REQUIRED",
            value=f"{heater_required_w:.1f} W",
        )

    # Coil leaving temperature
    st.markdown(
        f'<span class="unit-label">Coil leaving air temp: {coil_leaving_temp_c:.1f} °C</span>',
        unsafe_allow_html=True,
    )

    # Warnings
    if warnings:
        st.markdown("---")
        for w in warnings:
            if "SATURATED" in w.upper():
                st.error(w)
            elif "heater" in w.lower():
                st.info(w)
            else:
                st.warning(w)
```

**Step 2: Commit**

```bash
git add src/ui/panel_results.py
git commit -m "feat: add results display panel with warnings"
```

---

### Task 14: System Schematic (Plotly)

**Files:**
- Create: `src/ui/schematic.py`

**Step 1: Write the schematic renderer**

```python
"""Interactive system schematic using Plotly.

Renders the thermal loop: enclosure → return air → coil → supply air → enclosure,
with ambient coupling and live value annotations.
"""
import plotly.graph_objects as go


def render_schematic(
    enclosure_temp_c: float,
    supply_temp_c: float,
    return_temp_c: float,
    ambient_temp_c: float,
    chilled_water_temp_c: float,
    airflow_cfm: float,
    coolant_lpm: float,
    heat_load_w: float,
    ua_value: float,
) -> go.Figure:
    """Build and return a Plotly figure of the thermal system schematic."""
    fig = go.Figure()

    # Colors
    BG = "#0D1117"
    PANEL = "#161B22"
    BORDER = "#30363D"
    TEAL = "#00D4AA"
    BLUE = "#58A6FF"
    TEXT = "#E6EDF3"
    SECONDARY = "#8B949E"
    AMBER = "#F0A830"

    # ── Enclosure box ──────────────────────────────
    fig.add_shape(
        type="rect", x0=1, y0=1, x1=5, y1=4,
        line=dict(color=TEAL, width=2),
        fillcolor=PANEL,
    )
    fig.add_annotation(
        x=3, y=3.5, text="<b>ENCLOSURE</b>",
        font=dict(color=TEXT, size=14, family="DM Sans"),
        showarrow=False,
    )
    fig.add_annotation(
        x=3, y=2.8, text=f"T = {enclosure_temp_c:.1f} °C",
        font=dict(color=TEAL, size=16, family="JetBrains Mono"),
        showarrow=False,
    )
    fig.add_annotation(
        x=3, y=2.2, text=f"Q_load = {heat_load_w:.0f} W",
        font=dict(color=AMBER, size=12, family="JetBrains Mono"),
        showarrow=False,
    )

    # ── Cooling coil box ───────────────────────────
    fig.add_shape(
        type="rect", x0=7, y0=1.5, x1=9, y1=3.5,
        line=dict(color=BLUE, width=2),
        fillcolor=PANEL,
    )
    fig.add_annotation(
        x=8, y=3.0, text="<b>COIL</b>",
        font=dict(color=TEXT, size=12, family="DM Sans"),
        showarrow=False,
    )
    fig.add_annotation(
        x=8, y=2.2, text=f"T_out = {supply_temp_c:.1f} °C",
        font=dict(color=BLUE, size=11, family="JetBrains Mono"),
        showarrow=False,
    )

    # ── Airflow arrows: enclosure → coil (return) ──
    fig.add_annotation(
        x=7, y=3.8, ax=5, ay=3.8,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=2, arrowsize=1.5,
        arrowcolor=SECONDARY, arrowwidth=2,
    )
    fig.add_annotation(
        x=6, y=4.1, text=f"Return {return_temp_c:.1f} °C",
        font=dict(color=SECONDARY, size=10, family="JetBrains Mono"),
        showarrow=False,
    )

    # ── Airflow arrows: coil → enclosure (supply) ──
    fig.add_annotation(
        x=5, y=1.2, ax=7, ay=1.2,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=2, arrowsize=1.5,
        arrowcolor=TEAL, arrowwidth=2,
    )
    fig.add_annotation(
        x=6, y=0.9, text=f"Supply {supply_temp_c:.1f} °C  |  {airflow_cfm:.0f} CFM",
        font=dict(color=TEAL, size=10, family="JetBrains Mono"),
        showarrow=False,
    )

    # ── Ambient coupling ───────────────────────────
    fig.add_annotation(
        x=3, y=5.0, text=f"Ambient {ambient_temp_c:.1f} °C",
        font=dict(color=SECONDARY, size=11, family="JetBrains Mono"),
        showarrow=False,
    )
    fig.add_annotation(
        x=3, y=4.0, ax=3, ay=4.6,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=3, arrowsize=1,
        arrowcolor=SECONDARY, arrowwidth=1,
    )
    fig.add_annotation(
        x=3.8, y=4.5, text=f"UA = {ua_value:.1f} W/K",
        font=dict(color=SECONDARY, size=9, family="JetBrains Mono"),
        showarrow=False,
    )

    # ── Coolant annotation ─────────────────────────
    fig.add_annotation(
        x=8, y=1.1, text=f"Coolant: {chilled_water_temp_c:.0f} °C  |  {coolant_lpm:.2f} L/min",
        font=dict(color=BLUE, size=10, family="JetBrains Mono"),
        showarrow=False,
    )

    # ── Layout ─────────────────────────────────────
    fig.update_layout(
        xaxis=dict(visible=False, range=[0, 10]),
        yaxis=dict(visible=False, range=[0, 5.5], scaleanchor="x"),
        plot_bgcolor=BG,
        paper_bgcolor=BG,
        margin=dict(l=0, r=0, t=10, b=10),
        height=320,
        font=dict(family="DM Sans"),
    )

    return fig
```

**Step 2: Commit**

```bash
git add src/ui/schematic.py
git commit -m "feat: add Plotly system schematic with live annotations"
```

---

### Task 15: Main App Entry Point

**Files:**
- Create: `app.py`

**Step 1: Write the Streamlit app**

```python
"""Quantum Enclosure Thermal Analyzer — Streamlit entry point.

Composes UI panels, builds models, calls solvers, displays results.
Run: streamlit run app.py
"""
import streamlit as st

from src.ui.theme import inject_theme
from src.ui.panel_geometry import render_geometry_panel
from src.ui.panel_loads import render_loads_panel
from src.ui.panel_ambient import render_ambient_panel
from src.ui.panel_cooling import render_cooling_panel
from src.ui.panel_results import render_results_panel
from src.ui.schematic import render_schematic
from src.models import (
    Enclosure, HeatLoads, CoolingPlant, AmbientConditions,
    CoolingType, SolveMode,
)
from src.solvers import (
    solve_airflow, solve_coolant_flow,
    solve_coil_leaving_temp, solve_heater_requirement,
    compute_warnings,
)
from src.units import m3s_to_cfm, kgs_to_lpm
from src.constants import AIR_CP, AIR_DENSITY

st.set_page_config(
    page_title="Quantum Enclosure Thermal Analyzer",
    layout="wide",
)
inject_theme()

# ── Title ──────────────────────────────────────────────
st.markdown('<div class="main-title">QUANTUM ENCLOSURE THERMAL ANALYZER</div>', unsafe_allow_html=True)

# ── Sidebar: solve mode + unit toggle ──────────────────
with st.sidebar:
    st.markdown("### CONFIGURATION")
    solve_mode = st.selectbox(
        "Solve mode",
        options=[sm for sm in SolveMode],
        format_func=lambda sm: sm.value,
    )
    use_imperial = st.toggle("Imperial units", value=True)
    st.markdown("---")
    st.caption("Phase 1 — Steady-State Sizing")

# ── Input panels (left column) ─────────────────────────
left_col, right_col = st.columns([1, 2])

with left_col:
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
    temperature_c=ambient_input["temperature_c"],
    variation_amplitude_c=ambient_input["variation_amplitude_c"],
    variation_period_hr=ambient_input["variation_period_hr"],
    ua_value=ua_value,
)

cooling = CoolingPlant(
    cooling_type=CoolingType(cooling_input["cooling_type"]),
    coil_approach_temp_c=cooling_input["coil_approach_temp_c"],
    coil_max_capacity_w=cooling_input["coil_max_capacity_w"],
    chilled_water_temp_c=cooling_input["chilled_water_temp_c"],
    delta_t_air_c=cooling_input["delta_t_air_c"],
    delta_t_water_c=cooling_input["delta_t_water_c"],
)

# ── Run solvers ────────────────────────────────────────
q_total = loads.total_load_w

# Airflow
air_result = solve_airflow(q_total_w=q_total, delta_t_air_c=cooling.delta_t_air_c)

# Coolant
coolant_result = solve_coolant_flow(q_total_w=q_total, delta_t_water_c=cooling.delta_t_water_c)

# Coil leaving temp
coil_result = solve_coil_leaving_temp(
    q_total_w=q_total,
    airflow_kgs=air_result.airflow_kgs,
    return_air_temp_c=ambient.temperature_c,  # Approximate: return ≈ enclosure ≈ setpoint
)

# Heater requirement
heater_result = solve_heater_requirement(
    q_load_w=q_total,
    ua_value=ambient.ua_value,
    ambient_temp_c=ambient.temperature_c,
    setpoint_c=ambient.temperature_c,
)

# Coil utilization
coil_utilization = (q_total / cooling.coil_max_capacity_w) * 100.0

# Warnings
warnings = compute_warnings(
    coil_utilization_pct=coil_utilization,
    heater_required_w=heater_result.heater_required_w,
)

# ── Right column: schematic + results ──────────────────
with right_col:
    cfm = m3s_to_cfm(air_result.airflow_m3s)
    lpm = kgs_to_lpm(coolant_result.coolant_kgs)

    fig = render_schematic(
        enclosure_temp_c=ambient.temperature_c,
        supply_temp_c=coil_result.coil_leaving_temp_c,
        return_temp_c=ambient.temperature_c,
        ambient_temp_c=ambient.temperature_c,
        chilled_water_temp_c=cooling.chilled_water_temp_c,
        airflow_cfm=cfm,
        coolant_lpm=lpm,
        heat_load_w=q_total,
        ua_value=ambient.ua_value,
    )
    st.plotly_chart(fig, use_container_width=True)

    render_results_panel(
        airflow_m3s=air_result.airflow_m3s,
        coolant_kgs=coolant_result.coolant_kgs,
        coil_utilization_pct=coil_utilization,
        heater_required_w=heater_result.heater_required_w,
        coil_leaving_temp_c=coil_result.coil_leaving_temp_c,
        warnings=warnings,
    )
```

**Step 2: Run the app to verify it loads**

Run: `streamlit run app.py`
Expected: Dashboard opens in browser, shows default 100W case, schematic renders, results display ~38 CFM and ~0.72 L/min

**Step 3: Commit**

```bash
git add app.py
git commit -m "feat: add main Streamlit app with all panels and schematic"
```

---

### Task 16: Run Full Test Suite

**Step 1: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests PASS (units + solvers + defaults)

**Step 2: Verify default case sanity**

Run: `python -c "from defaults import *; from src.solvers import *; from src.units import *; r = solve_airflow(100, 5); print(f'CFM: {m3s_to_cfm(r.airflow_m3s):.1f}'); r2 = solve_coolant_flow(100, 2); print(f'LPM: {kgs_to_lpm(r2.coolant_kgs):.2f}')"`
Expected output:
```
CFM: 35.4
LPM: 0.72
```

**Step 3: Commit (if any fixes needed)**

If any test failures were found and fixed, commit the fixes.

---

### Task 17: Push to Remote

**Step 1: Push main branch**

Run: `git push -u origin master`
Expected: Successfully pushed to https://github.com/rbhale-git/laser-tms.git

---
