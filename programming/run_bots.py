#!/usr/bin/env python3
"""
run_bots.py
===========

Utility to spawn **multiple `bot.py` clients** in parallel.

DISCLAIMER:  
This tool is designed strictly for educational purposes and controlled
network-security testing.

---------------------------------------------------------------------------
Dependencies
---------------------------------------------------------------------------
    - Python ≥3.8  (uses `multiprocessing` and `subprocess`)
    - bot.py       (must be in the same directory)

---------------------------------------------------------------------------
Usage
---------------------------------------------------------------------------
    $ python run_bots.py 10                    # 10 bots → localhost:9999
    $ python run_bots.py 5 10.0.0.5 8888 -d    # 5 bots, custom Lead, DEBUG

Positional arguments
--------------------
    count         number of bot instances to launch

Optional arguments
------------------
    lead_ip       Lead host   (default 127.0.0.1)
    lead_port     Lead port   (default 9999)
    -d / --debug  pass DEBUG flag to each bot
"""

from __future__ import annotations

import argparse
import logging
import multiprocessing as mp
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from subprocess import Popen

# --------------------------------------------------------------------------- #
# Constants / paths
# --------------------------------------------------------------------------- #
SCRIPT_DIR = Path(__file__).resolve().parent
BOT_PATH   = SCRIPT_DIR / "bot.py"          # assumes bot.py sits next to this file


# --------------------------------------------------------------------------- #
# Configuration container
# --------------------------------------------------------------------------- #
@dataclass
class RunnerConfig:
    count: int        = 1
    lead_ip: str      = "127.0.0.1"
    lead_port: int    = 9999
    debug: bool       = False
    log_level: int    = logging.INFO


# --------------------------------------------------------------------------- #
# Bot-launcher utility
# --------------------------------------------------------------------------- #
class BotRunner:
    """Spawn `count` independent bot subprocesses."""

    # ---------------- constructor / public API --------------------------- #
    def __init__(self, cfg: RunnerConfig) -> None:
        self.cfg = cfg
        self.logger = self._configure_logger()

    def run(self) -> None:
        """Create the requested number of bots and wait for them to exit."""
        self.logger.info(
            "Launching %d bot(s) -> %s:%d  (debug=%s)",
            self.cfg.count,
            self.cfg.lead_ip,
            self.cfg.lead_port,
            self.cfg.debug,
        )

        procs: list[mp.Process] = []
        for _ in range(self.cfg.count):
            p = mp.Process(
                target=self._launch_bot,
                args=(self.cfg.lead_ip, self.cfg.lead_port, self.cfg.debug),
                daemon=False,
            )
            p.start()
            procs.append(p)

        # Wait for all children
        for p in procs:
            p.join()
            self.logger.info("Bot PID %d exited with code %s", p.pid, p.exitcode)

    # ---------------- internals ----------------------------------------- #
    @staticmethod
    def _launch_bot(lead_ip: str, lead_port: int, debug: bool) -> None:
        """Execute bot.py as a subprocess (blocking)."""
        cmd = [sys.executable, str(BOT_PATH), lead_ip, str(lead_port)]
        if debug:
            cmd.append("-d")

        # Give each bot its own log suffix to avoid file clobbering
        env = os.environ.copy()
        env["BOT_LOG_SUFFIX"] = f".{os.getpid()}"
        Popen(cmd, env=env).wait()

    # ------------------------------------------------------------------ #
    def _configure_logger(self) -> logging.Logger:
        """Simple console logger; no file rotation for this helper."""
        logger = logging.getLogger("run_bots")
        logger.setLevel(self.cfg.log_level)

        if not logger.handlers:
            h = logging.StreamHandler()
            h.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            logger.addHandler(h)
        return logger

    # ------------------------------------------------------------------ #
    # CLI helper
    # ------------------------------------------------------------------ #
    @staticmethod
    def parse_cli(argv: list[str]) -> RunnerConfig:
        parser = argparse.ArgumentParser(
            description="Spawn multiple bot.py instances in parallel"
        )
        parser.add_argument("count", type=int, help="Number of bot instances to start")
        parser.add_argument(
            "lead_ip", nargs="?", default="127.0.0.1",
            help="Lead IP / host (default 127.0.0.1)",
        )
        parser.add_argument(
            "lead_port", nargs="?", type=int, default=9999,
            help="Lead TCP port (default 9999)",
        )
        parser.add_argument(
            "-d", "--debug", action="store_true",
            help="Run each bot with DEBUG logging",
        )
        args = parser.parse_args(argv)

        return RunnerConfig(
            count=args.count,
            lead_ip=args.lead_ip,
            lead_port=args.lead_port,
            debug=args.debug,
            log_level=logging.DEBUG if args.debug else logging.INFO,
        )


# --------------------------------------------------------------------------- #
# Script entry-point
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    cfg = BotRunner.parse_cli(sys.argv[1:])
    BotRunner(cfg).run()
