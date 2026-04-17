"""
RoadSoS -- Fail-Safe Emergency Guidance System
Decision Engine (Phase 2)

Takes severity, distance, services, and CEIL signal
and produces human-readable imperative guidance.
"""

import copy
import time
from typing import Any

from core.config import (
    CEIL_MAP,
    CRITICAL_DISTANCE,
    FAILSAFE_RESPONSE,
    SEVERITY_LEVELS,
)
from core.logger import get_logger

logger = get_logger(__name__)

# ── Tiered action tables ────────────────────────
_ACTIONS: dict[str, dict[str, str]] = {
    "critical": {
        "primary_action":   "Call ambulance now",
        "secondary_action": "Apply first aid immediately",
    },
    "medium": {
        "primary_action":   "Go to nearest hospital",
        "secondary_action": "Call emergency helpline",
    },
    "low": {
        "primary_action":   "Visit nearby clinic",
        "secondary_action": "Monitor the situation",
    },
}


def make_decision(
    severity: str,
    distance: float,
    services: list[dict],
    ceil_signal: str,
    logger_: Any = None,
) -> dict:
    """Produce an action recommendation.

    Args:
        severity:    'low' | 'medium' | 'critical'
        distance:    Distance to nearest service in km.
        services:    List of service dicts.
        ceil_signal: CEIL level string ('none'|'low'|'medium'|'high').
        logger_:     Optional logger override.

    Returns:
        Response dict with status, data (actions + tier_used), and message.
    """
    log = logger_ or logger
    start = time.time()
    log.info(
        "ENTER make_decision(severity=%s, distance=%.2f, services=%d, ceil=%s)",
        severity, distance, len(services) if isinstance(services, list) else 0, ceil_signal,
    )

    try:
        # --- Validate severity ---------------------------------
        if severity not in SEVERITY_LEVELS:
            log.warning("Invalid severity '%s' -- defaulting to critical", severity)
            severity = "critical"

        # --- CEIL influence ------------------------------------
        ceil_value = CEIL_MAP.get(ceil_signal, 0)
        severity_index = SEVERITY_LEVELS.index(severity)
        severity_index += ceil_value // 2
        severity_index = min(severity_index, len(SEVERITY_LEVELS) - 1)
        effective_severity = SEVERITY_LEVELS[severity_index]

        # --- Distance escalation --------------------------------
        if distance <= CRITICAL_DISTANCE:
            effective_severity = "critical"

        # --- No services fallback -------------------------------
        if not services:
            log.warning("No services available -- escalating to critical")
            effective_severity = "critical"

        # --- Build response -------------------------------------
        actions = _ACTIONS[effective_severity]
        result = {
            "status": "ok",
            "data": {
                "primary_action":   actions["primary_action"],
                "secondary_action": actions["secondary_action"],
                "tier_used":        effective_severity,
            },
            "message": f"Decision made at {effective_severity} tier",
        }

        log.info("EXIT make_decision -> tier=%s", effective_severity)
        return result

    except Exception as exc:
        log.error("CRITICAL FAILURE in make_decision: %s", exc)
        return copy.deepcopy(FAILSAFE_RESPONSE)
    finally:
        log.info("time_ms=%.2f", (time.time() - start) * 1000)


# --------------------------------------------------
# SELF-TEST
# --------------------------------------------------
def run_test() -> None:
    log = get_logger("test_decision_engine")

    # Critical case
    r = make_decision("critical", 1.0, [{"name": "Hospital"}], "none", log)
    assert r["data"]["primary_action"] == "Call ambulance now", f"Got: {r}"

    # Empty services -> should escalate
    r = make_decision("low", 5.0, [], "none", log)
    assert r["data"]["primary_action"] == "Call ambulance now", f"Got: {r}"

    # Distance escalation
    r = make_decision("low", 2.0, [{"name": "Clinic"}], "none", log)
    assert r["data"]["tier_used"] == "critical", f"Got: {r}"

    # CEIL influence: medium severity + high ceil -> critical
    r = make_decision("medium", 5.0, [{"name": "Clinic"}], "high", log)
    assert r["data"]["tier_used"] == "critical", f"Got: {r}"

    # Low severity stays low when distance is far and ceil is none
    r = make_decision("low", 8.0, [{"name": "Clinic"}], "none", log)
    assert r["data"]["tier_used"] == "low", f"Got: {r}"

    # Invalid severity defaults to critical
    r = make_decision("garbage", 5.0, [{"name": "X"}], "none", log)
    assert r["data"]["tier_used"] == "critical", f"Got: {r}"

    print("[PASS] decision_engine.py -- all assertions passed")


if __name__ == "__main__":
    run_test()
