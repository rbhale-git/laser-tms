"""SI <-> Imperial unit conversion helpers.

All functions are pure -- no side effects. Internal calculations always use SI.
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
