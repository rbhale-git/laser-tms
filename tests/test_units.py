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
        assert ft3_to_m3(100.0) == pytest.approx(2.8317, rel=1e-3)

    def test_m3_ft3_roundtrip(self):
        original = 2.83
        assert m3_to_ft3(ft3_to_m3(m3_to_ft3(original))) == pytest.approx(
            m3_to_ft3(original), rel=1e-9
        )


class TestFlowConversions:
    def test_cfm_to_m3s(self):
        assert cfm_to_m3s(40.0) == pytest.approx(0.01888, rel=1e-2)

    def test_m3s_to_cfm(self):
        assert m3s_to_cfm(1.0) == pytest.approx(2118.88, rel=1e-3)

    def test_cfm_roundtrip(self):
        original = 38.0
        assert m3s_to_cfm(cfm_to_m3s(original)) == pytest.approx(original, rel=1e-9)


class TestLiquidFlowConversions:
    def test_kgs_to_lpm(self):
        assert kgs_to_lpm(0.012) == pytest.approx(0.72, rel=2e-2)

    def test_lpm_to_gpm(self):
        assert lpm_to_gpm(1.0) == pytest.approx(0.264172, rel=1e-3)

    def test_gpm_lpm_roundtrip(self):
        original = 0.72
        assert gpm_to_lpm(lpm_to_gpm(original)) == pytest.approx(original, rel=1e-9)
