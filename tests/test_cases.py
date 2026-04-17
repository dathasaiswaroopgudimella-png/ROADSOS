"""
RoadSoS -- Fail-Safe Emergency Guidance System
Test Cases (Phase 8)

All tests use assert -- NO print-only tests.
"""

import sys
import os
import time

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.config import (
    CEIL_MAP, CRITICAL_DISTANCE, FAILSAFE_RESPONSE,
    MAX_RADIUS, MAX_RESULTS, API_TIMEOUT_SEC, BACKEND_TIME_LIMIT_MS,
    CACHE_EXPIRY_DAYS, SEVERITY_LEVELS,
)
from core.logger import get_logger
from core.validator import validate_coordinates, validate_services_list
from core.timeout import run_with_timeout
from core.edge_handler import handle_error
from core.decision_engine import make_decision
from data.offline_cache import get_cached_services
from services.ceil import get_ceil_signal

logger = get_logger("test_cases")


# ==========================================================
# CONFIG TESTS
# ==========================================================
def test_config_constants() -> None:
    assert MAX_RADIUS == 10
    assert CRITICAL_DISTANCE == 3
    assert CACHE_EXPIRY_DAYS == 7
    assert MAX_RESULTS == 2
    assert API_TIMEOUT_SEC == 2
    assert BACKEND_TIME_LIMIT_MS == 500
    assert len(CEIL_MAP) == 4
    assert CEIL_MAP["high"] == 3
    assert FAILSAFE_RESPONSE["status"] == "fallback"
    assert "primary_action" in FAILSAFE_RESPONSE["data"]
    print("[PASS] test_config_constants")


# ==========================================================
# VALIDATOR TESTS
# ==========================================================
def test_validate_coordinates_valid() -> None:
    assert validate_coordinates(28.6, 77.2) == (28.6, 77.2)
    assert validate_coordinates(0, 0) == (0.0, 0.0)
    assert validate_coordinates(-90, -180) == (-90.0, -180.0)
    assert validate_coordinates(90, 180) == (90.0, 180.0)
    print("[PASS] test_validate_coordinates_valid")


def test_validate_coordinates_invalid() -> None:
    for bad_lat, bad_lon in [(100, 0), (-91, 0), (0, 181), (0, -181)]:
        try:
            validate_coordinates(bad_lat, bad_lon)
            assert False, f"Should have raised for ({bad_lat}, {bad_lon})"
        except ValueError:
            pass

    # Type errors
    for bad in [("a", 0), (0, "b"), (None, 0)]:
        try:
            validate_coordinates(bad[0], bad[1])  # type: ignore
            assert False, f"Should have raised for {bad}"
        except ValueError:
            pass

    print("[PASS] test_validate_coordinates_invalid")


def test_validate_services_list() -> None:
    good = [{"name": "Hospital", "distance": 1.0}]
    assert validate_services_list(good) == good

    # Empty list is valid
    assert validate_services_list([]) == []

    # Invalid structures
    for bad in ["not_list", [123], [{"no_name_key": True}]]:
        try:
            validate_services_list(bad)  # type: ignore
            assert False, f"Should have raised for {bad}"
        except ValueError:
            pass

    print("[PASS] test_validate_services_list")


# ==========================================================
# TIMEOUT TESTS
# ==========================================================
def test_timeout_fast() -> None:
    def fast(x: int) -> dict:
        return {"status": "ok", "data": x, "message": ""}
    r = run_with_timeout(fast, 2, 42)
    assert r["status"] == "ok"
    assert r["data"] == 42
    print("[PASS] test_timeout_fast")


def test_timeout_slow() -> None:
    def slow() -> dict:
        time.sleep(5)
        return {"status": "ok", "data": None, "message": ""}
    r = run_with_timeout(slow, 1)
    assert r["status"] == "error"
    assert "Timeout" in r["message"]
    print("[PASS] test_timeout_slow")


