"""
IoT Hardware & Embedded Microcontroller Unit (MCU) Power Modeling.
Models low-power states, battery consumption, and energy harvesting.
"""

from enum import Enum
from typing import Dict, Any, Optional
import math


class PowerMode(Enum):
    ACTIVE = "ACTIVE"
    IDLE = "IDLE"
    STANDBY = "STANDBY"
    DEEP_SLEEP = "DEEP_SLEEP"


class MicrocontrollerUnit:
    """
    Simulates a constrained embedded MCU (e.g., ARM Cortex-M0+/M4, ESP32, TI CC2650).
    Tracks clock speed, memory limits, and dynamic current consumption per power state.
    """

    def __init__(
        self,
        mcu_name: str = "Cortex-M4-IoT",
        clock_mhz: float = 64.0,
        ram_kb: int = 64,
        flash_kb: int = 256,
        voltage_v: float = 3.3,
        current_active_ma: float = 12.0,
        current_idle_ma: float = 2.0,
        current_standby_ma: float = 0.040,      # 40 uA
        current_deep_sleep_ma: float = 0.002    # 2 uA
    ):
        self.mcu_name = mcu_name
        self.clock_mhz = clock_mhz
        self.ram_kb = ram_kb
        self.flash_kb = flash_kb
        self.voltage_v = voltage_v

        self.current_draw_ma = {
            PowerMode.ACTIVE: current_active_ma,
            PowerMode.IDLE: current_idle_ma,
            PowerMode.STANDBY: current_standby_ma,
            PowerMode.DEEP_SLEEP: current_deep_sleep_ma
        }

        self.current_mode = PowerMode.DEEP_SLEEP
        self.total_energy_consumed_joules = 0.0

    def set_mode(self, mode: PowerMode):
        self.current_mode = mode

    def get_current_draw_ma(self) -> float:
        return self.current_draw_ma[self.current_mode]

    def get_power_mw(self) -> float:
        """P = V * I in milliwatts."""
        return self.voltage_v * self.get_current_draw_ma()

    def step_time(self, duration_seconds: float) -> float:
        """
        Simulates execution for duration_seconds in current power mode.
        Returns energy consumed in Joules: E = P * t = (V * I / 1000) * t.
        """
        power_watts = (self.voltage_v * self.get_current_draw_ma()) / 1000.0
        energy_joules = power_watts * duration_seconds
        self.total_energy_consumed_joules += energy_joules
        return energy_joules


class Battery:
    """
    Simulates an IoT chemical cell (e.g. Li-SOCl2, CR2032 Coin Cell, Li-Ion).
    Supports coulometric capacity tracking and Peukert's law capacity derating.
    """

    def __init__(
        self,
        nominal_capacity_mah: float = 240.0,  # e.g., standard CR2032
        nominal_voltage_v: float = 3.0,
        peukert_coefficient: float = 1.05
    ):
        self.nominal_capacity_mah = nominal_capacity_mah
        self.remaining_capacity_mah = nominal_capacity_mah
        self.nominal_voltage_v = nominal_voltage_v
        self.peukert_k = peukert_coefficient

    @property
    def state_of_charge(self) -> float:
        """State of Charge (SoC) between 0.0 and 1.0."""
        return max(0.0, min(1.0, self.remaining_capacity_mah / self.nominal_capacity_mah))

    def discharge(self, current_ma: float, duration_hours: float) -> float:
        """
        Discharges battery accounting for Peukert effect.
        Returns remaining capacity in mAh.
        """
        if self.remaining_capacity_mah <= 0:
            return 0.0

        # Effective discharge accounting for Peukert rate
        # I_eff = I * (I / I_nom)^(k - 1)
        effective_draw = (current_ma ** self.peukert_k) / (1.0 ** (self.peukert_k - 1.0))
        consumed_mah = effective_draw * duration_hours

        self.remaining_capacity_mah = max(0.0, self.remaining_capacity_mah - consumed_mah)
        return self.remaining_capacity_mah

    def estimate_lifetime_days(self, average_current_ma: float) -> float:
        """Estimates device operating lifetime in days given an average continuous current."""
        if average_current_ma <= 0:
            return float("inf")
        hours = self.nominal_capacity_mah / average_current_ma
        return round(hours / 24.0, 2)


class EnergyHarvester:
    """
    Simulates an ambient energy harvesting transducer (Solar, Thermoelectric TEG, Piezoelectric).
    Computes energy balance and autonomous perpetual runtime.
    """

    def __init__(self, harvest_type: str = "Solar-Indoor", peak_power_mw: float = 1.5, efficiency: float = 0.85):
        self.harvest_type = harvest_type
        self.peak_power_mw = peak_power_mw
        self.efficiency = efficiency

    def harvest_energy_joules(self, ambient_flux_ratio: float, duration_seconds: float) -> float:
        """
        ambient_flux_ratio: 0.0 (dark) to 1.0 (full illuminance / peak temperature gradient).
        Returns harvested energy in Joules.
        """
        flux = max(0.0, min(1.0, ambient_flux_ratio))
        actual_power_watts = (self.peak_power_mw * flux * self.efficiency) / 1000.0
        return actual_power_watts * duration_seconds

    def compute_energy_neutrality(
        self,
        avg_harvested_mw: float,
        duty_cycle: float,
        active_power_mw: float,
        sleep_power_mw: float
    ) -> Dict[str, Any]:
        """
        Evaluates energy-neutral operation criterion:
        P_harvest >= Duty * P_active + (1 - Duty) * P_sleep
        """
        avg_consumed_mw = (duty_cycle * active_power_mw) + ((1.0 - duty_cycle) * sleep_power_mw)
        is_neutral = avg_harvested_mw >= avg_consumed_mw
        net_surplus_mw = avg_harvested_mw - avg_consumed_mw

        return {
            "avg_harvested_mw": avg_harvested_mw,
            "avg_consumed_mw": round(avg_consumed_mw, 4),
            "net_surplus_mw": round(net_surplus_mw, 4),
            "is_energy_neutral": is_neutral
        }
