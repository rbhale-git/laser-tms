# Design: Separate Ambient & Enclosure Setpoint Temperatures

**Date:** 2026-02-26
**Status:** Approved

## Problem

The tool conflates ambient (lab) temperature and enclosure setpoint into a single value. In `app.py`, the heater solver receives the same value for both `ambient_temp_c` and `setpoint_c`, so it always computes 0 W — it can never detect a heating requirement. The enclosure setpoint is a regulated control target; ambient is an unregulated disturbance. They must be modeled separately.

## Design

### Models (`src/models.py`)

Restructure `AmbientConditions`:

| Old field | New field | Default | Description |
|---|---|---|---|
| `temperature_c` | `T_ambient_c` | 23.5 °C | Unregulated lab temperature |
| *(new)* | `T_setpoint_c` | 23.0 °C | Regulated enclosure target |
| `variation_amplitude_c` | `T_ambient_variation_c` | 2.5 °C | Ambient swing amplitude |
| `variation_period_hr` | *(dropped)* | — | Unused; re-add in Phase 2 |
| `ua_value` | `ua_value` | 2.0 W/K | Unchanged |

Computed properties:
- `T_ambient_low` = `T_ambient_c - T_ambient_variation_c`
- `T_ambient_high` = `T_ambient_c + T_ambient_variation_c`

### Solvers (`src/solvers.py`)

No changes. `solve_heater_requirement` already accepts separate `ambient_temp_c` and `setpoint_c`. The fix is at the call site in `app.py`.

### App orchestration (`app.py`)

| Call site | Old value | New value |
|---|---|---|
| `solve_coil_leaving_temp(return_air_temp_c=...)` | `ambient.temperature_c` | `ambient.T_setpoint_c` |
| `solve_heater_requirement(ambient_temp_c=...)` | `ambient.temperature_c` | `ambient.T_ambient_low` |
| `solve_heater_requirement(setpoint_c=...)` | `ambient.temperature_c` | `ambient.T_setpoint_c` |
| `render_schematic(enclosure_temp_c=...)` | `ambient.temperature_c` | `ambient.T_setpoint_c` |
| `render_schematic(return_temp_c=...)` | `ambient.temperature_c` | `ambient.T_setpoint_c` |
| `render_schematic(ambient_temp_c=...)` | `ambient.temperature_c` | `ambient.T_ambient_c` |

### UI panel (`src/ui/panel_ambient.py`)

Two groups:
1. **Enclosure Setpoint (Regulated)** — `T_setpoint` input with helper text
2. **Ambient Environment (Unregulated)** — `T_ambient` + `T_ambient_variation` inputs, computed range display

Dual-unit display (SI + Imperial) preserved.

### Schematic (`src/ui/schematic.py`)

- Inside enclosure: "T_set = 23.0 °C (regulated)"
- Above enclosure: "T_amb = 23.5 °C (unregulated)"

### Defaults (`defaults.py`)

`T_ambient_c=23.5`, `T_setpoint_c=23.0`, `T_ambient_variation_c=2.5`. Drop `variation_period_hr`.

### Physics card (`src/ui/physics_card.py`)

Show `T_set` and `T_amb` as separate entries in the control variable glossary.

### Tests

- Update field names in `test_defaults.py`
- Add heater tests: cold ambient (19 °C, setpoint 23 °C) requires heating; warm ambient (25 °C, setpoint 23 °C) requires 0 W
- Airflow/coolant tests unchanged

## Validation

Default case still produces ~35.4 CFM and ~0.72 L/min (unaffected by split). Heater at worst-case ambient: `max(0, 2.0*(23.0 - 21.0) - 100) = 0 W` — load dominates.
