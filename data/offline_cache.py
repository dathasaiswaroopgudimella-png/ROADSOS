"""
RoadSoS -- Fail-Safe Emergency Guidance System
Offline Cache (Phase 3)

Serves cached/demo service data when APIs are unavailable.
Query time target: < 100 ms.
"""

import copy
import json
import math
import os
import time
from typing import Any

from core.config import CACHE_EXPIRY_DAYS, FAILSAFE_RESPONSE, MAX_RESULTS
from core.edge_handler import handle_error
from core.logger import get_logger

logger = get_logger(__name__)

_DATA_DIR = os.path.join(os.path.dirname(__file__))
_DEMO_PATH = os.path.join(_DATA_DIR, "demo_data.json")

# In-memory cache: key = "lat,lon,radius" -> {"ts": epoch, "services": [...]}
_cache: dict[str, dict[str, Any]] = {}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate distance in km between two coordinates."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _load_demo_data() -> list[dict]:
    """Load demo_data.json from disk."""
    try:
        with open(_DEMO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error("Failed to load demo data: %s", exc)
        return []


def get_cached_services(lat: float, lon: float, radius: float, logger_: Any = None) -> dict:
    """Return nearby services from cache or demo data.

    Args:
        lat: Latitude.
        lon: Longitude.
        radius: Search radius in km.
        logger_: Optional logger.

    Returns:
        Response dict.
    """
    log = logger_ or logger
    start = time.time()
    log.info("ENTER get_cached_services(lat=%.4f, lon=%.4f, radius=%.1f)", lat, lon, radius)

    try:
        cache_key = f"{lat:.4f},{lon:.4f},{radius:.1f}"

        # Check in-memory cache freshness
        if cache_key in _cache:
            entry = _cache[cache_key]
            age_days = (time.time() - entry["ts"]) / 86400
            if age_days < CACHE_EXPIRY_DAYS:
                log.info("Cache HIT (age=%.1f days)", age_days)
                return {
                    "status": "ok",
                    "data": entry["services"],
                    "message": "Served from cache",
                }
            else:
                log.info("Cache EXPIRED (age=%.1f days)", age_days)

        # Fall back to demo data
        all_services = _load_demo_data()
        if not all_services:
            log.warning("No demo data available")
            return handle_error("no_data")

        # Filter by radius and sort by distance
        nearby = []
        for svc in all_services:
            dist = _haversine_km(lat, lon, svc.get("lat", 0), svc.get("lon", 0))
            svc_copy = copy.deepcopy(svc)
            svc_copy["distance_km"] = round(dist, 2)
            if dist <= radius:
                nearby.append(svc_copy)

        nearby.sort(key=lambda s: s["distance_km"])
        nearby = nearby[:MAX_RESULTS]

        if not nearby:
            log.warning("No services within %.1f km", radius)
            return handle_error("no_data")

        # Store in cache
        _cache[cache_key] = {"ts": time.time(), "services": nearby}

        log.info("EXIT get_cached_services -> %d services", len(nearby))
        return {
            "status": "ok",
            "data": nearby,
            "message": f"Found {len(nearby)} services within {radius} km",
        }

    except Exception as exc:
        log.error("CRITICAL FAILURE in get_cached_services: %s", exc)
        return copy.deepcopy(FAILSAFE_RESPONSE)
    finally:
        log.info("time_ms=%.2f", (time.time() - start) * 1000)


# --------------------------------------------------
# SELF-TEST
# --------------------------------------------------
def run_test() -> None:
    log = get_logger("test_cache")

    # Should find services near demo coordinates
    r = get_cached_services(28.6139, 77.2090, 10.0, log)
    assert r["status"] == "ok", f"Expected ok, got {r['status']}"
    assert isinstance(r["data"], list), "Data should be a list"
    assert len(r["data"]) <= MAX_RESULTS, f"Too many results: {len(r['data'])}"

    # Second call should be cache hit
    r2 = get_cached_services(28.6139, 77.2090, 10.0, log)
    assert r2["message"] == "Served from cache", f"Expected cache hit: {r2['message']}"

    # Very small radius should trigger no_data
    r3 = get_cached_services(0.0, 0.0, 0.01, log)
    assert r3["status"] == "fallback", f"Expected fallback, got {r3['status']}"

    print("[PASS] offline_cache.py -- all assertions passed")


if __name__ == "__main__":
    run_test()
