# Laser Enclosure Thermal Modelling Tool

Steady-state thermal modelling tool for precision temperature-controlled laser enclosures. Built with Streamlit and designed for lab engineers who need to quickly size airflow, coolant flow, and heat exchanger capacity for enclosures that must hold tight temperature tolerances.

## Problem Statement

Laser systems generate continuous heat loads (~100 W typical) inside sealed enclosures that must maintain temperature stability within +-0.1 degC. Engineers need to answer:

- **How much airflow** is required to remove the heat load for a given air-side delta-T?
- **How much coolant flow** does the chilled water coil need?
- **What is the coil leaving air temperature** supplied back to the enclosure?
- **Is supplemental heating required** when ambient conditions drop below setpoint?
- **Is the coil capacity sufficient**, or is the heat exchanger saturated?

This tool answers all of these from first principles using a single-node energy balance model.

## Features

- **Interactive Streamlit dashboard** with three-column layout (inputs | schematic | results)
- **Four solve modes**: Airflow, Coolant, Coil Temperature, Heater requirement
- **Live system schematic** rendered with Plotly, showing temperatures, flow rates, and heat paths
- **Physics breakdown card** with governing equations and live variable substitution
- **Dual unit display** (SI and Imperial) throughout
- **Real-time warnings** for coil saturation and heater requirements
- **Dark "Precision Instrument" theme** with JetBrains Mono numerics and DM Sans labels

## Physics Model

Single-node lumped capacitance energy balance at steady state:

```
C_e * dT_e/dt = Q_load + UA * (T_a - T_e) + m_dot_air * c_p * (T_sup - T_e)
```

At steady state (`dT_e/dt = 0`), the solver computes:

| Quantity | Equation |
|----------|----------|
| Airflow | `m_dot = Q / (c_p * dT_air)` |
| Coolant flow | `m_dot_w = Q / (c_p_w * dT_water)` |
| Coil leaving temp | `T_sup = T_return - Q / (m_dot_air * c_p)` |
| Heater requirement | `Q_heater = max(0, UA * (T_set - T_amb) - Q_load)` |

**Constants used:**
- Air specific heat: 1005 J/(kg*K)
- Air density: 1.19 kg/m^3
- Water specific heat: 4186 J/(kg*K)

## Default Validation Case

A 4 x 10 x 2.5 ft enclosure with 100 W heat load, 5 degC air delta-T, 2 degC water delta-T:

| Parameter | Expected | Computed |
|-----------|----------|----------|
| Required airflow | 35-40 CFM | 35.4 CFM |
| Coolant flow | ~0.7 L/min | 0.72 L/min |
| Heater at 23.5 degC ambient | 0 W | 0 W |

## Quick Start

```bash
# Clone
git clone https://github.com/rbhale-git/laser-tms.git
cd laser-tms

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py

# Run tests
pytest tests/ -v
```

## Project Structure

```
thermal-enclosure/
├── app.py                    # Streamlit entry point — composes UI, builds models, calls solvers
├── defaults.py               # Factory functions for 100 W default case
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── config.toml           # Dark theme configuration
├── src/
│   ├── constants.py          # Physical constants and conversion factors
│   ├── models.py             # Dataclasses: Enclosure, HeatLoads, CoolingPlant, AmbientConditions
│   ├── solvers.py            # Pure solver functions returning SolverResult dataclasses
│   ├── units.py              # Unit conversion functions (SI <-> Imperial)
│   └── ui/
│       ├── theme.py          # "Precision Instrument" CSS theme injection
│       ├── panel_geometry.py # Enclosure dimensions input panel
│       ├── panel_loads.py    # Heat load input panel
│       ├── panel_ambient.py  # Ambient conditions input panel
│       ├── panel_cooling.py  # Cooling plant configuration panel
│       ├── panel_results.py  # Computed results display with metric cards
│       ├── schematic.py      # Plotly system schematic diagram
│       └── physics_card.py   # Governing equations and control variable glossary
├── tests/
│   ├── test_units.py         # 11 unit conversion tests with roundtrip verification
│   ├── test_solvers.py       # 13 solver tests validating physics equations
│   └── test_defaults.py      # 4 tests validating 100 W default case against spec
└── docs/
    └── plans/                # Design and implementation documents
```

## Architecture

The codebase follows a strict **model / solver / UI** separation:

1. **Models** (`src/models.py`) — Pure dataclasses with computed properties. All values stored in SI units internally. No UI or solver logic.

2. **Solvers** (`src/solvers.py`) — Pure functions that take physical parameters and return `SolverResult` dataclasses. No Streamlit imports. Fully testable in isolation.

3. **UI** (`src/ui/`) — Streamlit rendering functions. Each panel is a separate module returning a dict of user inputs. The main `app.py` orchestrates: collect inputs -> build models -> call solvers -> display results.

4. **Units** (`src/units.py`) — Bidirectional conversion functions between SI and Imperial. Used at the display boundary only; all internal computation is SI.

## Solve Modes

| Mode | Solves For | User Provides |
|------|-----------|---------------|
| **Airflow** | Required air volume flow | Heat load, air delta-T |
| **Coolant** | Required coolant mass flow | Heat load, water delta-T |
| **Coil Temp** | Coil leaving air temperature | Heat load, airflow rate |
| **Heater** | Supplemental heating requirement | Heat load, UA, ambient temp |

The selected solve mode disables the corresponding input field and shows a "SOLVING" badge.

## Testing

28 tests organized across three modules:

```bash
# Run all tests
pytest tests/ -v

# Run specific module
pytest tests/test_solvers.py -v

# Run single test
pytest tests/test_solvers.py::TestSolveAirflow::test_100w_5c_delta -v
```

Tests validate:
- Unit conversion accuracy and roundtrip consistency
- Solver physics against hand calculations
- Default case outputs against engineering spec bounds

## Roadmap

**Phase 1 (Current):** Steady-state sizing — single operating point analysis.

**Phase 2:** Transient simulation — time-domain response with PID control loop modeling, disturbance rejection analysis, ambient temperature cycling.

**Phase 3:** Advanced features — multi-zone modeling, component database, report export, optimization routines.

## Tech Stack

- **Python 3.10+**
- **Streamlit** >= 1.30.0 — Dashboard framework
- **Plotly** >= 5.18.0 — Interactive system schematic
- **NumPy** >= 1.26.0 — Numerical computation
- **pytest** >= 7.4.0 — Test framework

## License

MIT
