"""
RoadSoS -- Fail-Safe Emergency Guidance System
Logger Module (Phase 1B)

Central logging configuration.
EVERY module MUST call get_logger(__name__).
"""

import logging
import sys
from typing import Optional


_CONFIGURED: bool = False


def _configure_root() -> None:
    """One-time root logger configuration."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Console handler -- INFO and above
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)-7s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console.setFormatter(fmt)
    root.addHandler(console)

    # File handler -- DEBUG and above
    try:
        fh = logging.FileHandler("roadsos.log", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except OSError:
        root.warning("Could not create log file -- continuing with console only")

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Configures root on first call.

    Args:
        name: Module name -- use __name__.

    Returns:
        logging.Logger instance.
    """
    _configure_root()
    return logging.getLogger(name)


# --------------------------------------------------
# SELF-TEST
# --------------------------------------------------
def run_test() -> None:
    logger = get_logger("test_logger")
    logger.info("Logger self-test: INFO message")
    logger.debug("Logger self-test: DEBUG message")
    logger.warning("Logger self-test: WARNING message")
    assert logger.name == "test_logger", "Logger name mismatch"
    print("[PASS] logger.py -- all assertions passed")


if __name__ == "__main__":
    run_test()
