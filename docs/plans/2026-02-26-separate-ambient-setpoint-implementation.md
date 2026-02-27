# Separate Ambient & Setpoint Temperatures — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Decouple ambient (lab) temperature and enclosure setpoint into separate inputs throughout models, solvers, UI, and tests so the heater solver correctly evaluates worst-case ambient conditions.

**Architecture:** The `AmbientConditions` dataclass gains `T_setpoint_c` and renames fields for clarity. Solvers are unchanged — the fix is at the call site in `app.py` where both `ambient_temp_c` and `setpoint_c` currently receive the same value. UI panel splits into two labeled groups.

**Tech Stack:** Python 3.10+, Streamlit, Plotly, pytest

---

### Task 1: Update AmbientConditions model

**Files:**
- Modify: `src/models.py:67-73`

**Step 1: Replace the AmbientConditions dataclass**

Replace lines 67–73 with:

```python
@dataclass
class AmbientConditions:
    T_ambient_c: float = 23.5
    T_setpoint_c: float = 23.0
    T_ambient_variation_c: float = 2.5
    ua_value: float = 2.0  # W/K

    @property
    def T_ambient_low(self) -> float:
        """Worst-case cold ambient (T_ambient - variation)."""
        return self.T_ambient_c - self.T_ambient_variation_c

    @property
    def T_ambient_high(self) -> float:
        """Worst-case hot ambient (T_ambient + variation)."""
        return self.T_ambient_c + self.T_ambient_variation_c
```

**Step 2: Run existing tests to confirm they fail**

Run: `pytest tests/ -v 2>&1 | head -40`
Expected: Failures in test_defaults.py due to renamed fields (`temperature_c` → `T_ambient_c`).

**Step 3: Commit**

```bash
git add src/models.py
git commit -m "refactor: rename AmbientConditions fields, add T_setpoint_c and computed properties"
```

---

### Task 2: Update defaults factory

**Files:**
- Modify: `defaults.py:42-48`

**Step 1: Update default_ambient()**

Replace the function body:

```python
def default_ambient() -> AmbientConditions:
    return AmbientConditions(
        T_ambient_c=23.5,
        T_setpoint_c=23.0,
        T_ambient_variation_c=2.5,
        ua_value=2.0,
    )
```

**Step 2: Commit**

```bash
git add defaults.py
git commit -m "refactor: update default_ambient to use new field names and values"
```

---

### Task 3: Update tests — new heater tests + fix field references

**Files:**
- Modify: `tests/test_defaults.py:44-53`
- Modify: `tests/test_solvers.py:70-83`

**Step 1: Fix test_defaults.py heater test**

Replace `test_no_heater_at_nominal_ambient` (lines 44–53):

```python
    def test_no_heater_at_nominal_ambient(self):
        loads = default_heat_loads()
        ambient = default_ambient()
        result = solve_heater_requirement(
            q_load_w=loads.total_load_w,
            ua_value=ambient.ua_value,
            ambient_temp_c=ambient.T_ambient_c,
            setpoint_c=ambient.T_setpoint_c,
        )
        assert result.heater_required_w == pytest.approx(0.0)
```

**Step 2: Add new heater tests in test_solvers.py**

Add two tests to `TestSolveHeaterRequirement`:

```python
    def test_heater_needed_cold_ambient_below_setpoint(self):
        """T_amb=19°C, T_set=23°C, UA=2 → loss=8W, load=5W → heater=3W."""
        result = solve_heater_requirement(
            q_load_w=5.0, ua_value=2.0, ambient_temp_c=19.0, setpoint_c=23.0,
        )
        assert result.heater_required_w == pytest.approx(3.0, rel=1e-3)

    def test_no_heater_warm_ambient_above_setpoint(self):
        """T_amb=25°C, T_set=23°C → ambient warmer than setpoint, no heating."""
        result = solve_heater_requirement(
            q_load_w=100.0, ua_value=2.0, ambient_temp_c=25.0, setpoint_c=23.0,
        )
        assert result.heater_required_w == pytest.approx(0.0)
```

**Step 3: Run tests to verify the solver tests pass**

Run: `pytest tests/test_solvers.py -v`
Expected: All pass (solvers unchanged, tests use raw floats).

**Step 4: Run defaults tests to verify they pass**

Run: `pytest tests/test_defaults.py -v`
Expected: All 4 pass (field names now match updated model and factory).

**Step 5: Commit**

```bash
git add tests/test_solvers.py tests/test_defaults.py
git commit -m "test: add heater solver tests for separated ambient/setpoint, fix field refs"
```

---

### Task 4: Update ambient UI panel

**Files:**
- Modify: `src/ui/panel_ambient.py` (full rewrite)

