#!/usr/bin/env python3

"""
leader.py

Leader server for the *Distributed DDoS Attack Simulator* bachelor-thesis project.

DISCLAIMER:  
This tool is designed strictly for educational purposes and controlled network security testing.

-----------------------------------------------------------------------------
Scapy Installation Notes
-----------------------------------------------------------------------------
    - Linux: Install scapy via pip or your package manager.
    - Windows: Ensure Npcap (https://npcap.com/#download) is installed before using scapy.
"""

import argparse
import logging
import socket
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from attacks.ICMPFlood import ICMPFlood
from attacks.HTTPFlood import HTTPFlood
from attacks.SynFloodAttack import SynFloodAttack
from logger import DetailedLogger
from plan import Plan


# --------------------------------------------------------------------------- #
# Dataclass configuration                                                     #
# --------------------------------------------------------------------------- #
@dataclass
class LeaderConfig:
    host: str = "127.0.0.1"
    port: int = 9999
    plan_file: Path = Path("attack_plan.json")

    debug: bool = False
    print_info: bool = True
    stats: bool = True
    no_trace: bool = False


# --------------------------------------------------------------------------- #
# Leader implementation
# --------------------------------------------------------------------------- #

class Leader:
    """Serve attack-plan JSON / hash to connecting Bot clients."""

    # --------------------------------------------------------------------- #
    # Constructor & top‑level control                                       #
    # --------------------------------------------------------------------- #
    def __init__(self, cfg: LeaderConfig) -> None:
        self.cfg = cfg
        self.log = self._make_logger()

        self.plan: Plan = self._load_plan(cfg.plan_file)
        self.running = False
        self.conn_count = 0

 # --------------------------------------------------------------------- #
    def start(self) -> None:
        """Block - accept connections until exit command or Ctrl-C."""
        self.running = True
        self.log.info("Leader listening on %s:%s",
                      self.cfg.host, self.cfg.port)
        if self.cfg.print_info:
            print(f"Leader server running at {self.cfg.host}:{self.cfg.port}")

        # console thread listening for shutdown
        threading.Thread(target=self._exit_listener,
                         name="ExitListener", daemon=True).start()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.bind((self.cfg.host, self.cfg.port))
            srv.listen()
            srv.settimeout(1.0)

            try:
                while self.running:
                    try:
                        conn, addr = srv.accept()
                        self._handle_client(conn, addr)
                    except socket.timeout:
                        continue
            except KeyboardInterrupt:
                self.log.warning("Ctrl-C pressed - shutting down")
            finally:
                self.running = False

        if self.cfg.stats:
            self._print_stats()

    # ----------------------------- internals ----------------------------- #
    def _make_logger(self) -> DetailedLogger:
        if self.cfg.no_trace:
            return DetailedLogger(enable_logging=False)
        level = logging.DEBUG if self.cfg.debug else logging.INFO
        return DetailedLogger("leader_log.log", log_level=level)

    # ------------------------------------------------------------------ #
    def _load_plan(self, plan_path: Path) -> Plan:
        """Return Plan from file or demo fallback."""
        if plan_path.exists():
            try:
                self.log.info("Loading plan file %s", plan_path)
                return Plan.from_json(plan_path.read_text(encoding="utf-8"))
            except Exception as exc:
                self.log.error("Invalid plan file - fallback used: %s", exc)

        self.log.warning("Plan file not found - using fallback demo plan")
        return self._fallback_plan()

    # ------------------------------------------------------------------ #
    @staticmethod
    def _fallback_plan() -> Plan:
        """Return a simple hard-coded plan (single-IP model)."""
        attack1 = SynFloodAttack(
            "127.0.0.1", {"duration": 5, "target_port": 443})
        attack2 = ICMPFlood("127.0.0.1", {"duration": 5})
        attack3 = HTTPFlood("127.0.0.1", {"duration": 5, "target_port": 80})
        return Plan([attack1, attack2, attack3])

    # ------------------------------------------------------------------ #
    def _handle_client(self, conn: socket.socket, addr: Tuple[str, int]) -> None:
        """Serve plan / hash depending on first byte from the Bot."""
        self.conn_count += 1
        if self.cfg.print_info:
            print(f"Connection from {addr}")

        with conn:
            opcode = conn.recv(1)  # b"0" or b"1"
            if opcode == b"1":
                conn.sendall(self.plan.sha256().encode())
                what = "heartbeat (hash only)"
            else:
                conn.sendall(self.plan.to_json().encode())
                what = "full plan"

            self.log.debug("Served %s to %s", what, addr)

    # ------------------------------------------------------------------ #
    def _exit_listener(self) -> None:
        """Listen for *exit* on stdin; stop server gracefully."""
        if self.cfg.no_trace:           # no I/O in no-trace mode
            return

        try:
            while self.running:
                if input("Type 'exit' to stop server: ").strip().lower() == "exit":
                    self.log.info("Exit command received")
                    self.running = False
        except (EOFError, KeyboardInterrupt):
            self.log.critical("Input thread interrupted")
            self.running = False

    # ------------------------------------------------------------------ #
    def _print_stats(self) -> None:
        msg = f"Total bot connections handled: {self.conn_count}"
        if self.cfg.print_info:
            print(msg)
        self.log.info(msg)

# --------------------------------------------------------------------------- #
# CLI helper                                                                  #
# --------------------------------------------------------------------------- #


def parse_cli() -> LeaderConfig:
    p = argparse.ArgumentParser(
        description="Leader server for the Distributed DDoS Attack Simulator")
    p.add_argument("-H", "--host", default="127.0.0.1",
                   help="Bind address (default 127.0.0.1)")
    p.add_argument("-P", "--port", type=int, default=9999,
                   help="TCP port (default 9999)")
    p.add_argument("--plan", default="attack_plan.json",
                   help="Path to attack-plan JSON")
    p.add_argument("-d", "--debug", action="store_true",
                   help="Enable DEBUG logging")
    p.add_argument("-p", "--quiet", action="store_true",
                   help="Suppress console output")
    p.add_argument("-n", "--no-stats", action="store_true",
                   help="Disable connection statistics")
    p.add_argument("--no-trace", action="store_true",
                   help="Disable all logging / printing")

    ns = p.parse_args()
    return LeaderConfig(
        host=ns.host,
        port=ns.port,
        plan_file=Path(ns.plan),
        debug=ns.debug,
        print_info=not ns.quiet,
        stats=not ns.no_stats,
        no_trace=ns.no_trace,
    )


# --------------------------------------------------------------------------- #
# Script entry-point                                                          #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    cfg = parse_cli()
    Leader(cfg).start()
