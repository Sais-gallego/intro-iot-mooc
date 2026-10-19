"""
IoT Data Management Layer: Edge Stream Windowing, Compression, and Aggregation.
"""

from typing import List, Dict, Any, Optional
import math


class StreamWindow:
    """Computes real-time streaming aggregates over fixed windows."""

    @staticmethod
    def tumbling_window_aggregates(data: List[float], window_size: int) -> List[Dict[str, float]]:
        """Splits time-series into non-overlapping contiguous windows and computes aggregates."""
        if window_size <= 0:
            raise ValueError("Window size must be greater than zero")

        results = []
        for i in range(0, len(data), window_size):
            chunk = data[i:i + window_size]
            if not chunk:
                continue
            mean_val = sum(chunk) / len(chunk)
            variance = sum((x - mean_val) ** 2 for x in chunk) / len(chunk)
            results.append({
                "count": len(chunk),
                "mean": round(mean_val, 3),
                "min": min(chunk),
                "max": max(chunk),
                "std": round(math.sqrt(variance), 3)
            })
        return results

    @staticmethod
    def sliding_window_aggregates(data: List[float], window_size: int, step_size: int) -> List[Dict[str, float]]:
        """Computes aggregates over overlapping sliding windows."""
        if window_size <= 0 or step_size <= 0:
            raise ValueError("Window size and step size must be positive")

        results = []
        for i in range(0, len(data) - window_size + 1, step_size):
            chunk = data[i:i + window_size]
            mean_val = sum(chunk) / len(chunk)
            results.append({
                "start_idx": i,
                "end_idx": i + window_size,
                "mean": round(mean_val, 3),
                "min": min(chunk),
                "max": max(chunk)
            })
        return results


class EdgeDataCompressor:
    """Constrained edge compression algorithms (Delta Encoding, RLE, Deadband Filter)."""

    @staticmethod
    def delta_encode(data: List[int]) -> List[int]:
        """Encodes sequence as initial base value followed by deltas."""
        if not data:
            return []
        encoded = [data[0]]
        for i in range(1, len(data)):
            encoded.append(data[i] - data[i - 1])
        return encoded

    @staticmethod
    def delta_decode(encoded: List[int]) -> List[int]:
        """Reconstructs original sequence from delta-encoded list."""
        if not encoded:
            return []
        decoded = [encoded[0]]
        for delta in encoded[1:]:
            decoded.append(decoded[-1] + delta)
        return decoded

    @staticmethod
    def run_length_encode(data: List[Any]) -> List[tuple]:
        """Encodes repeated runs as (value, count) tuples."""
        if not data:
            return []
        rle = []
        curr_val = data[0]
        count = 1
        for val in data[1:]:
            if val == curr_val:
                count += 1
            else:
                rle.append((curr_val, count))
                curr_val = val
                count = 1
        rle.append((curr_val, count))
        return rle

    @staticmethod
    def deadband_filter(data: List[float], threshold_epsilon: float) -> List[tuple]:
        """
        Piecewise constant / deadband compression.
        Only records index and value when change exceeds threshold_epsilon.
        """
        if not data:
            return []
        compressed = [(0, data[0])]
        last_val = data[0]

        for idx in range(1, len(data)):
            if abs(data[idx] - last_val) >= threshold_epsilon:
                compressed.append((idx, data[idx]))
                last_val = data[idx]

        return compressed
