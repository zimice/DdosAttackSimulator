#!/usr/bin/env python3
"""
bot.py

Bot client for the *Distributed DDoS Attack Simulator bachelor-thesis project.

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
import random
import socket
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from logger import DetailedLogger
from plan   import Plan

# --------------------------------------------------------------------------- #
# Dataclass config
# --------------------------------------------------------------------------- #

@dataclass
class BotConfig:
    lead_ip: str = "127.0.0.1"
    lead_port: int = 9999
    debug: bool = False
    log_file: Path = Path("bot_log.log")

# --------------------------------------------------------------------------- #
# Bot implementation                                                          #
# --------------------------------------------------------------------------- #

class Bot:
    """Connects to a Lead server, downloads an attack plan, and executes it."""

    # --------------------------------------------------------------------- #
    # Constructor & top‑level control                                       #
    # --------------------------------------------------------------------- #

    def __init__(self, cfg: BotConfig) -> None:
        self.cfg   = cfg
        self.log   = self._make_logger()
        self.hash: str | None = None  # updated after first fetch

    # ------------------------------- public -------------------------------- #
    def run(self) -> None:
        """Entry-point - fetch plan, start heartbeat, execute indefinitely."""
        try:
            plan_json          = self._fetch_plan()
            self.plan_hash     = Plan.sha256_json(plan_json)

            # launch heartbeat before first execution so hash stays current
            threading.Thread(target=self._heartbeat_loop,
                             name="Heartbeat",
                             daemon=True).start()

            self._execute_plan(Plan.from_json(plan_json))

            # idle forever – heartbeat thread keeps the process alive
            while True:
                time.sleep(3600)
        except Exception as exc:
            self.log.error("Fatal error: %s", exc)
            sys.exit(1)

    # ------------------------- internals ----------------------------------- #
    def _make_logger(self) -> DetailedLogger:
        level = logging.DEBUG if self.cfg.debug else logging.INFO
        return DetailedLogger(str(self.cfg.log_file), log_level=level)

    # --------------------------------------------------------------------- #
    # Lead communication helpers
    def _fetch_plan(self) -> str:
        """TCP request: opcode 0 full plan JSON."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.cfg.lead_ip, self.cfg.lead_port))
            s.sendall(b"0")
            chunks: List[bytes] = []
            while (blk := s.recv(4096)):
                chunks.append(blk)
        return b"".join(chunks).decode()

    def _fetch_plan_hash(self) -> str:
        """TCP request: opcode 1  64-byte hex SHA-256 digest."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.cfg.lead_ip, self.cfg.lead_port))
            s.sendall(b"1")
            return s.recv(64).decode()

    # --------------------------------------------------------------------- #
    def _heartbeat_loop(self) -> None:
        self.log.debug("Heartbeat thread started")
        while True:
            time.sleep(random.randint(1, 2))# 3–5 min jitter
            try:
                new_hash = self._fetch_plan_hash()
                if new_hash != self.plan_hash:
                    self.log.info("Plan hash changed - downloading update")
                    plan_json      = self._fetch_plan()
                    self.plan_hash = Plan.sha256_json(plan_json)
                    self._execute_plan(Plan.from_json(plan_json))
                else:
                    self.log.debug("Plan unchanged")
            except Exception as exc:
                self.log.error("Heartbeat failed: %s", exc)

    # --------------------------------------------------------------------- #
    def _execute_plan(self, plan: Plan) -> None:
            """Run each attack in order"""
            for atk in plan.attack_objs:
                workers: List[threading.Thread] = []

                def _worker() -> None:
                    try:
                        atk.wait_until_start()
                        if self.cfg.debug:
                            print(f"Executing on {atk.target_ip} | "f"{type(atk).__name__} | {atk.parameters}",flush=True)
                        atk.execute()
                        self.log.info("Worker finished %s on %s",type(atk).__name__, atk.target_ip)
                    except Exception as exc:
                        self.log.error("Worker error for %s on %s: %s",type(atk).__name__, atk.target_ip, exc)

                self.log.info("Starting %s on %s with %d thread(s)",type(atk).__name__, atk.target_ip, atk.threads)

                for _ in range(atk.threads):
                    t = threading.Thread(target=_worker, daemon=True)
                    t.start()
                    workers.append(t)

                for t in workers:
                    t.join()

                self.log.info("Attack %s on %s completed",type(atk).__name__, atk.target_ip)
            if self.cfg.debug:
                print("All attacks completed",flush=True)

    # --------------------------------------------------------------------- #
    # CLI                                                                   #
    # --------------------------------------------------------------------- #
    @staticmethod
    def parse_cli(argv: List[str]) -> BotConfig:
        p = argparse.ArgumentParser(description="Bot client for the Distributed DDoS Attack Simulator")
        p.add_argument("lead_ip",   nargs="?", default="127.0.0.1",help="Lead server host (default 127.0.0.1)")
        p.add_argument("lead_port", nargs="?", type=int, default=9999,help="Lead TCP port (default 9999)")
        p.add_argument("-d", "--debug", action="store_true",help="Enable DEBUG logging")
        ns = p.parse_args(argv)

        return BotConfig(ns.lead_ip, ns.lead_port, ns.debug)

# --------------------------------------------------------------------------- #
# Script entry-point                                                          #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    try:
        config = Bot.parse_cli(sys.argv[1:])
        Bot(config).run()
    except KeyboardInterrupt:
        DetailedLogger().critical("Bot interrupted by user (Ctrl-C) – exiting")
        sys.exit(1)