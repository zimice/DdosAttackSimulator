"""
attack.py

This module defines the abstract base class Attack, which is inherited by all specific attack types.
Each attack is defined for a single target IP, a parameters dictionary, and an optional start time.
If no start time is provided, the attack is scheduled to start immediately (in UTC).

DISCLAIMER:
This tool is designed strictly for educational purposes and controlled network security testing.
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class Attack(ABC):
    """
    Abstract base class for all attack types.

    Attributes:
        target_ip (str): The target IP address.
        parameters (dict): A dictionary containing attack-specific parameters.
        start_time (datetime): The scheduled start time for the attack (UTC).If None, defaults to the current time in UTC.
    """
    # ------------------------------------------------------------------ #

    def __init__(self, target_ip: str, parameters: Dict[str, Any] | None = None, start_time: Optional[datetime] = None,) -> None:
        self.target_ip = target_ip
        self.parameters = parameters or {}
        self.threads: int = int(self.parameters.get("threads", 1))
        self.start_time = start_time or datetime.now(timezone.utc)

    # ------------------------------------------------------------------ #
    @abstractmethod
    def execute(self):
        """Abstract method to execute the attack. Must be implemented by subclasses."""
        pass

    # ------------------------------------------------------------------ #
    def wait_until_start(self) -> None:
        """Block until self.start_time (UTC) is reached."""
        now = datetime.now(timezone.utc)
        if now < self.start_time:
            time.sleep((self.start_time - now).total_seconds())
