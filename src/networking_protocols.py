"""
IoT Networking Protocols: CoAP (RFC 7252), MQTT Broker, and LoRaWAN Physical Modeler.
"""

from enum import Enum
from typing import Dict, List, Set, Any, Optional, Tuple
import math
import struct


# =====================================================================
# 1. CoAP (Constrained Application Protocol - RFC 7252)
# =====================================================================

class CoapType(Enum):
    CON = 0  # Confirmable
    NON = 1  # Non-confirmable
    ACK = 2  # Acknowledgement
    RST = 3  # Reset


class CoapCode(Enum):
    EMPTY = 0
    GET = 1
    POST = 2
    PUT = 3
    DELETE = 4
    RESP_CREATED = 65     # 2.01
    RESP_DELETED = 66     # 2.02
    RESP_VALID = 67       # 2.03
    RESP_CHANGED = 68     # 2.04
    RESP_CONTENT = 69     # 2.05
    RESP_BAD_REQUEST = 128  # 4.00
    RESP_NOT_FOUND = 132    # 4.04
    RESP_INTERNAL_ERR = 160 # 5.00


class CoapMessage:
    """Represents a RFC 7252 CoAP PDU."""

    def __init__(
        self,
        msg_type: CoapType = CoapType.CON,
        code: CoapCode = CoapCode.GET,
        message_id: int = 1,
        token: bytes = b"",
        uri_path: str = "",
        payload: bytes = b"",
        observe: Optional[int] = None
    ):
        self.version = 1
        self.msg_type = msg_type
        self.code = code
        self.message_id = message_id
        self.token = token
        self.uri_path = uri_path
        self.payload = payload
        self.observe = observe

    def serialize_header(self) -> bytes:
        """Serializes 4-byte mandatory CoAP header."""
        t_val = self.msg_type.value
        tkl = len(self.token) & 0x0F
        byte0 = (self.version << 6) | (t_val << 4) | tkl
        byte1 = self.code.value
        return struct.pack("!BBH", byte0, byte1, self.message_id) + self.token


class CoapServer:
    """Lightweight CoAP RESTful server managing resources and the Observe pattern."""

    def __init__(self):
        self.resources: Dict[str, bytes] = {}
        self.observers: Dict[str, Set[str]] = {}  # uri_path -> client_ids

    def register_resource(self, uri_path: str, initial_data: bytes):
        self.resources[uri_path] = initial_data
        self.observers[uri_path] = set()

    def handle_request(self, req: CoapMessage, client_id: str = "client-01") -> CoapMessage:
        if req.code == CoapCode.GET:
            if req.uri_path in self.resources:
                if req.observe == 0:  # Register observation (RFC 7641)
                    self.observers[req.uri_path].add(client_id)

                resp_type = CoapType.ACK if req.msg_type == CoapType.CON else CoapType.NON
                return CoapMessage(
                    msg_type=resp_type,
                    code=CoapCode.RESP_CONTENT,
                    message_id=req.message_id,
                    token=req.token,
                    payload=self.resources[req.uri_path]
                )
            return CoapMessage(
                msg_type=CoapType.ACK if req.msg_type == CoapType.CON else CoapType.NON,
                code=CoapCode.RESP_NOT_FOUND,
                message_id=req.message_id,
                token=req.token
            )
        elif req.code in (CoapCode.POST, CoapCode.PUT):
            self.resources[req.uri_path] = req.payload
            return CoapMessage(
                msg_type=CoapType.ACK if req.msg_type == CoapType.CON else CoapType.NON,
                code=CoapCode.RESP_CHANGED,
                message_id=req.message_id,
                token=req.token
            )
        return CoapMessage(
            msg_type=CoapType.RST,
            code=CoapCode.RESP_BAD_REQUEST,
            message_id=req.message_id
        )


# =====================================================================
# 2. MQTT (Message Queuing Telemetry Transport)
# =====================================================================

class MqttQoS(Enum):
    AT_MOST_ONCE = 0   # QoS 0
    AT_LEAST_ONCE = 1  # QoS 1
    EXACTLY_ONCE = 2   # QoS 2


