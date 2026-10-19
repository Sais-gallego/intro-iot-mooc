"""
IoT Sensing Layer: ADC Conversion, Nyquist-Shannon Sampling, and Signal Filtering.
Implements Moving Average, Exponential Smoothing, and 1D Kalman Filter.
"""

from typing import List, Dict, Any, Optional
import math


class AnalogToDigitalConverter:
    """
    Models a Successive Approximation Register (SAR) or Delta-Sigma ADC.
    Simulates quantization step size, digital code generation, and SNR/ENOB.
    """

    def __init__(self, resolution_bits: int = 12, vref_volts: float = 3.3):
        if resolution_bits <= 0:
            raise ValueError("ADC resolution bits must be positive")
        self.resolution_bits = resolution_bits
        self.vref_volts = vref_volts
        self.max_digital_code = (1 << resolution_bits) - 1
        self.lsb_volts = vref_volts / self.max_digital_code

    def convert_voltage_to_code(self, vin: float) -> int:
        """Converts analog voltage to quantized integer ADC code."""
        clamped_v = max(0.0, min(self.vref_volts, vin))
        code = round(clamped_v / self.lsb_volts)
        return int(min(self.max_digital_code, max(0, code)))

    def reconstruct_voltage(self, code: int) -> float:
        """Reconstructs estimated analog voltage from digital code."""
        clamped_code = max(0, min(self.max_digital_code, code))
        return round(clamped_code * self.lsb_volts, 5)

    def calculate_theoretical_snr_db(self) -> float:
        """Ideal quantization SNR = 6.02 * N + 1.76 dB."""
        return round(6.02 * self.resolution_bits + 1.76, 2)


class NyquistSamplingValidator:
    """Validates sampling frequency and calculates aliased frequencies under under-sampling."""

    @staticmethod
    def is_nyquist_satisfied(sampling_rate_hz: float, signal_max_freq_hz: float) -> bool:
        """Nyquist-Shannon theorem: f_s >= 2 * f_max."""
        return sampling_rate_hz >= (2.0 * signal_max_freq_hz)

    @staticmethod
    def calculate_alias_frequency(signal_freq_hz: float, sampling_rate_hz: float) -> float:
        """Calculates apparent frequency seen when signal is under-sampled."""
        if sampling_rate_hz <= 0:
            return 0.0
        # Fold into [0, f_s / 2]
        nyquist_limit = sampling_rate_hz / 2.0
        rem = signal_freq_hz % sampling_rate_hz
        if rem > nyquist_limit:
            return round(sampling_rate_hz - rem, 3)
        return round(rem, 3)


class MovingAverageFilter:
    """Sliding window finite impulse response (FIR) moving average filter."""

    def __init__(self, window_size: int = 5):
        if window_size <= 0:
            raise ValueError("Window size must be greater than zero")
        self.window_size = window_size
        self.buffer: List[float] = []

    def update(self, measurement: float) -> float:
        self.buffer.append(measurement)
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)
        return sum(self.buffer) / len(self.buffer)


class ExponentialMovingAverage:
    """Infinite impulse response (IIR) single-pole low-pass exponential smoothing."""

    def __init__(self, alpha: float = 0.2):
        if not (0.0 < alpha <= 1.0):
            raise ValueError("Smoothing factor alpha must be in (0, 1]")
        self.alpha = alpha
        self.current_estimate: Optional[float] = None

    def update(self, measurement: float) -> float:
        if self.current_estimate is None:
            self.current_estimate = measurement
        else:
            self.current_estimate = (self.alpha * measurement) + ((1.0 - self.alpha) * self.current_estimate)
        return self.current_estimate


class OneDimensionalKalmanFilter:
    """
    1D discrete-time linear Kalman filter for sensor noise filtering.
    Optimal minimum mean-square error (MMSE) estimator for Gaussian white noise.
    """

    def __init__(
        self,
        process_noise_q: float = 1e-4,
        measurement_noise_r: float = 1e-2,
        initial_estimate: float = 0.0,
        initial_covariance_p: float = 1.0
    ):
        self.q = process_noise_q
        self.r = measurement_noise_r
        self.x_hat = initial_estimate
        self.p = initial_covariance_p
        self.kalman_gain = 0.0

    def step(self, measurement_z: float) -> float:
        # 1. Time Update (Predict)
        # x_hat_prior = x_hat
        p_prior = self.p + self.q

        # 2. Measurement Update (Correct)
        self.kalman_gain = p_prior / (p_prior + self.r)
        self.x_hat = self.x_hat + self.kalman_gain * (measurement_z - self.x_hat)
        self.p = (1.0 - self.kalman_gain) * p_prior

        return self.x_hat
