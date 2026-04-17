"""
RoadSoS -- Fail-Safe Emergency Guidance System
Validator Module (Phase 1C)

Strict type validation for coordinates and service lists.
Invalid input raises ValueError -- handled by edge_handler.
"""

import time
from typing import Any

from core.logger import get_logger

logger = get_logger(__name__)


def validate_coordinates(lat: float, lon: float) -> tuple[float, float]:
    """Validate and return (lat, lon).

    Args:
        lat: Latitude, must be float/int in [-90, 90].
        lon: Longitude, must be float/int in [-180, 180].

    Returns:
        Tuple of (lat, lon) as floats.

    Raises:
        ValueError: If types or ranges are invalid.
    """
    start = time.time()
    logger.info("ENTER validate_coordinates(lat=%s, lon=%s)", lat, lon)
    try:
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            raise ValueError(
                f"Coordinates must be numeric. Got lat={type(lat).__name__}, lon={type(lon).__name__}"
            )

        lat_f, lon_f = float(lat), float(lon)

        if not (-90.0 <= lat_f <= 90.0):
            raise ValueError(f"Latitude {lat_f} out of range [-90, 90]")
        if not (-180.0 <= lon_f <= 180.0):
            raise ValueError(f"Longitude {lon_f} out of range [-180, 180]")

        logger.info("EXIT validate_coordinates -> (%s, %s)", lat_f, lon_f)
        return lat_f, lon_f
    except ValueError:
        raise
    finally:
        logger.info("time_ms=%.2f", (time.time() - start) * 1000)


def validate_services_list(services: list[dict]) -> list[dict]:
    """Validate that services is a list of dicts with required keys.

    Args:
        services: List of service dicts. Each must have 'name' and 'distance'.

    Returns:
        The validated list (unchanged if valid).

    Raises:
        ValueError: If structure is invalid.
    """
    start = time.time()
    logger.info("ENTER validate_services_list(count=%s)", len(services) if isinstance(services, list) else "N/A")
    try:
        if not isinstance(services, list):
            raise ValueError(f"Services must be a list. Got {type(services).__name__}")

        for i, svc in enumerate(services):
            if not isinstance(svc, dict):
                raise ValueError(f"Service[{i}] must be a dict. Got {type(svc).__name__}")
            if "name" not in svc:
                raise ValueError(f"Service[{i}] missing required key 'name'")

        logger.info("EXIT validate_services_list -> %d valid services", len(services))
        return services
    except ValueError:
        raise
    finally:
        logger.info("time_ms=%.2f", (time.time() - start) * 1000)


# --------------------------------------------------
# SELF-TEST
# --------------------------------------------------
def run_test() -> None:
    # Valid coordinates
    assert validate_coordinates(28.6, 77.2) == (28.6, 77.2)

    # Invalid coordinates
    try:
        validate_coordinates(100.0, 77.2)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    # Type error
    try:
        validate_coordinates("bad", 77.2)  # type: ignore
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    # Valid services
    svcs = [{"name": "Hospital A", "distance": 1.2}]
    assert validate_services_list(svcs) == svcs

    # Invalid services
    try:
        validate_services_list("not_a_list")  # type: ignore
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    try:
        validate_services_list([{"no_name": True}])
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    print("[PASS] validator.py -- all assertions passed")


if __name__ == "__main__":
    run_test()
