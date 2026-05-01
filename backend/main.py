"""
RoadSoS — Omniscient Architect Protocol v5.0
FastAPI Application: All endpoints for the emergency guidance system.

Endpoints:
  GET  /api/health          — System health + DB stats + API key status
  POST /api/emergency/guidance — Full emergency triage (GPS → hospitals → AI + weather)
  POST /api/search           — Search hospitals by pincode/district/town/name
  POST /api/geocode          — Geocode an address/pincode to lat/lon
  GET  /api/weather          — Get weather for a location
"""

import time
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from backend import database
from backend.config import (
    OPENCAGE_API_KEY, GEOAPIFY_API_KEY, WEATHER_API_KEY,
    DEEPSEEK_API_KEY, OPENAI_API_KEY, IPINFO_API_KEY,
    FAILSAFE_PLAN
)
from backend.models import (
    EmergencyRequest, EmergencyResponse, SearchRequest, SearchResponse,
    GeocodeRequest, GeocodeResponse, HealthResponse, HospitalResponse,
    ActionPlan, WeatherInfo
)
from backend.ai_triage import triage_racing
from backend.geocode import geocode, geocode_with_ip_fallback
from backend.weather import get_weather

# ──────────────────────────────────────────────
# Loguru Configuration
# ──────────────────────────────────────────────
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>"
)
logger.add("roadsos.log", rotation="10 MB", retention="7 days", compression="zip")

# ──────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────
app = FastAPI(
    title="RoadSoS — Omniscient Emergency Guidance API",
    description="Production-grade emergency guidance with 10,000+ hospitals, AI triage, and weather-aware routing.",
    version="5.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# ──────────────────────────────────────────────
# Startup: Initialize database + cKDTree
# ──────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    logger.info("[STARTUP] Initializing RoadSoS Omniscient Engine...")
    try:
        database.initialize()
        stats = database.get_db_stats()
        logger.success(f"[DATABASE] Database ready: {stats.get('total_hospitals', 0)} hospitals, "
                      f"{stats.get('states', 0)} states, {stats.get('districts', 0)} districts, "
                      f"{stats.get('pincodes', 0)} pincodes")
    except Exception as e:
        logger.error(f"[DATABASE] Database initialization failed: {e}")


# ──────────────────────────────────────────────
# Global Exception Handler — NEVER leave user hanging
# ──────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"CRITICAL FAILURE: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "plan": FAILSAFE_PLAN,
            "hospitals": [],
            "weather": None,
            "metadata": {"error": str(exc)}
        }
    )


# ──────────────────────────────────────────────
# GET /api/health
# ──────────────────────────────────────────────
@app.get("/api/health")
async def health():
    """System health check with DB stats and API key status."""
    stats = database.get_db_stats()
    return {
        "status": "healthy",
        "db_stats": stats,
        "api_keys": {
            "opencage": bool(OPENCAGE_API_KEY),
            "geoapify": bool(GEOAPIFY_API_KEY),
            "weather": bool(WEATHER_API_KEY),
            "deepseek": bool(DEEPSEEK_API_KEY),
            "openrouter": bool(OPENAI_API_KEY),
            "ipinfo": bool(IPINFO_API_KEY)
        }
    }


# ──────────────────────────────────────────────
# POST /api/emergency/guidance — THE CORE ENDPOINT
# ──────────────────────────────────────────────
@app.post("/api/emergency/guidance")
async def get_guidance(req: EmergencyRequest):
    """Full emergency triage: GPS → nearest hospitals → AI racing + weather context."""
    logger.info(f"🚨 Emergency request: ({req.lat}, {req.lon}) signals={req.signals}")
    start = time.time()

    try:
        # 1. Find nearest hospitals from the 10k+ database
        hospitals = database.get_nearest_hospitals(req.lat, req.lon)
        logger.info(f"Found {len(hospitals)} hospitals nearby")

        # 2. Get weather context (non-blocking, best-effort)
        weather_data = None
        weather_summary = ""
        try:
            weather_data = await get_weather(req.lat, req.lon)
            if weather_data.get("status") == "ok":
                weather_summary = weather_data.get("summary", "")
        except Exception as e:
            logger.warning(f"Weather fetch failed (non-critical): {e}")

        # 3. AI Racing: Run rule engine + LLM in parallel
        plan = await triage_racing(
            signals=req.signals,
            hospitals=hospitals,
            vehicle_available=req.vehicle_available,
            weather_context=weather_summary
        )

        duration_ms = round((time.time() - start) * 1000, 2)
        logger.success(f"✅ Guidance generated in {duration_ms}ms | Severity: {plan['severity']} | Tier: {plan['tier_used']}")

        return {
            "status": "ok",
            "plan": plan,
            "hospitals": hospitals[:10],
            "weather": weather_data if weather_data and weather_data.get("status") == "ok" else None,
            "metadata": {
                "time_ms": duration_ms,
                "hospitals_found": len(hospitals),
                "engine_version": "omniscient-v5.0",
                "ai_used": plan.get("tier_used", ""),
            }
        }

    except Exception as e:
        logger.exception("Failed to generate guidance")
        duration_ms = round((time.time() - start) * 1000, 2)
        return JSONResponse(
            status_code=200,
            content={
                "status": "fallback",
                "plan": FAILSAFE_PLAN,
                "hospitals": [],
                "weather": None,
                "metadata": {"error": str(e), "time_ms": duration_ms}
            }
        )


# ──────────────────────────────────────────────
# POST /api/search — Hospital text search
# ──────────────────────────────────────────────
@app.post("/api/search")
async def search_hospitals(req: SearchRequest):
    """Search hospitals by pincode, district, town, name, or state.

    Examples: "744101", "South Andaman", "Apollo", "Kerala"
    """
    logger.info(f"🔍 Search: '{req.query}'")

    results = database.search_hospitals(req.query)

    # If lat/lon provided, calculate distances
    if req.lat is not None and req.lon is not None:
        for h in results:
            if h.get("lat") and h.get("lon"):
                h["distance_km"] = round(
                    database.haversine(req.lat, req.lon, h["lat"], h["lon"]), 2
                )
        results.sort(key=lambda x: x.get("distance_km", 9999))

    logger.info(f"Found {len(results)} results for '{req.query}'")

    return {
        "status": "ok",
        "count": len(results),
        "hospitals": results
    }


# ──────────────────────────────────────────────
# POST /api/geocode — Geocode address/pincode
# ──────────────────────────────────────────────
@app.post("/api/geocode")
async def geocode_endpoint(req: GeocodeRequest):
    """Geocode an address, pincode, or place name to lat/lon.

    Uses OpenCage → Geoapify fallback chain.
    """
    logger.info(f"📍 Geocode: '{req.query}'")
    result = await geocode(req.query)
    return result


# ──────────────────────────────────────────────
# GET /api/weather — Weather for location
# ──────────────────────────────────────────────
@app.get("/api/weather")
async def weather_endpoint(lat: float, lon: float):
    """Get current weather conditions for emergency context."""
    logger.info(f"🌤️ Weather: ({lat}, {lon})")
    result = await get_weather(lat, lon)
    return result


# ──────────────────────────────────────────────
# Entrypoint
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    logger.info("[SYSTEM] Starting RoadSoS Omniscient Engine on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
