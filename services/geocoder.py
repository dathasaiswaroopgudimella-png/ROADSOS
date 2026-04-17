"""
RoadSoS -- Fail-Safe Emergency Guidance System
Geocoder Service (Phase 4)

Converts a location string to (lat, lon) via OpenCage API.
Uses timeout wrapper. Falls back to edge_handler on failure.
"""

import copy
import time
from typing import Any

try:
    import requests
except ImportError:
    requests = None  # type: ignore

from core.config import API_TIMEOUT_SEC, FAILSAFE_RESPONSE, OPENCAGE_API_KEY
from core.edge_handler import handle_error
from core.logger import get_logger
from core.timeout import run_with_timeout

logger = get_logger(__name__)

_OPENCAGE_URL = "https://api.opencagedata.com/geocode/v1/json"


def _call_opencage(location: str) -> dict:
    """Raw API call -- wrapped by run_with_timeout."""
    if requests is None:
        raise RuntimeError("requests library not installed")

    resp = requests.get(
        _OPENCAGE_URL,
        params={"q": location, "key": OPENCAGE_API_KEY, "limit": 1},
        timeout=API_TIMEOUT_SEC,
    )
    resp.raise_for_status()
    data = resp.json()

    results = data.get("results", [])
    if not results:
        return {"status": "error", "data": None, "message": "No geocoding results"}

    geo = results[0].get("geometry", {})
    return {
        "status": "ok",
        "data": {
            "lat": geo.get("lat", 0.0),
            "lon": geo.get("lng", 0.0),
            "formatted": results[0].get("formatted", location),
        },
        "message": "Geocoded successfully",
    }


def get_coordinates(location: str, logger_: Any = None) -> dict:
    """Geocode a location string to coordinates.

    Args:
        location: Human-readable address or place name.
        logger_: Optional logger.

    Returns:
        Response dict with lat/lon in data field.
    """
    log = logger_ or logger
    start = time.time()
    log.info("ENTER get_coordinates(location=%s)", location)

    try:
        if not location or not isinstance(location, str):
            log.warning("Invalid location input")
            return handle_error("invalid_input")

        result = run_with_timeout(_call_opencage, API_TIMEOUT_SEC, location)

        if result.get("status") == "error":
            log.warning("Geocoding failed: %s", result.get("message"))
            return handle_error("api_failure")

        log.info("EXIT get_coordinates -> %s", result.get("data"))
        return result

    except Exception as exc:
        log.error("CRITICAL FAILURE in get_coordinates: %s", exc)
        return handle_error("api_failure")
    finally:
        log.info("time_ms=%.2f", (time.time() - start) * 1000)


# --------------------------------------------------
# SELF-TEST
# --------------------------------------------------
def run_test() -> None:
    log = get_logger("test_geocoder")

    # Invalid input
    r = get_coordinates("", log)
    assert r["status"] == "fallback", f"Expected fallback for empty input, got {r['status']}"

    r2 = get_coordinates(None, log)  # type: ignore
    assert r2["status"] == "fallback", f"Expected fallback for None, got {r2['status']}"

    # Live API call (may fail without network -- that's safe)
    r3 = get_coordinates("New Delhi, India", log)
    assert r3["status"] in ("ok", "fallback"), f"Unexpected status: {r3['status']}"
    if r3["status"] == "ok":
        assert "lat" in r3["data"], "Missing lat"
        assert "lon" in r3["data"], "Missing lon"

    print("[PASS] geocoder.py -- all assertions passed")


if __name__ == "__main__":
    run_test()
