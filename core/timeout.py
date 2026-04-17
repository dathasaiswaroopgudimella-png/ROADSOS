"""
RoadSoS -- Fail-Safe Emergency Guidance System
Timeout Wrapper (Phase 1D)

Wraps ANY callable with a hard time limit.
If the callable exceeds the limit, returns an error response.
ALL API calls MUST use this.
"""

import time
import threading
from typing import Any, Callable

from core.logger import get_logger

logger = get_logger(__name__)


def run_with_timeout(func: Callable, timeout_sec: int, *args: Any) -> dict:
    """Execute *func* with a hard timeout.

    Args:
        func: Callable to execute.
        timeout_sec: Maximum seconds to wait.
        *args: Positional args forwarded to *func*.

    Returns:
        The return value of *func* if it completes in time,
        otherwise {"status": "error", "data": None, "message": "..."}.
    """
    start = time.time()
    logger.info("ENTER run_with_timeout(func=%s, timeout=%ds)", func.__name__, timeout_sec)

    result_container: list[Any] = []
    error_container: list[Exception] = []

    def target() -> None:
        try:
            result_container.append(func(*args))
        except Exception as exc:
            error_container.append(exc)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout_sec)

    elapsed = (time.time() - start) * 1000
    logger.info("time_ms=%.2f", elapsed)

    if thread.is_alive():
        logger.error("TIMEOUT after %ds for %s", timeout_sec, func.__name__)
        return {
            "status": "error",
            "data": None,
            "message": f"Timeout: {func.__name__} exceeded {timeout_sec}s",
        }

    if error_container:
        logger.error("ERROR in %s: %s", func.__name__, error_container[0])
        return {
            "status": "error",
            "data": None,
            "message": f"Error in {func.__name__}: {error_container[0]}",
        }

    if result_container:
        logger.info("EXIT run_with_timeout -> success")
        return result_container[0]

    logger.error("No result from %s", func.__name__)
    return {
        "status": "error",
        "data": None,
        "message": f"No result from {func.__name__}",
    }


# --------------------------------------------------
# SELF-TEST
# --------------------------------------------------
def run_test() -> None:
    import time as t

    def fast_fn(x: int) -> dict:
        return {"status": "ok", "data": x * 2, "message": "fast"}

    def slow_fn() -> dict:
        t.sleep(5)
        return {"status": "ok", "data": None, "message": "slow"}

    # Fast function completes
    r = run_with_timeout(fast_fn, 2, 21)
    assert r["status"] == "ok", f"Expected ok, got {r['status']}"
    assert r["data"] == 42, f"Expected 42, got {r['data']}"

    # Slow function times out
    r = run_with_timeout(slow_fn, 1)
    assert r["status"] == "error", f"Expected error, got {r['status']}"
    assert "Timeout" in r["message"], f"Expected timeout message, got {r['message']}"

    print("[PASS] timeout.py -- all assertions passed")


if __name__ == "__main__":
    run_test()
