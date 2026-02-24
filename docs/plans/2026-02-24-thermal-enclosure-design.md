# Quantum Lab Enclosure Thermal Analysis Tool — Design Document

**Date:** 2026-02-24
**Status:** Approved

---

## 1. Summary

Python-based Streamlit dashboard for modeling and designing a precision temperature-controlled enclosure for a quantum computing lab laser system. MVP covers steady-state sizing; architecture supports Phase 2 transient simulation and PID control.

**Key requirements:**
- Remove ~100 W continuous internal heat load
- Maintain ±0.1 °C temperature stability
- Account for ambient variation (~23.5 °C ± 2 °C)
- Heat exchanger (HX) based cooling with recirculating air

---

## 2. Decisions

| Decision | Choice |
|---|---|
| Framework | Streamlit |
| Project location | `~/Projects/thermal-enclosure/` |
| MVP panels | 1–4 + 6 (Panel 5 deferred to Phase 2) |
| Unit handling | Dual display (SI + Imperial), SI internally |
| Solve mode selection | Explicit dropdown |
| Testing | pytest from the start |
| Architecture | Layered: model / solver / UI separation |
| Aesthetic | "Precision Instrument" dark theme |

---

## 3. Architecture

```
thermal-enclosure/
├── app.py                       # Streamlit entry point
├── requirements.txt             # streamlit, numpy, plotly, pytest
├── defaults.py                  # Preloaded 100W case
├── src/
│   ├── __init__.py
│   ├── constants.py             # Air/water properties, conversion factors
│   ├── models.py                # Dataclasses: Enclosure, CoolingPlant, etc.
│   ├── solvers.py               # Pure functions: solve_airflow, solve_coolant, etc.
│   ├── units.py                 # SI ↔ imperial conversion helpers
│   └── ui/
│       ├── __init__.py
│       ├── panel_geometry.py    # Panel 1: dimensions, volume, thermal mass
│       ├── panel_loads.py       # Panel 2: heat load inputs
│       ├── panel_ambient.py     # Panel 3: ambient conditions, UA
│       ├── panel_cooling.py     # Panel 4: cooling plant config
│       └── panel_results.py     # Panel 6: outputs, warnings, schematic
├── tests/
│   ├── test_solvers.py          # Verify against 100W analytical case
│   └── test_units.py            # Conversion accuracy
└── .streamlit/
    └── config.toml              # Dark theme configuration
```

**Principle:** Physics functions are pure Python — no Streamlit dependency. The UI layer calls solvers and displays results. This makes testing trivial and Phase 2 additions slot in cleanly.

---

## 4. Data Models

```python
@dataclass
class Enclosure:
    length_m: float
    width_m: float
    height_m: float
    volume_m3: float              # Computed: L × W × H
    air_density: float            # kg/m³ (default 1.19)
    air_cp: float                 # J/kg·K (default 1005)
    internal_thermal_mass: float  # J/K (default 50000)
    thermal_capacitance: float    # C_e = ρ·V·cp + C_internal

@dataclass
class HeatLoads:
    baseline_load_w: float        # Default 100
    additional_loads_w: float     # Default 0
    total_load_w: float           # Computed sum

@dataclass
class CoolingPlant:
    cooling_type: str             # "air_coil" | "liquid" | "hybrid"
    coil_approach_temp_c: float   # Default 2°C
    coil_max_capacity_w: float
    chilled_water_temp_c: float
    delta_t_air_c: float
    delta_t_water_c: float        # Default 2°C

@dataclass
class AmbientConditions:
    temperature_c: float          # Default 23.5
    variation_amplitude_c: float  # Default 2.0
    variation_period_hr: float    # For Phase 2
    ua_value: float               # W/K
```

**Solve modes** (explicit selection):
1. Solve airflow given Q and ΔT_air
2. Solve coolant flow given Q and ΔT_water
3. Solve coil leaving temperature
4. Solve heater requirement

---