**Step 1: Rewrite panel_ambient.py**

```python
"""Panel 3: Enclosure setpoint and ambient environment inputs."""
import streamlit as st


def render_ambient_panel() -> dict:
    """Render setpoint and ambient inputs, return values in SI.

    Returns dict with keys: T_setpoint_c, T_ambient_c, T_ambient_variation_c,
    ua_value, ua_mode.
    """
    # ── Group 1: Enclosure Setpoint (Regulated) ──────────
    with st.expander("ENCLOSURE SETPOINT", expanded=True):
        setpoint = st.number_input(
            "Setpoint temperature (°C)",
            value=23.0,
            min_value=10.0,
            max_value=40.0,
            step=0.5,
        )
        setpoint_f = setpoint * 9.0 / 5.0 + 32.0
        st.caption(f"{setpoint_f:.1f} °F")
        st.markdown(
            '<span class="eq-assume" style="font-size:0.78em">'
            "The temperature the cooling system actively maintains "
            "inside the enclosure (\u00b10.1 \u00b0C). Set this to match the "
            "average ambient so opening the lid causes minimal disturbance."
            "</span>",
            unsafe_allow_html=True,
        )

    # ── Group 2: Ambient Environment (Unregulated) ───────
    with st.expander("AMBIENT ENVIRONMENT", expanded=True):
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
                value=2.5,
                min_value=0.0,
                max_value=10.0,
                step=0.5,
                help="Peak amplitude of ambient temperature swing",
            )

        t_low = temp - variation
        t_high = temp + variation
        t_low_f = t_low * 9.0 / 5.0 + 32.0
        t_high_f = t_high * 9.0 / 5.0 + 32.0
        temp_f = temp * 9.0 / 5.0 + 32.0
        st.caption(f"{temp_f:.1f} °F")
        st.markdown(
            f"**Ambient range:** {t_low:.1f} °C to {t_high:.1f} °C "
            f"({t_low_f:.1f} °F to {t_high_f:.1f} °F)"
        )
        st.markdown(
            '<span class="eq-assume" style="font-size:0.78em">'
            "The surrounding lab temperature. This is a disturbance the "
            "system must counteract — it is not controlled."
            "</span>",
            unsafe_allow_html=True,
        )

        # ── UA coupling input ────────────────────────────
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
            st.caption("Note: UA computed using enclosure volume from Panel 1")
            ua = ach  # Will be converted in app.py using actual volume

    return {
        "T_setpoint_c": setpoint,
        "T_ambient_c": temp,
        "T_ambient_variation_c": variation,
        "ua_value": ua,
        "ua_mode": ua_mode,
    }
```

**Step 2: Commit**

```bash
git add src/ui/panel_ambient.py
git commit -m "feat: split ambient panel into setpoint (regulated) and ambient (unregulated) groups"
```

---

### Task 5: Update app.py orchestration

**Files:**
- Modify: `app.py:122-165` (model build + solver calls)
- Modify: `app.py:183-209` (schematic + physics card calls)

**Step 1: Update AmbientConditions construction (lines 127–132)**

Replace:

```python
ambient = AmbientConditions(
    temperature_c=ambient_input["temperature_c"],
    variation_amplitude_c=ambient_input["variation_amplitude_c"],
    variation_period_hr=ambient_input["variation_period_hr"],
    ua_value=ua_value,
)
```

With:

```python
ambient = AmbientConditions(
    T_ambient_c=ambient_input["T_ambient_c"],
    T_setpoint_c=ambient_input["T_setpoint_c"],
    T_ambient_variation_c=ambient_input["T_ambient_variation_c"],
    ua_value=ua_value,
)
```

**Step 2: Fix coil solver call (lines 154–158)**

Replace `return_air_temp_c=ambient.temperature_c` with:

```python
coil_result = solve_coil_leaving_temp(
    q_total_w=q_total,
    airflow_kgs=air_result.airflow_kgs,
    return_air_temp_c=ambient.T_setpoint_c,
)
```

**Step 3: Fix heater solver call (lines 160–165)**

Replace:

```python
heater_result = solve_heater_requirement(
    q_load_w=q_total,
    ua_value=ambient.ua_value,
    ambient_temp_c=ambient.temperature_c,
    setpoint_c=ambient.temperature_c,
)
```

With:

```python
heater_result = solve_heater_requirement(
    q_load_w=q_total,
    ua_value=ambient.ua_value,
    ambient_temp_c=ambient.T_ambient_low,
    setpoint_c=ambient.T_setpoint_c,
)
```

**Step 4: Fix schematic call (lines 183–193)**

Replace:

```python
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
```

With:

```python
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
```

