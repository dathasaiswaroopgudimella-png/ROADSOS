"""
RoadSoS — Omniscient Architect Protocol v5.0
Unified Configuration: ALL API keys, ALL thresholds, ZERO hardcoding elsewhere.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend directory
_BACKEND_DIR = Path(__file__).parent
load_dotenv(_BACKEND_DIR / ".env")

# ──────────────────────────────────────────────
# API KEYS — Every single one the user provided
# ──────────────────────────────────────────────
OPENCAGE_API_KEY: str = os.getenv("OPENCAGE_API_KEY", "")
GEOAPIFY_API_KEY: str = os.getenv("GEOAPIFY_API_KEY", "")
WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")  # OpenRouter
IPINFO_API_KEY: str = os.getenv("IPINFO_API_KEY", "")

# ──────────────────────────────────────────────
# PATHS
# ──────────────────────────────────────────────
PROJECT_ROOT = _BACKEND_DIR.parent
CSV_PATH = PROJECT_ROOT / "hospital_directory.csv"
DB_PATH = _BACKEND_DIR / "data" / "hospitals.db"

# ──────────────────────────────────────────────
# SEARCH & DISTANCE THRESHOLDS
# ──────────────────────────────────────────────
MAX_RADIUS_KM: float = 25.0          # Search radius for nearby hospitals
CRITICAL_DISTANCE_KM: float = 3.0    # Triggers elevated urgency
MAX_RESULTS: int = 10                # Max hospitals returned per query
FTS_RESULTS: int = 20                # Max FTS search results

# ──────────────────────────────────────────────
# TIMING CONSTRAINTS
# ──────────────────────────────────────────────
API_TIMEOUT_SEC: float = 3.0         # Hard cap on external API calls
AI_RACE_TIMEOUT_SEC: float = 4.0     # Max time to wait for LLM before rule-engine fallback

# ──────────────────────────────────────────────
# FAIL-SAFE DEFAULT RESPONSE
# ──────────────────────────────────────────────
FAILSAFE_PLAN = {
    "primary_action": "Call national ambulance (102) immediately",
    "secondary_action": "Stay calm. Share your GPS coordinates with the operator.",
    "reason": "System fallback activated — prioritizing your safety above all else.",
    "severity": "critical",
    "confidence": 1.0,
    "tier_used": "failsafe",
    "ai_insight": None,
    "weather_context": None
}
