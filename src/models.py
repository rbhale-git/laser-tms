"""Dataclass models for thermal enclosure system components.

All values stored in SI units internally.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

from src.constants import AIR_CP, AIR_DENSITY



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
    coil_approach_temp_c: float = 2.0
    coil_max_capacity_w: float = 500.0
    chilled_water_temp_c: float = 15.0
    delta_t_air_c: float = 5.0
    delta_t_water_c: float = 2.0


@dataclass
class AmbientConditions:
    T_ambient_c: float = 23.5
    T_setpoint_c: float = 23.0
    T_ambient_variation_c: float = 5.5
    ua_value: float = 2.0  # W/K

    @property
    def T_ambient_low(self) -> float:
        """Worst-case cold ambient (T_ambient - variation)."""
        return self.T_ambient_c - self.T_ambient_variation_c

    @property
    def T_ambient_high(self) -> float:
        """Worst-case hot ambient (T_ambient + variation)."""
        return self.T_ambient_c + self.T_ambient_variation_c