**Step 5: Fix physics card call (lines 196–209)**

Replace `ambient_temp_c=ambient.temperature_c` and `setpoint_c=ambient.temperature_c`:

```python
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
```

**Step 6: Run all tests**

Run: `pytest tests/ -v`
Expected: All pass.

**Step 7: Commit**

```bash
git add app.py
git commit -m "fix: pass separate T_setpoint and T_ambient to solvers, schematic, physics card"
```

---

### Task 6: Update schematic labels

**Files:**
- Modify: `src/ui/schematic.py:52-71` (enclosure annotations)
- Modify: `src/ui/schematic.py:123-135` (ambient annotation)

**Step 1: Update enclosure temperature label (line 58–61)**

Replace:

```python
    fig.add_annotation(
        x=3.0, y=5.8, text=f"T = {enclosure_temp_c:.1f} °C",
        font=dict(color=TEAL, size=17, family="JetBrains Mono"),
        showarrow=False,
    )
```

With:

```python
    fig.add_annotation(
        x=3.0, y=5.8, text=f"T<sub>set</sub> = {enclosure_temp_c:.1f} °C",
        font=dict(color=TEAL, size=17, family="JetBrains Mono"),
        showarrow=False,
    )
    fig.add_annotation(
        x=3.0, y=5.05, text="(regulated)",
        font=dict(color=MUTED, size=10, family="DM Sans"),
        showarrow=False,
    )
```

**Step 2: Shift existing annotations down to make room**

Move `Q_load` annotation from y=4.55 to y=4.2 and `UA` from y=3.45 to y=3.3.

**Step 3: Update ambient label (lines 130–135)**

Replace:

```python
    fig.add_annotation(
        x=3.0, y=9.45,
        text=f"Ambient  {ambient_temp_c:.1f} °C",
        font=dict(color=MUTED, size=12, family="JetBrains Mono"),
        showarrow=False,
    )
```

With:

```python
    fig.add_annotation(
        x=3.0, y=9.45,
        text=f"T<sub>amb</sub> = {ambient_temp_c:.1f} °C",
        font=dict(color=MUTED, size=12, family="JetBrains Mono"),
        showarrow=False,
    )
    fig.add_annotation(
        x=3.0, y=9.0,
        text="(unregulated)",
        font=dict(color=MUTED, size=9, family="DM Sans"),
        showarrow=False,
    )
```

**Step 4: Commit**

```bash
git add src/ui/schematic.py
git commit -m "feat: label T_set (regulated) inside enclosure, T_amb (unregulated) outside"
```

---

### Task 7: Update physics card control variable glossary

**Files:**
- Modify: `src/ui/physics_card.py:168-174` (T_a row in variable table)

**Step 1: Split T_a row into T_set and T_amb**

Replace the single `T_a` row:

```python
        '<tr>'
        '<td class="var-sym">T<sub>a</sub></td>'
        '<td class="var-desc">Ambient (lab) temperature</td>'
        f'<td class="var-val">{ambient_temp_c:.1f} &deg;C</td>'
        '<td class="var-control">Lab HVAC setpoint</td>'
        '</tr>'
```

With two rows:

```python
        '<tr>'
        '<td class="var-sym">T<sub>set</sub></td>'
        '<td class="var-desc">Enclosure setpoint (regulated)</td>'
        f'<td class="var-val">{setpoint_c:.1f} &deg;C</td>'
        '<td class="var-control">Cooling system target</td>'
        '</tr>'
        '<tr>'
        '<td class="var-sym">T<sub>amb</sub></td>'
        '<td class="var-desc">Ambient lab temperature (unregulated)</td>'
        f'<td class="var-val">{ambient_temp_c:.1f} &deg;C</td>'
        '<td class="var-control">Lab HVAC / environment</td>'
        '</tr>'
```

**Step 2: Run full test suite**

Run: `pytest tests/ -v`
Expected: All pass (physics card is display-only, no test coverage).

**Step 3: Commit**

```bash
git add src/ui/physics_card.py
git commit -m "feat: show T_set and T_amb as separate entries in physics card glossary"
```

---

### Task 8: Final verification

**Step 1: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests pass (should be 30 total — 28 original + 2 new heater tests).

**Step 2: Verify default case math**

Airflow: `100 / (1005 * 5) / 1.19 * 2118.88 ≈ 35.4 CFM` — unchanged.
Coolant: `100 / (4186 * 2) * 60/998*1000 ≈ 0.72 L/min` — unchanged.
Heater at worst-case: `max(0, 2*(23.0-21.0) - 100) = max(0, -96) = 0 W` — still 0.

**Step 3: Commit**

No commit needed if all prior commits are clean.
