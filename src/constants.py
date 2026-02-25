"""Physical constants and conversion factors for thermal analysis."""

# Air properties at ~20-25°C, 1 atm
AIR_CP = 1005.0        # J/(kg·K) - specific heat capacity
AIR_DENSITY = 1.19      # kg/m³ - density at ~23°C

# Water properties at ~15-20°C
WATER_CP = 4186.0       # J/(kg·K) - specific heat capacity
WATER_DENSITY = 998.0    # kg/m³

# Length conversions
FT_TO_M = 0.3048
M_TO_FT = 1.0 / FT_TO_M

# Volume conversions
FT3_TO_M3 = FT_TO_M ** 3
M3_TO_FT3 = M_TO_FT ** 3

# Flow conversions
M3S_TO_CFM = 2118.88    # 1 m³/s ≈ 2119 CFM
CFM_TO_M3S = 1.0 / M3S_TO_CFM

# Liquid flow conversions
KGS_TO_LPM_WATER = 60.0 / WATER_DENSITY * 1000.0  # kg/s → L/min
LPM_TO_GPM = 0.264172   # L/min → US gallons/min
GPM_TO_LPM = 1.0 / LPM_TO_GPM

# Temperature (offsets only — °C and K have same scale)
CELSIUS_TO_KELVIN_OFFSET = 273.15
