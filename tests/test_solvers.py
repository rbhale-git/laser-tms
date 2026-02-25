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
from src.constants import AIR_CP, AIR_DENSITY, WATER_CP
from src.units import m3s_to_cfm, kgs_to_lpm


class TestSolveAirflow:
    """m_dot = Q / (c_p * ΔT_air), then convert to CFM."""

    def test_100w_5c_delta(self):
        result = solve_airflow(q_total_w=100.0, delta_t_air_c=5.0)
        cfm = m3s_to_cfm(result.airflow_m3s)
        assert 35.0 <= cfm <= 42.0

    def test_analytical_value(self):
        result = solve_airflow(q_total_w=100.0, delta_t_air_c=5.0)
        expected_m3s = 100.0 / (AIR_CP * 5.0) / AIR_DENSITY
        assert result.airflow_m3s == pytest.approx(expected_m3s, rel=1e-6)

    def test_zero_load(self):
        result = solve_airflow(q_total_w=0.0, delta_t_air_c=5.0)
        assert result.airflow_m3s == pytest.approx(0.0)

    def test_small_delta_t_large_flow(self):
        result = solve_airflow(q_total_w=100.0, delta_t_air_c=1.0)
        cfm = m3s_to_cfm(result.airflow_m3s)
        assert cfm > 150.0


class TestSolveCoolantFlow:
    """m_dot_water = Q / (c_p_water * ΔT_water)."""

    def test_100w_2c_delta(self):
        result = solve_coolant_flow(q_total_w=100.0, delta_t_water_c=2.0)
        lpm = kgs_to_lpm(result.coolant_kgs)
        assert lpm == pytest.approx(0.72, rel=5e-2)

    def test_analytical_value(self):
        result = solve_coolant_flow(q_total_w=100.0, delta_t_water_c=2.0)
        expected_kgs = 100.0 / (WATER_CP * 2.0)
        assert result.coolant_kgs == pytest.approx(expected_kgs, rel=1e-6)


class TestSolveCoilLeavingTemp:
    """T_coil_out = T_return - Q / (m_dot * c_p)."""

    def test_known_case(self):
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
        result = solve_heater_requirement(
            q_load_w=100.0, ua_value=2.0, ambient_temp_c=23.5, setpoint_c=23.5,
        )
        assert result.heater_required_w == pytest.approx(0.0)

    def test_heater_needed_cold_ambient(self):
        result = solve_heater_requirement(
            q_load_w=10.0, ua_value=2.0, ambient_temp_c=15.0, setpoint_c=23.5,
        )
        assert result.heater_required_w == pytest.approx(7.0, rel=1e-3)


class TestComputeWarnings:
    def test_no_warnings_nominal(self):
        warnings = compute_warnings(coil_utilization_pct=50.0, heater_required_w=0.0)
        assert len(warnings) == 0

    def test_coil_warning_high_utilization(self):
        warnings = compute_warnings(coil_utilization_pct=92.0, heater_required_w=0.0)
        assert any("utilization" in w.lower() for w in warnings)

    def test_coil_error_saturated(self):
        warnings = compute_warnings(coil_utilization_pct=105.0, heater_required_w=0.0)
        assert any("saturated" in w.lower() for w in warnings)

    def test_heater_warning(self):
        warnings = compute_warnings(coil_utilization_pct=10.0, heater_required_w=15.0)
        assert any("heater" in w.lower() for w in warnings)
