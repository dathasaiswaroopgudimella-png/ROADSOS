"""
RoadSoS — Omniscient Architect Protocol v5.0
Geocoding Engine: Dual-source (OpenCage + Geoapify) geocoding.

Converts pincode/district/town/address → lat/lon coordinates.
Falls back between providers for maximum reliability.
"""

import httpx
from backend.config import OPENCAGE_API_KEY, GEOAPIFY_API_KEY, IPINFO_API_KEY, API_TIMEOUT_SEC


async def geocode_opencage(query: str) -> dict | None:
    """Geocode using OpenCage API."""
    if not OPENCAGE_API_KEY:
        return None

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT_SEC) as client:
            resp = await client.get(
                "https://api.opencagedata.com/geocode/v1/json",
                params={"q": query, "key": OPENCAGE_API_KEY, "limit": 1, "countrycode": "in"}
            )
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            if results:
                geo = results[0].get("geometry", {})
                components = results[0].get("components", {})
                return {
                    "lat": geo.get("lat"),
                    "lon": geo.get("lng"),
                    "formatted": results[0].get("formatted", query),
                    "state": components.get("state", ""),
                    "district": components.get("county", components.get("state_district", "")),
                    "source": "opencage"
                }
    except Exception as e:
        print(f"[GEOCODE] OpenCage failed: {e}")

    return None


async def geocode_geoapify(query: str) -> dict | None:
    """Geocode using Geoapify API."""
    if not GEOAPIFY_API_KEY:
        return None

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT_SEC) as client:
            resp = await client.get(
                "https://api.geoapify.com/v1/geocode/search",
                params={
                    "text": query,
                    "apiKey": GEOAPIFY_API_KEY,
                    "limit": 1,
                    "filter": "countrycode:in"
                }
            )
            resp.raise_for_status()
            data = resp.json()

            features = data.get("features", [])
            if features:
                props = features[0].get("properties", {})
                return {
                    "lat": props.get("lat"),
                    "lon": props.get("lon"),
                    "formatted": props.get("formatted", query),
                    "state": props.get("state", ""),
                    "district": props.get("county", ""),
                    "source": "geoapify"
                }
    except Exception as e:
        print(f"[GEOCODE] Geoapify failed: {e}")

    return None


async def geocode_ipinfo(ip: str = "") -> dict | None:
    """Fallback: get approximate location from IP using IPInfo."""
    if not IPINFO_API_KEY:
        return None

    try:
        url = f"https://ipinfo.io/{ip}/json" if ip else "https://ipinfo.io/json"
        async with httpx.AsyncClient(timeout=API_TIMEOUT_SEC) as client:
            resp = await client.get(url, params={"token": IPINFO_API_KEY})
            resp.raise_for_status()
            data = resp.json()

            loc = data.get("loc", "")
            if loc:
                parts = loc.split(",")
                return {
                    "lat": float(parts[0]),
                    "lon": float(parts[1]),
                    "formatted": f"{data.get('city', '')}, {data.get('region', '')}",
                    "state": data.get("region", ""),
                    "district": data.get("city", ""),
                    "source": "ipinfo"
                }
    except Exception as e:
        print(f"[GEOCODE] IPInfo failed: {e}")

    return None


async def geocode(query: str) -> dict:
    """Geocode a query string using dual-source fusion.

    Tries OpenCage first, falls back to Geoapify, then IPInfo.
    Returns dict with lat, lon, formatted address, source.
    """
    # Try OpenCage (highest quality for India)
    result = await geocode_opencage(query)
    if result and result.get("lat"):
        return {"status": "ok", **result}

    # Fallback to Geoapify
    result = await geocode_geoapify(query)
    if result and result.get("lat"):
        return {"status": "ok", **result}

    return {"status": "error", "message": f"Could not geocode: {query}"}


async def geocode_with_ip_fallback(query: str = "", ip: str = "") -> dict:
    """Full fusion: try text geocoding, then IP fallback."""
    if query:
        result = await geocode(query)
        if result.get("status") == "ok":
            return result

    # IP fallback
    result = await geocode_ipinfo(ip)
    if result and result.get("lat"):
        return {"status": "fallback", **result}

    return {"status": "error", "message": "All geocoding sources failed"}
