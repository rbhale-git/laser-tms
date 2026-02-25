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