## 5. UI Design — "Precision Instrument" Aesthetic

### Color Palette
- Background: `#0D1117` (deep charcoal)
- Panel surfaces: `#161B22` with 1px `#30363D` borders
- Primary accent: `#00D4AA` (teal — nominal/active)
- Warning: `#F0A830` (amber)
- Error: `#F85149` (signal red)
- Text primary: `#E6EDF3`
- Text secondary: `#8B949E`
- Units/labels: `#58A6FF`

### Typography
- Values/numbers: **JetBrains Mono** — engineered for numeral legibility
- Labels/headers: **DM Sans** — geometric, clean
- Panel titles: DM Sans Medium, all-caps, letterspaced

### Layout
```
┌─────────────────────────────────────────────────────────┐
│  QUANTUM ENCLOSURE THERMAL ANALYZER    [SI/Imperial] ▼  │
├──────────────┬──────────────────────────────────────────┤
│  INPUT       │  SYSTEM SCHEMATIC                        │
│  PANELS      │  (Plotly figure with live values          │
│  (left col)  │   overlaid on thermal loop diagram)      │
│              │                                          │
│  Geometry    │──────────────────────────────────────────│
│  Loads       │  RESULTS                                 │
│  Ambient     │  [CFM] [L/min] [Coil %] [Heater W]      │
│  Cooling     │  Metric cards with teal/amber/red glow   │
│              │                                          │
│              │  ⚠ Warnings                              │
├──────────────┴──────────────────────────────────────────┤
│  Solve mode: [dropdown]                                 │
└─────────────────────────────────────────────────────────┘
```

### Key Details
- Metric cards: subtle top-border glow — teal (nominal), amber (warning), red (saturated)
- System schematic: Plotly figure with annotations, values update reactively
- Coil utilization: horizontal bar with color gradient teal → amber → red
- Warnings: pill-shaped badges, hardware-indicator style
- Input focus state: teal accent border

---

## 6. Testing Strategy

| Test | Validates |
|---|---|
| `test_solve_airflow` | 100W, ΔT=5°C → ~38 CFM |
| `test_solve_coolant` | 100W, ΔT_water=2°C → ~0.72 L/min |
| `test_solve_coil_temp` | Coil leaving temp from airflow + load |
| `test_solve_heater` | Heater need when ambient drops |
| `test_unit_conversions` | ft↔m, CFM↔m³/s, L/min↔GPM round-trip |
| `test_warnings` | Saturation, heater triggers |
| `test_defaults` | Preloaded case matches spec sanity checks |

---

## 7. Phase 2 Hooks (Not Built in MVP)

The architecture accommodates without refactoring:
- `solvers.py` → `solve_transient()` using `scipy.integrate.solve_ivp`
- `models.py` → `TwoNodeEnclosure` dataclass
- New `src/controllers.py` for PID logic
- Panel 5 (Control Settings) added to `src/ui/`
- Panel 6 gains time-series Plotly charts
- System schematic animates temperature over time

---

## 8. Default Case (Preloaded)

- Dimensions: 4 × 10 × 2.5 ft (1.22 × 3.05 × 0.76 m)
- Volume: ~2.83 m³
- Heat load: 100 W
- Ambient: 23.5 °C ± 2 °C
- Internal thermal mass: 50 kJ/K
- Coil approach: 2 °C
- ΔT_air: 5 °C
- Coolant ΔT_water: 2 °C

**Expected outputs:**
- Required airflow: ~35–40 CFM
- Required coolant: ~0.7 L/min

---

## 9. Acceptance Criteria (MVP)

- [ ] Computes airflow correctly for 100W case
- [ ] Computes coolant flow correctly
- [ ] Allows variable ΔT_air
- [ ] Supports SI/Imperial dual display
- [ ] Produces consistent engineering outputs
- [ ] All pytest tests pass
- [ ] Dashboard loads with preloaded defaults
- [ ] Warnings display for saturation/heater conditions
- [ ] System schematic renders with live values
