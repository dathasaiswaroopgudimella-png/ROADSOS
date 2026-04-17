"""
RoadSoS — Fail-Safe Emergency Guidance System
Configuration Module (Phase 1A)

ALL system-wide constants are defined HERE and ONLY here.
No hardcoding is permitted in any other module.
"""

from typing import Final

# ──────────────────────────────────────────────
# SEARCH & DISTANCE THRESHOLDS
# ──────────────────────────────────────────────
MAX_RADIUS: Final[int] = 10                # km — maximum search radius
CRITICAL_DISTANCE: Final[int] = 3          # km — triggers elevated urgency
CACHE_EXPIRY_DAYS: Final[int] = 7          # days before cached data is stale
MAX_RESULTS: Final[int] = 2                # max services returned per query

# ──────────────────────────────────────────────
# TIMING CONSTRAINTS
# ──────────────────────────────────────────────
API_TIMEOUT_SEC: Final[int] = 2            # seconds — hard cap on any API call
BACKEND_TIME_LIMIT_MS: Final[int] = 500    # ms — total backend processing budget

# ──────────────────────────────────────────────
# CEIL (Community Emergency Impact Level) MAP
# ──────────────────────────────────────────────
CEIL_MAP: Final[dict[str, int]] = {
    "none":   0,
    "low":    1,
    "medium": 2,
    "high":   3,
}

# ──────────────────────────────────────────────
# API KEYS (loaded centrally — never hardcode elsewhere)
# ──────────────────────────────────────────────
OPENCAGE_API_KEY: Final[str]    = "180ee001cd874e7f8091c1423bc5c2f8"
GEOAPIFY_API_KEY: Final[str]    = "eb7d9953f5de4679a02b9265ebcf63df"
WEATHER_API_KEY: Final[str]     = "3adf7ce03c367a47f47837c24feaa382"
DEEPSEEK_API_KEY: Final[str]    = "sk-70d13c18a9b64afaa0ae24b2083d6539"
OPENAI_API_KEY: Final[str]      = "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"
IPINFO_API_KEY: Final[str]      = "ddf1976e6ec702"

# ──────────────────────────────────────────────
# FAIL-SAFE DEFAULT RESPONSE (MANDATORY)
# ──────────────────────────────────────────────
FAILSAFE_RESPONSE: Final[dict] = {
    "status": "fallback",
    "data": {
        "primary_action":   "Call ambulance now",
        "secondary_action": "Seek nearest help immediately",
    },
    "message": "System degraded — follow safest action",
}

# ──────────────────────────────────────────────
# SEVERITY LEVELS (canonical ordering)
# ──────────────────────────────────────────────
SEVERITY_LEVELS: Final[list[str]] = ["low", "medium", "critical"]


# ──────────────────────────────────────────────
# SELF-TEST
# ──────────────────────────────────────────────
def run_test() -> None:
    """Quick sanity check — importable by test_cases.py."""
    assert MAX_RADIUS == 10,                "MAX_RADIUS mismatch"
    assert CRITICAL_DISTANCE == 3,          "CRITICAL_DISTANCE mismatch"
    assert CACHE_EXPIRY_DAYS == 7,          "CACHE_EXPIRY_DAYS mismatch"
    assert MAX_RESULTS == 2,                "MAX_RESULTS mismatch"
    assert API_TIMEOUT_SEC == 2,            "API_TIMEOUT_SEC mismatch"
    assert BACKEND_TIME_LIMIT_MS == 500,    "BACKEND_TIME_LIMIT_MS mismatch"
    assert len(CEIL_MAP) == 4,              "CEIL_MAP incomplete"
    assert CEIL_MAP["high"] == 3,           "CEIL_MAP[high] wrong"
    assert FAILSAFE_RESPONSE["status"] == "fallback", "Failsafe format broken"
    assert "primary_action" in FAILSAFE_RESPONSE["data"], "Failsafe data missing"
    print("[PASS] config.py -- all assertions passed")


if __name__ == "__main__":
    run_test()
