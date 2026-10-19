"""
Unit tests for IoT Sensing Layer: ADC conversion, Nyquist sampling, and digital filters.
"""

import unittest
from src.sensing_pipeline import (
    AnalogToDigitalConverter,
    NyquistSamplingValidator,
    MovingAverageFilter,
    ExponentialMovingAverage,
    OneDimensionalKalmanFilter,
)


class TestSensingPipeline(unittest.TestCase):
    def test_adc_quantization_and_reconstruction(self):
        adc12 = AnalogToDigitalConverter(resolution_bits=12, vref_volts=3.3)
        self.assertEqual(adc12.max_digital_code, 4095)
        self.assertAlmostEqual(adc12.lsb_volts, 3.3 / 4095, places=5)

        # 0V -> code 0
        self.assertEqual(adc12.convert_voltage_to_code(0.0), 0)
        # 3.3V -> code 4095
        self.assertEqual(adc12.convert_voltage_to_code(3.3), 4095)
        # 1.65V (half scale) -> code ~2048
        code_half = adc12.convert_voltage_to_code(1.65)
        self.assertIn(code_half, (2047, 2048))

        # Reconstructed voltage
        v_recon = adc12.reconstruct_voltage(code_half)
        self.assertAlmostEqual(v_recon, 1.65, places=2)

        # SNR calculation (6.02 * 12 + 1.76 = 74.0 dB)
        self.assertEqual(adc12.calculate_theoretical_snr_db(), 74.0)

    def test_nyquist_validator(self):
        # 100 Hz signal, 250 Hz sampling -> Nyquist satisfied
        self.assertTrue(NyquistSamplingValidator.is_nyquist_satisfied(250.0, 100.0))
        # 100 Hz signal, 150 Hz sampling -> Violation
        self.assertFalse(NyquistSamplingValidator.is_nyquist_satisfied(150.0, 100.0))

        # Aliasing calculation: 80 Hz signal sampled at 100 Hz
        # Nyquist limit = 50 Hz. Apparent frequency = 100 - 80 = 20 Hz
        alias = NyquistSamplingValidator.calculate_alias_frequency(80.0, 100.0)
        self.assertEqual(alias, 20.0)

    def test_moving_average_filter(self):
        ma = MovingAverageFilter(window_size=3)
        self.assertEqual(ma.update(10.0), 10.0)
        self.assertEqual(ma.update(20.0), 15.0)
        self.assertEqual(ma.update(30.0), 20.0)
        # Next value replaces oldest (10.0)
        self.assertEqual(ma.update(40.0), 30.0)

    def test_exponential_moving_average(self):
        ema = ExponentialMovingAverage(alpha=0.5)
        self.assertEqual(ema.update(10.0), 10.0)
        # y1 = 0.5 * 20 + 0.5 * 10 = 15.0
        self.assertEqual(ema.update(20.0), 15.0)
        # y2 = 0.5 * 30 + 0.5 * 15 = 22.5
        self.assertEqual(ema.update(30.0), 22.5)

    def test_kalman_filter_noise_suppression(self):
        # True value is constant 25.0 degrees C, corrupted by Gaussian noise
        kf = OneDimensionalKalmanFilter(
            process_noise_q=1e-4,
            measurement_noise_r=0.1,
            initial_estimate=20.0,
            initial_covariance_p=1.0
        )
        noisy_measurements = [24.8, 25.3, 24.9, 25.2, 25.1, 24.7, 25.0, 25.2]
        estimates = []
        for z in noisy_measurements:
            estimates.append(kf.step(z))

        # After several iterations, estimate should be close to 25.0
        final_estimate = estimates[-1]
        self.assertAlmostEqual(final_estimate, 25.0, places=1)
        # Covariance P should decrease monotonically with updates
        self.assertLess(kf.p, 1.0)


if __name__ == "__main__":
    unittest.main()
