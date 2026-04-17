"""
RoadSoS -- Fail-Safe Emergency Guidance System
Edge Handler (Phase 1E)

Centralised error-to-response mapper.
ALL modules MUST call handle_error() on failure.
"""

import copy
import time
from typing import Final

from core.config import FAILSAFE_RESPONSE
from core.logger import get_logger

logger = get_logger(__name__)

# Predefined messages per error type
_ERROR_MESSAGES: Final[dict[str, str]] = {
    "no_data":       "No services found nearby -- follow safest action",
    "invalid_input": "Invalid input received -- follow safest action",
    "api_failure":   "External API unreachable -- follow safest action",
    "timeout":       "Request timed out -- follow safest action",
}


def handle_error(error_type: str) -> dict:
    """Return a fail-safe response for the given error category.

    Args:
        error_type: One of 'no_data', 'invalid_input', 'api_failure', 'timeout'.

    Returns:
        A Response dict with status='fallback'.
    """
    start = time.time()
    logger.info("ENTER handle_error(error_type=%s)", error_type)

    response = copy.deepcopy(FAILSAFE_RESPONSE)

    if error_type in _ERROR_MESSAGES:
        response["message"] = _ERROR_MESSAGES[error_type]
    else:
        logger.warning("Unknown error_type '%s' -- using default failsafe", error_type)

    logger.info("EXIT handle_error -> %s", response["status"])
    logger.info("time_ms=%.2f", (time.time() - start) * 1000)
    return response


# --------------------------------------------------
# SELF-TEST
# --------------------------------------------------
def run_test() -> None:
    for etype in ("no_data", "invalid_input", "api_failure", "timeout"):
        r = handle_error(etype)
        assert r["status"] == "fallback", f"Expected fallback for {etype}"
        assert "primary_action" in r["data"], f"Missing primary_action for {etype}"
        assert "secondary_action" in r["data"], f"Missing secondary_action for {etype}"

    # Unknown error type still returns safe response
    r = handle_error("unknown_xyz")
    assert r["status"] == "fallback", "Unknown type must still return fallback"

    print("[PASS] edge_handler.py -- all assertions passed")


if __name__ == "__main__":
    run_test()
