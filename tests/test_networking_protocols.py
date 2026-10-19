"""
Unit tests for IoT Networking Protocols: CoAP, MQTT Broker, and LoRaWAN ToA.
"""

import unittest
from src.networking_protocols import (
    CoapType,
    CoapCode,
    CoapMessage,
    CoapServer,
    MqttQoS,
    MqttBroker,
    LoraModulation,
)


class TestCoapProtocol(unittest.TestCase):
    def setUp(self):
        self.server = CoapServer()
        self.server.register_resource("sensors/temperature", b"23.5 C")

    def test_coap_header_serialization(self):
        msg = CoapMessage(
            msg_type=CoapType.CON,
            code=CoapCode.GET,
            message_id=0x1234,
            token=b"\xAA\xBB"
        )
        hdr = msg.serialize_header()
        self.assertEqual(len(hdr), 4 + 2)  # 4 header bytes + 2 token bytes
        # Byte 0: version 1 (01), type 0 (00), tkl 2 (0010) -> 0b01000010 = 0x42
        self.assertEqual(hdr[0], 0x42)
        # Byte 1: code 1 (GET)
        self.assertEqual(hdr[1], 0x01)

    def test_coap_get_resource_and_observe(self):
        # 1. Successful GET
        req = CoapMessage(
            msg_type=CoapType.CON,
            code=CoapCode.GET,
            message_id=10,
            token=b"\x01",
            uri_path="sensors/temperature",
            observe=0
        )
        resp = self.server.handle_request(req, client_id="node-alpha")
        self.assertEqual(resp.code, CoapCode.RESP_CONTENT)
        self.assertEqual(resp.payload, b"23.5 C")
        self.assertIn("node-alpha", self.server.observers["sensors/temperature"])

        # 2. 4.04 Not Found
        req_missing = CoapMessage(
            msg_type=CoapType.CON,
            code=CoapCode.GET,
            message_id=11,
            uri_path="nonexistent"
        )
        resp_missing = self.server.handle_request(req_missing)
        self.assertEqual(resp_missing.code, CoapCode.RESP_NOT_FOUND)

    def test_coap_post_and_put(self):
        req_post = CoapMessage(
            msg_type=CoapType.CON,
            code=CoapCode.POST,
            message_id=12,
            uri_path="actuators/relay",
            payload=b"ON"
        )
        resp_post = self.server.handle_request(req_post)
        self.assertEqual(resp_post.code, CoapCode.RESP_CHANGED)
        self.assertEqual(self.server.resources["actuators/relay"], b"ON")


class TestMqttBroker(unittest.TestCase):
    def setUp(self):
        self.broker = MqttBroker()

    def test_topic_matching_wildcards(self):
        # Single-level '+' wildcard
        self.assertTrue(MqttBroker.topic_matches("home/+/temperature", "home/kitchen/temperature"))
        self.assertTrue(MqttBroker.topic_matches("home/+/temperature", "home/bedroom/temperature"))
        self.assertFalse(MqttBroker.topic_matches("home/+/temperature", "home/kitchen/sub/temperature"))

        # Multi-level '#' wildcard
        self.assertTrue(MqttBroker.topic_matches("factory/#", "factory/sensor1"))
        self.assertTrue(MqttBroker.topic_matches("factory/#", "factory/line1/station2/temp"))
        self.assertFalse(MqttBroker.topic_matches("factory/#", "office/printer"))

    def test_publish_subscribe_dispatch(self):
        self.broker.subscribe("client-A", "sensors/temperature/+")
        self.broker.subscribe("client-B", "sensors/#")
        self.broker.subscribe("client-C", "actuators/#")

        # Publish to sensors/temperature/room1
        recipients = self.broker.publish("sensors/temperature/room1", "24.2 C", retain=True)
        self.assertIn("client-A", recipients)
        self.assertIn("client-B", recipients)
        self.assertNotIn("client-C", recipients)

        # Check retained message
        self.assertIn("sensors/temperature/room1", self.broker.retained_messages)


class TestLoraModulation(unittest.TestCase):
    def test_time_on_air_sf_scaling(self):
        # 16-byte payload at SF7 vs SF12 (125 kHz BW)
        toa_sf7 = LoraModulation.calculate_time_on_air_ms(payload_bytes=16, spreading_factor=7)
        toa_sf12 = LoraModulation.calculate_time_on_air_ms(payload_bytes=16, spreading_factor=12)

        # SF12 symbol is 2^(12-7) = 32x longer than SF7, so ToA must be substantially greater
        self.assertGreater(toa_sf7, 40.0)
        self.assertLess(toa_sf7, 100.0)
        self.assertGreater(toa_sf12, 1000.0)

    def test_duty_cycle_compliance(self):
        # 50 ms ToA sent once every 10 seconds (10,000 ms) -> 50 / 10000 = 0.5% (<= 1.0% limit)
        eval_compliant = LoraModulation.check_duty_cycle_compliance(toa_ms=50.0, interval_seconds=10.0)
        self.assertTrue(eval_compliant["is_compliant"])
        self.assertEqual(eval_compliant["duty_cycle_pct"], 0.5)

        # 500 ms ToA sent once every 10 seconds -> 500 / 10000 = 5.0% (> 1.0% limit)
        eval_violation = LoraModulation.check_duty_cycle_compliance(toa_ms=500.0, interval_seconds=10.0)
        self.assertFalse(eval_violation["is_compliant"])


if __name__ == "__main__":
    unittest.main()
