# logger.py
import logging
from logging.handlers import RotatingFileHandler
from types import MethodType

class DetailedLogger:
    """
    Thin wrapper around Python's logging module with an optional
    `enable_logging` flag so callers can disable all I/O cleanly.
    """

    def __init__(
        self,
        log_file: str = "detailed_log.log",
        log_level: int = logging.DEBUG,
        enable_logging: bool = True,
    ):
        self._enabled = enable_logging

        # If logging is disabled, create a dummy logger with no‑op methods
        if not enable_logging:
            for level in ("debug", "info", "warning", "error", "critical"):
                setattr(self, level, MethodType(lambda *_, **__: None, self))
            return  # nothing else to configure

        # Normal logging setup ↓
        self.logger = logging.getLogger(log_file)
        self.logger.setLevel(log_level)

        handler = RotatingFileHandler(
            log_file, maxBytes=1_000_000, backupCount=3
        )
        handler.setLevel(log_level)

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # delegate convenience wrappers
        self.debug     = self.logger.debug
        self.info      = self.logger.info
        self.warning   = self.logger.warning
        self.error     = self.logger.error
        self.critical  = self.logger.critical
