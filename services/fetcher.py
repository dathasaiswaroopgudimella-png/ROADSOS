"""
RoadSoS -- Fail-Safe Emergency Guidance System
Fetcher Service (Phase 4)

Fetches nearby emergency services via Geoapify Places API.
Uses timeout wrapper. Falls back to cache/edge_handler on failure.
"""

import copy
import time
from typing import Any

try:
    import requests
except ImportError:
    requests = None  # type: ignore

from core.config import (
    API_TIMEOUT_SEC,
    FAILSAFE_RESPONSE,
    GEOAPIFY_API_KEY,
    MAX_RADIUS,
    MAX_RESULTS,
)
from core.edge_handler import handle_error
from core.logger import get_logger
from core.timeout import run_with_timeout
from data.offline_cache import get_cached_services

logger = get_logger(__name__)

_GEOAPIFY_URL = "https://api.geoapify.com/v2/places"

# Geoapify categories for emergency services
_CATEGORIES = "healthcare.hospital,emergency.ambulance_station,healthcare.clinic"


def _call_geoapify(lat: float, lon: float) -> dict:
    """Raw API call -- wrapped by run_with_timeout."""
    if requests is None:
        raise RuntimeError("requests library not installed")

    resp = requests.get(
        _GEOAPIFY_URL,
        params={
            "categories": _CATEGORIES,
            "filter": f"circle:{lon},{lat},{MAX_RADIUS * 1000}",
            "bias": f"proximity:{lon},{lat}",
            "limit": MAX_RESULTS,
            "apiKey": GEOAPIFY_API_KEY,
        },
        timeout=API_TIMEOUT_SEC,
    )
    resp.raise_for_status()
    data = resp.json()

    features = data.get("features", [])
    if not features:
        return {"status": "error", "data": None, "message": "No places found"}

    services = []
    for feat in features:
        props = feat.get("properties", {})
        services.append({
            "name": props.get("name", "Unknown Service"),
            "lat": props.get("lat", 0.0),
            "lon": props.get("lon", 0.0),
            "type": props.get("categories", ["unknown"])[0] if props.get("categories") else "unknown",
            "distance_km": round(props.get("distance", 0) / 1000, 2),
            "address": props.get("formatted", ""),
        })

    return {
        "status": "ok",
        "data": services,
        "message": f"Found {len(services)} services",
    }


def get_services(lat: float, lon: float, logger_: Any = None) -> dict:
    """Fetch nearby emergency services.

    Args:
        lat: Latitude.
        lon: Longitude.
        logger_: Optional logger.

    Returns:
        Response dict with list of services in data field.
    """
    log = logger_ or logger
    start = time.time()
    log.info("ENTER get_services(lat=%.4f, lon=%.4f)", lat, lon)

    try:
        result = run_with_timeout(_call_geoapify, API_TIMEOUT_SEC, lat, lon)

        if result.get("status") in ("ok",):
            log.info("EXIT get_services -> %d services (API)", len(result["data"]))
            return result

        # API failed -- fall back to cache
        log.warning("API failed, falling back to cache: %s", result.get("message"))
        cache_result = get_cached_services(lat, lon, float(MAX_RADIUS), log)

        if cache_result.get("status") == "ok":
            cache_result["status"] = "fallback"
            cache_result["message"] = "Served from offline cache (API unavailable)"
            log.info("EXIT get_services -> cache fallback (%d services)", len(cache_result["data"]))
            return cache_result

        return handle_error("no_data")

    except Exception as exc:
        log.error("CRITICAL FAILURE in get_services: %s", exc)
        # Last resort: cache
        try:
            cache_result = get_cached_services(lat, lon, float(MAX_RADIUS), log)
            if cache_result.get("status") == "ok":
                cache_result["status"] = "fallback"
                return cache_result
        except Exception:
            pass
        return copy.deepcopy(FAILSAFE_RESPONSE)
    finally:
        log.info("time_ms=%.2f", (time.time() - start) * 1000)


# --------------------------------------------------
# SELF-TEST
# --------------------------------------------------
def run_test() -> None:
    log = get_logger("test_fetcher")

    # Live call (may fail without network -- cache should save us)
    r = get_services(28.6139, 77.2090, log)
    assert r["status"] in ("ok", "fallback"), f"Unexpected status: {r['status']}"
    if r["status"] == "ok":
        assert isinstance(r["data"], list), "Data should be a list"

    print("[PASS] fetcher.py -- all assertions passed")


if __name__ == "__main__":
    run_test()