class MqttBroker:
    """
    Simulates an MQTT broker with topic tree routing, single/multi-level wildcards,
    retained messages, and QoS tracking.
    """

    def __init__(self):
        # client_id -> set of subscribed topic filters
        self.subscriptions: Dict[str, Set[str]] = {}
        self.retained_messages: Dict[str, Dict[str, Any]] = {}
        self.delivered_count = 0

    @staticmethod
    def topic_matches(filter_pattern: str, topic: str) -> bool:
        """
        Matches MQTT topic against filter containing '+' (single-level) or '#' (multi-level).
        """
        f_parts = filter_pattern.split("/")
        t_parts = topic.split("/")

        i = 0
        while i < len(f_parts):
            if f_parts[i] == "#":
                return True
            if i >= len(t_parts):
                return False
            if f_parts[i] != "+" and f_parts[i] != t_parts[i]:
                return False
            i += 1

        return i == len(t_parts)

    def subscribe(self, client_id: str, topic_filter: str):
        if client_id not in self.subscriptions:
            self.subscriptions[client_id] = set()
        self.subscriptions[client_id].add(topic_filter)

    def unsubscribe(self, client_id: str, topic_filter: str):
        if client_id in self.subscriptions:
            self.subscriptions[client_id].discard(topic_filter)

    def publish(
        self,
        topic: str,
        payload: str,
        qos: MqttQoS = MqttQoS.AT_MOST_ONCE,
        retain: bool = False
    ) -> List[str]:
        """
        Publishes message to matching subscribers.
        Returns list of client IDs that received the publication.
        """
        if retain:
            self.retained_messages[topic] = {"payload": payload, "qos": qos}

        recipients = []
        for client_id, filters in self.subscriptions.items():
            for f in filters:
                if self.topic_matches(f, topic):
                    recipients.append(client_id)
                    self.delivered_count += 1
                    break

        return recipients


# =====================================================================
# 3. LoRaWAN (Long Range Wide Area Network)
# =====================================================================

class LoraModulation:
    """
    Computes LoRa Chirp Spread Spectrum (CSS) Time-on-Air (ToA)
    and validates regulatory duty cycle limits (e.g. 1% EU868).
    """

    @staticmethod
    def calculate_time_on_air_ms(
        payload_bytes: int,
        spreading_factor: int = 7,
        bandwidth_khz: float = 125.0,
        coding_rate: int = 1,  # 1 = 4/5, 2 = 4/6, etc.
        preamble_symbols: int = 8,
        explicit_header: bool = True,
        enable_crc: bool = True
    ) -> float:
        """
        Calculates Time-on-Air (ToA) in milliseconds according to Semtech SX1276 datasheet.
        """
        if spreading_factor < 6 or spreading_factor > 12:
            raise ValueError("Spreading factor must be between 6 and 12")

        # Symbol duration
        t_sym_ms = (2 ** spreading_factor) / (bandwidth_khz * 1000.0) * 1000.0

        # Preamble duration
        t_preamble_ms = (preamble_symbols + 4.25) * t_sym_ms

        # Low data rate optimization flag
        de = 1 if (spreading_factor >= 11 and bandwidth_khz == 125.0) else 0
        ih = 0 if explicit_header else 1
        crc = 1 if enable_crc else 0

        # Number of payload symbols
        term1 = (8 * payload_bytes) - (4 * spreading_factor) + 28 + (16 * crc) - (20 * ih)
        term2 = 4 * (spreading_factor - (2 * de))

        if term2 <= 0:
            n_payload = 8
        else:
            payload_sym_nb = 8 + max(0, math.ceil(term1 / term2) * (coding_rate + 4))
            n_payload = payload_sym_nb

        t_payload_ms = n_payload * t_sym_ms
        return round(t_preamble_ms + t_payload_ms, 2)

    @staticmethod
    def check_duty_cycle_compliance(
        toa_ms: float,
        interval_seconds: float,
        allowed_duty_cycle_pct: float = 1.0
    ) -> Dict[str, Any]:
        """Validates transmission duty cycle against regulatory caps."""
        duty_cycle_pct = (toa_ms / (interval_seconds * 1000.0)) * 100.0
        compliant = duty_cycle_pct <= allowed_duty_cycle_pct
        return {
            "duty_cycle_pct": round(duty_cycle_pct, 4),
            "allowed_pct": allowed_duty_cycle_pct,
            "is_compliant": compliant
        }
