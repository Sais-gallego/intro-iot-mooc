"""
Unit tests for IoT Hardware MCU, Battery, Energy Harvesting, and RTOS Scheduling.
"""

import unittest
from src.device_hardware import PowerMode, MicrocontrollerUnit, Battery, EnergyHarvester
from src.operating_systems import TaskState, Task, Mutex, RtosScheduler


class TestDeviceHardware(unittest.TestCase):
    def setUp(self):
        self.mcu = MicrocontrollerUnit(voltage_v=3.3)
        self.battery = Battery(nominal_capacity_mah=240.0)
        self.harvester = EnergyHarvester(peak_power_mw=2.0)

    def test_mcu_power_modes_and_energy(self):
        self.assertEqual(self.mcu.current_mode, PowerMode.DEEP_SLEEP)
        self.assertEqual(self.mcu.get_current_draw_ma(), 0.002)

        # Switch to ACTIVE
        self.mcu.set_mode(PowerMode.ACTIVE)
        self.assertEqual(self.mcu.get_current_draw_ma(), 12.0)
        p_mw = self.mcu.get_power_mw()
        self.assertAlmostEqual(p_mw, 3.3 * 12.0)

        # Step 10 seconds active
        energy_j = self.mcu.step_time(10.0)
        expected_j = (3.3 * 0.012) * 10.0
        self.assertAlmostEqual(energy_j, expected_j)
        self.assertAlmostEqual(self.mcu.total_energy_consumed_joules, expected_j)

    def test_battery_discharge_and_lifetime(self):
        self.assertEqual(self.battery.state_of_charge, 1.0)
        # Discharge at 10 mA for 1 hour
        rem = self.battery.discharge(current_ma=10.0, duration_hours=1.0)
        self.assertLess(rem, 240.0)
        self.assertLess(self.battery.state_of_charge, 1.0)

        # Lifetime estimation: 0.1 mA average current
        days = self.battery.estimate_lifetime_days(average_current_ma=0.1)
        # 240 / 0.1 = 2400 hours = 100 days
        self.assertEqual(days, 100.0)

    def test_energy_harvester_neutrality(self):
        # 100 seconds at 50% flux
        joules = self.harvester.harvest_energy_joules(0.5, 100.0)
        self.assertGreater(joules, 0.0)

        # Check neutrality: 1 mW harvested, 1% duty cycle active (40 mW) + 99% sleep (0.01 mW)
        neutral_eval = self.harvester.compute_energy_neutrality(
            avg_harvested_mw=1.0,
            duty_cycle=0.01,
            active_power_mw=40.0,
            sleep_power_mw=0.01
        )
        # 0.01 * 40 + 0.99 * 0.01 = 0.4 + 0.0099 = 0.4099 mW < 1.0 mW
        self.assertTrue(neutral_eval["is_energy_neutral"])
        self.assertGreater(neutral_eval["net_surplus_mw"], 0.5)


class TestRtosScheduling(unittest.TestCase):
    def test_preemptive_priority_scheduling(self):
        scheduler = RtosScheduler(is_preemptive=True)
        t_low = Task(task_id="t1", name="TelemetryTask", base_priority=1, workload_ticks=3)
        t_high = Task(task_id="t2", name="CriticalAlertTask", base_priority=5, workload_ticks=2)

        scheduler.add_task(t_low)
        scheduler.add_task(t_high)

        # Simulate 5 ticks
        trace = scheduler.run_simulation(5)
        # Higher priority CriticalAlertTask must run first for 2 ticks
        self.assertEqual(trace[0]["running"], "CriticalAlertTask")
        self.assertEqual(trace[1]["running"], "CriticalAlertTask")
        # Then TelemetryTask takes over
        self.assertEqual(trace[2]["running"], "TelemetryTask")
        self.assertEqual(trace[3]["running"], "TelemetryTask")
        self.assertEqual(trace[4]["running"], "TelemetryTask")

    def test_priority_inheritance_protocol(self):
        mutex = Mutex("SPI_BUS_MUTEX")
        t_low = Task(task_id="t1", name="LowTask", base_priority=1, workload_ticks=4)
        t_high = Task(task_id="t3", name="HighTask", base_priority=10, workload_ticks=2)

        # Low task acquires mutex
        acquired = mutex.acquire(t_low)
        self.assertTrue(acquired)
        self.assertEqual(t_low.current_priority, 1)

        # High task attempts to acquire same mutex -> BLOCKED, priority inherited by low task!
        blocked = mutex.acquire(t_high)
        self.assertFalse(blocked)
        self.assertEqual(t_high.state, TaskState.BLOCKED)
        self.assertEqual(t_low.current_priority, 10)  # Inherited high priority

        # Low task finishes critical section and releases mutex
        woken = mutex.release(t_low)
        self.assertEqual(t_low.current_priority, 1)  # Restored to base priority
        self.assertEqual(woken, t_high)
        self.assertEqual(t_high.state, TaskState.READY)
        self.assertEqual(mutex.owner, t_high)


if __name__ == "__main__":
    unittest.main()
