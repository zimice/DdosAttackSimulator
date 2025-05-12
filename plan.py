"""
plan.py

Define the Plan class (serialize / deserialize) and provide a stable
SHA-256 hash for integrity checks.
"""

from __future__ import annotations
import json
import hashlib
from datetime import datetime
from attacks.SynFloodAttack import SynFloodAttack
from attacks.ICMPFlood import ICMPFlood
from attacks.HTTPFlood import HTTPFlood
from attacks.UDPFlood import UDPFlood
from attacks.SlowLorisAttack import SlowLorisAttack


class Plan:
    """A collection of attack objects with JSON object helpers."""

    # ------------------------------------------------------------------ #
    def __init__(self, attack_objs: list) -> None:
        self.attack_objs = attack_objs

    # ------------------------------------------------------------------ #
    # Serialisation helpers
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        """Return a plain-Python representation (used by to_json / hash)."""
        attacks = []
        for atk in self.attack_objs:
            attacks.append(
                {
                    "attack_type": type(atk).__name__,
                    "target_ip":   atk.target_ip,
                    "parameters":  atk.parameters,
                    "start_time": (
                        atk.start_time.isoformat() if atk.start_time else None
                    ),
                }
            )
        return {"attacks": attacks}

    # note: separators remove whitespace; sort_keys guarantees canonical order
    def to_json(self, *, sort_keys: bool = True) -> str:
        return json.dumps(
            self.to_dict(),
            separators=(",", ":"),
            sort_keys=sort_keys,
        )

    # ------------------------------------------------------------------ #
    # Deserialisation
    # ------------------------------------------------------------------ #
    @staticmethod
    def from_json(json_str: str) -> "Plan":
        data = json.loads(json_str)
        objs = []
        for a in data.get("attacks", []):
            cls = {
                "SynFloodAttack":  SynFloodAttack,
                "ICMPFlood":       ICMPFlood,
                "HTTPFlood":       HTTPFlood,
                "UDPFlood":        UDPFlood,
                "SlowLorisAttack": SlowLorisAttack,
            }.get(a["attack_type"])
            if cls is None:
                raise ValueError(f"Unknown attack type {a['attack_type']}")
            start = (
                datetime.fromisoformat(a["start_time"])
                if a.get("start_time")
                else None
            )
            objs.append(cls(a["target_ip"], a["parameters"], start))
        return Plan(objs)

    # ------------------------------------------------------------------ #
    # Stable SHA-256 hash helpers
    # ------------------------------------------------------------------ #
    def sha256(self) -> str:
        """Hash of *this* plan in canonical JSON form."""
        return hashlib.sha256(self.to_json().encode()).hexdigest()

    @staticmethod
    def sha256_json(json_str: str) -> str:
        """Hash a JSON string that was produced by Plan.to_json()."""
        return hashlib.sha256(json_str.encode()).hexdigest()
