"""
Unit tests for IoT Data Management, Stream Windowing, Compression, and Security.
"""

import unittest
from src.data_aggregation import StreamWindow, EdgeDataCompressor
from src.iot_security import AntiReplayWindow, ConstrainedDeviceSecurity


class TestDataAggregation(unittest.TestCase):
    def test_tumbling_window_aggregates(self):
        data = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        aggs = StreamWindow.tumbling_window_aggregates(data, window_size=3)
        self.assertEqual(len(aggs), 2)
        # Window 1: [10, 20, 30] -> mean = 20.0, min = 10, max = 30
        self.assertEqual(aggs[0]["mean"], 20.0)
        self.assertEqual(aggs[0]["min"], 10.0)
        self.assertEqual(aggs[0]["max"], 30.0)
        # Window 2: [40, 50, 60] -> mean = 50.0
        self.assertEqual(aggs[1]["mean"], 50.0)

    def test_sliding_window_aggregates(self):
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        aggs = StreamWindow.sliding_window_aggregates(data, window_size=3, step_size=1)
        # Windows: [1,2,3], [2,3,4], [3,4,5]
        self.assertEqual(len(aggs), 3)
        self.assertEqual(aggs[0]["mean"], 2.0)
        self.assertEqual(aggs[1]["mean"], 3.0)
        self.assertEqual(aggs[2]["mean"], 4.0)

    def test_delta_encoding_roundtrip(self):
        original = [1000, 1002, 1005, 1001, 1004]
        encoded = EdgeDataCompressor.delta_encode(original)
        self.assertEqual(encoded, [1000, 2, 3, -4, 3])
        decoded = EdgeDataCompressor.delta_decode(encoded)
        self.assertEqual(decoded, original)

    def test_run_length_encoding(self):
        states = ["IDLE", "IDLE", "IDLE", "ACTIVE", "ACTIVE", "SLEEP"]
        rle = EdgeDataCompressor.run_length_encode(states)
        self.assertEqual(rle, [("IDLE", 3), ("ACTIVE", 2), ("SLEEP", 1)])

    def test_deadband_filtering(self):
        # Transmit only when abs change >= 0.5
        readings = [20.0, 20.1, 20.2, 20.6, 20.7, 21.3]
        filtered = EdgeDataCompressor.deadband_filter(readings, threshold_epsilon=0.5)
        # Index 0: 20.0
        # Index 3: 20.6 (change 0.6 >= 0.5)
        # Index 5: 21.3 (change 0.7 >= 0.5 from 20.6)
        self.assertEqual(len(filtered), 3)
        self.assertEqual(filtered[0], (0, 20.0))
        self.assertEqual(filtered[1], (3, 20.6))
        self.assertEqual(filtered[2], (5, 21.3))


class TestIotSecurity(unittest.TestCase):
    def setUp(self):
        self.psk = b"secret-key-32-bytes-long-123456"
        self.device = ConstrainedDeviceSecurity(device_id="sensor-node-42", pre_shared_key=self.psk)
        self.replay = AntiReplayWindow(window_size=64)

    def test_telemetry_packet_creation_and_verification(self):
        packet = self.device.secure_telemetry_packet({"temperature": 22.4, "humidity": 55.0})
        self.assertIn("body", packet)
        self.assertIn("hmac", packet)
        self.assertEqual(packet["body"]["seq"], 1)

        # Successful verification
        valid, reason = ConstrainedDeviceSecurity.verify_packet(packet, self.psk, self.replay)
        self.assertTrue(valid)
        self.assertEqual(reason, "VERIFIED")

    def test_tamper_detection(self):
        packet = self.device.secure_telemetry_packet({"temperature": 22.4})
        # Attacker tampers with payload data
        packet["body"]["data"]["temperature"] = 99.9

        valid, reason = ConstrainedDeviceSecurity.verify_packet(packet, self.psk, self.replay)
        self.assertFalse(valid)
        self.assertIn("HMAC signature mismatch", reason)

    def test_anti_replay_protection(self):
        p1 = self.device.secure_telemetry_packet({"val": 1})
        p2 = self.device.secure_telemetry_packet({"val": 2})

        # Deliver p1
        v1, _ = ConstrainedDeviceSecurity.verify_packet(p1, self.psk, self.replay)
        self.assertTrue(v1)

        # Replay p1 again -> must be rejected!
        v1_replay, reason = ConstrainedDeviceSecurity.verify_packet(p1, self.psk, self.replay)
        self.assertFalse(v1_replay)
        self.assertIn("Replay attack detected", reason)

        # Deliver fresh p2 -> must succeed
        v2, _ = ConstrainedDeviceSecurity.verify_packet(p2, self.psk, self.replay)
        self.assertTrue(v2)


if __name__ == "__main__":
    unittest.main()
