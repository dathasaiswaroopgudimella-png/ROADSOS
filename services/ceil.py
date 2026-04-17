"""
RoadSoS -- Fail-Safe Emergency Guidance System
CEIL Module (Phase 5)

Community Emergency Impact Level signal.
Returns ONLY: "none" | "low" | "medium" | "high"

STATIC JSON only -- NO networking.
"""

import json
import os
import time
from typing import Any

from core.logger import get_logger

logger = get_logger(__name__)

_CEIL_DATA_PATH = os.path.join(os.path.dirname(__file__), "ceil_data.json")

# Static fallback if file is missing
_DEFAULT_CEIL: str = "none"


def get_ceil_signal(logger_: Any = None) -> str:
    """Return the current CEIL signal level.

    Reads from a static local JSON file.
    NO network calls are made.

    Returns:
        One of 'none', 'low', 'medium', 'high'.
    """
    log = logger_ or logger
    start = time.time()
    log.info("ENTER get_ceil_signal()")

    try:
        if os.path.exists(_CEIL_DATA_PATH):
            with open(_CEIL_DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            signal = data.get("level", _DEFAULT_CEIL)
        else:
            log.warning("CEIL data file not found, using default '%s'", _DEFAULT_CEIL)
            signal = _DEFAULT_CEIL

        # Validate
        valid = {"none", "low", "medium", "high"}
        if signal not in valid:
            log.warning("Invalid CEIL signal '%s', defaulting to '%s'", signal, _DEFAULT_CEIL)
            signal = _DEFAULT_CEIL

        log.info("EXIT get_ceil_signal -> '%s'", signal)
        return signal

    except Exception as exc:
        log.error("CRITICAL FAILURE in get_ceil_signal: %s", exc)
        return _DEFAULT_CEIL
    finally:
        log.info("time_ms=%.2f", (time.time() - start) * 1000)


# --------------------------------------------------
# SELF-TEST
# --------------------------------------------------
def run_test() -> None:
    valid = {"none", "low", "medium", "high"}
    sig = get_ceil_signal()
    assert sig in valid, f"Invalid CEIL signal: {sig}"
    print("[PASS] ceil.py -- all assertions passed")


if __name__ == "__main__":
    run_test()
