"""
IoT Security & Constrained Cryptographic Primitives.
Implements Pre-Shared Key (PSK) authentication, HMAC-SHA256 message integrity,
and Anti-Replay Protection via monotonic sequence verification.
"""

import hashlib
import hmac
import json
import time
from typing import Dict, Any, Optional, Tuple


class AntiReplayWindow:
    """
    Sliding window anti-replay protection (similar to IPsec RFC 4303 / DTLS).
    Protects constrained IoT devices from replayed wireless frames.
    """

    def __init__(self, window_size: int = 64):
        self.window_size = window_size
        self.highest_seq = 0
        self.seen_bitmask = 0  # Bitmask representing received packets within window

    def verify_and_update(self, seq_num: int) -> bool:
        """
        Returns True if packet is fresh and valid.
        Returns False if packet is a duplicate or too old.
        """
        if seq_num <= 0:
            return False

        if seq_num > self.highest_seq:
            # New highest sequence number received
            diff = seq_num - self.highest_seq
            if diff < self.window_size:
                self.seen_bitmask = (self.seen_bitmask << diff) | 1
            else:
                self.seen_bitmask = 1
            self.highest_seq = seq_num
            return True

        diff = self.highest_seq - seq_num
        if diff >= self.window_size:
            # Packet falls outside window on the low side (too old)
            return False

        # Check if already seen
        mask = 1 << diff
        if self.seen_bitmask & mask:
            # Duplicate replayed packet
            return False

        # Mark as seen
        self.seen_bitmask |= mask
        return True


class ConstrainedDeviceSecurity:
    """
    Implements lightweight message authentication code (MAC) and payload integrity
    for resource-constrained IoT nodes using HMAC-SHA256.
    """

    def __init__(self, device_id: str, pre_shared_key: bytes):
        self.device_id = device_id
        self.psk = pre_shared_key
        self.outgoing_seq = 0

    def secure_telemetry_packet(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Signs outgoing telemetry with sequence number and HMAC."""
        self.outgoing_seq += 1
        seq = self.outgoing_seq
        timestamp = int(time.time())

        body = {
            "device_id": self.device_id,
            "seq": seq,
            "ts": timestamp,
            "data": payload
        }
        serialized = json.dumps(body, sort_keys=True).encode("utf-8")
        mac = hmac.new(self.psk, serialized, hashlib.sha256).hexdigest()

        return {
            "body": body,
            "hmac": mac
        }

    @staticmethod
    def verify_packet(
        packet: Dict[str, Any],
        pre_shared_key: bytes,
        replay_tracker: Optional[AntiReplayWindow] = None
    ) -> Tuple[bool, str]:
        """
        Verifies packet integrity and freshness.
        Returns (is_valid, reason).
        """
        body = packet.get("body")
        received_hmac = packet.get("hmac")

        if not body or not received_hmac:
            return False, "Malformed packet structure"

        # Check HMAC
        serialized = json.dumps(body, sort_keys=True).encode("utf-8")
        expected_hmac = hmac.new(pre_shared_key, serialized, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_hmac, received_hmac):
            return False, "HMAC signature mismatch"

        # Check anti-replay if tracker provided
        if replay_tracker is not None:
            seq = body.get("seq", 0)
            if not replay_tracker.verify_and_update(seq):
                return False, f"Replay attack detected or packet expired (seq={seq})"

        return True, "VERIFIED"