# ==========================================================
# EDGE HANDLER TESTS
# ==========================================================
def test_edge_handler_known_types() -> None:
    for etype in ("no_data", "invalid_input", "api_failure", "timeout"):
        r = handle_error(etype)
        assert r["status"] == "fallback"
        assert "primary_action" in r["data"]
        assert "secondary_action" in r["data"]
    print("[PASS] test_edge_handler_known_types")


def test_edge_handler_unknown_type() -> None:
    r = handle_error("totally_unknown")
    assert r["status"] == "fallback"
    print("[PASS] test_edge_handler_unknown_type")


# ==========================================================
# DECISION ENGINE TESTS
# ==========================================================
def test_decision_critical() -> None:
    r = make_decision("critical", 1.0, [{"name": "Hospital"}], "none", logger)
    assert r["data"]["primary_action"] == "Call ambulance now"
    assert r["data"]["tier_used"] == "critical"
    print("[PASS] test_decision_critical")


def test_decision_empty_services() -> None:
    r = make_decision("low", 5.0, [], "none", logger)
    assert r["data"]["primary_action"] == "Call ambulance now"
    assert r["data"]["tier_used"] == "critical"
    print("[PASS] test_decision_empty_services")


def test_decision_invalid_severity() -> None:
    r = make_decision("garbage", 5.0, [{"name": "X"}], "none", logger)
    assert r["data"]["tier_used"] == "critical"
    print("[PASS] test_decision_invalid_severity")


def test_decision_ceil_escalation() -> None:
    r = make_decision("medium", 5.0, [{"name": "Clinic"}], "high", logger)
    assert r["data"]["tier_used"] == "critical"
    print("[PASS] test_decision_ceil_escalation")


def test_decision_low_stays_low() -> None:
    r = make_decision("low", 8.0, [{"name": "Clinic"}], "none", logger)
    assert r["data"]["tier_used"] == "low"
    print("[PASS] test_decision_low_stays_low")


def test_decision_distance_escalation() -> None:
    r = make_decision("low", 2.0, [{"name": "Clinic"}], "none", logger)
    assert r["data"]["tier_used"] == "critical"
    print("[PASS] test_decision_distance_escalation")


# ==========================================================
# CACHE TESTS
# ==========================================================
def test_cache_services() -> None:
    r = get_cached_services(28.6139, 77.2090, 10.0, logger)
    assert r["status"] == "ok"
    assert isinstance(r["data"], list)
    assert len(r["data"]) <= MAX_RESULTS
    print("[PASS] test_cache_services")


def test_cache_no_results() -> None:
    r = get_cached_services(0.0, 0.0, 0.01, logger)
    assert r["status"] == "fallback"
    print("[PASS] test_cache_no_results")


# ==========================================================
# CEIL TESTS
# ==========================================================
def test_ceil_signal() -> None:
    sig = get_ceil_signal(logger)
    assert sig in {"none", "low", "medium", "high"}
    print("[PASS] test_ceil_signal")


# ==========================================================
# RUNNER
# ==========================================================
_ALL_TESTS = [
    test_config_constants,
    test_validate_coordinates_valid,
    test_validate_coordinates_invalid,
    test_validate_services_list,
    test_timeout_fast,
    test_timeout_slow,
    test_edge_handler_known_types,
    test_edge_handler_unknown_type,
    test_decision_critical,
    test_decision_empty_services,
    test_decision_invalid_severity,
    test_decision_ceil_escalation,
    test_decision_low_stays_low,
    test_decision_distance_escalation,
    test_cache_services,
    test_cache_no_results,
    test_ceil_signal,
]


def run_test() -> None:
    passed = 0
    failed = 0
    for t in _ALL_TESTS:
        try:
            t()
            passed += 1
        except Exception as exc:
            failed += 1
            print(f"[FAIL] {t.__name__}: {exc}")

    total = passed + failed
    print(f"\n{'='*50}")
    print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
    print(f"{'='*50}")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_test()
