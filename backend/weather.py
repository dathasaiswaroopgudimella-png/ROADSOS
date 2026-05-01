"""
RoadSoS — Omniscient Architect Protocol v5.0
Weather Engine: Real-time weather context for emergency triage.

Uses WeatherAPI to provide conditions that affect emergency response:
- Heavy rain → longer ambulance ETAs
- Floods → route changes
- Low visibility → increased danger
"""

import httpx
from backend.config import WEATHER_API_KEY, API_TIMEOUT_SEC


async def get_weather(lat: float, lon: float) -> dict:
    """Fetch current weather conditions for a location.

    Returns weather context relevant to emergency response.
    """
    if not WEATHER_API_KEY:
        return {"status": "unavailable", "message": "Weather API key not configured"}

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT_SEC) as client:
            resp = await client.get(
                "http://api.weatherapi.com/v1/current.json",
                params={
                    "key": WEATHER_API_KEY,
                    "q": f"{lat},{lon}",
                    "aqi": "no"
                }
            )
            resp.raise_for_status()
            data = resp.json()

            current = data.get("current", {})
            condition = current.get("condition", {})
            location = data.get("location", {})

            # Determine emergency impact
            precip_mm = current.get("precip_mm", 0)
            wind_kph = current.get("wind_kph", 0)
            vis_km = current.get("vis_km", 10)
            temp_c = current.get("temp_c", 25)

            impact = "normal"
            warnings = []

            if precip_mm > 10:
                impact = "severe"
                warnings.append(f"Heavy precipitation ({precip_mm}mm) — ambulance delays expected")
            elif precip_mm > 2:
                impact = "moderate"
                warnings.append(f"Rain ({precip_mm}mm) — roads may be slippery")

            if vis_km < 1:
                impact = "severe"
                warnings.append(f"Very low visibility ({vis_km}km) — extreme caution")
            elif vis_km < 5:
                if impact != "severe":
                    impact = "moderate"
                warnings.append(f"Reduced visibility ({vis_km}km)")

            if wind_kph > 60:
                impact = "severe"
                warnings.append(f"High winds ({wind_kph}kph) — travel dangerous")

            if temp_c > 45:
                warnings.append(f"Extreme heat ({temp_c}°C) — heatstroke risk")
            elif temp_c < 5:
                warnings.append(f"Cold conditions ({temp_c}°C) — hypothermia risk")

            return {
                "status": "ok",
                "temperature_c": temp_c,
                "condition": condition.get("text", "Unknown"),
                "condition_icon": condition.get("icon", ""),
                "humidity": current.get("humidity", 0),
                "wind_kph": wind_kph,
                "visibility_km": vis_km,
                "precipitation_mm": precip_mm,
                "feels_like_c": current.get("feelslike_c", temp_c),
                "location_name": location.get("name", ""),
                "impact": impact,
                "warnings": warnings,
                "summary": _build_summary(condition.get("text", ""), temp_c, precip_mm, vis_km, warnings)
            }

    except Exception as e:
        print(f"[WEATHER] API failed: {e}")
        return {"status": "error", "message": str(e)}


def _build_summary(condition: str, temp: float, precip: float, vis: float, warnings: list) -> str:
    """Build a human-readable weather summary for AI context."""
    parts = [f"Current conditions: {condition}, {temp}°C"]
    if precip > 0:
        parts.append(f"Precipitation: {precip}mm")
    if vis < 10:
        parts.append(f"Visibility: {vis}km")
    if warnings:
        parts.append("Warnings: " + "; ".join(warnings))
    return ". ".join(parts)
