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
