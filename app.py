"""
RoadSoS -- Fail-Safe Emergency Guidance System
Streamlit Application (Phase 7)

Entry point: streamlit run app.py

State-safe: uses st.session_state.setdefault for ALL keys.
Handles reload gracefully. Never crashes.
"""

import copy
import sys
import os
import time
from typing import Any

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from core.config import (
    CEIL_MAP,
    CRITICAL_DISTANCE,
    FAILSAFE_RESPONSE,
    MAX_RADIUS,
    SEVERITY_LEVELS,
)
from core.logger import get_logger
from core.validator import validate_coordinates
from core.edge_handler import handle_error
from core.decision_engine import make_decision
from data.offline_cache import get_cached_services
from services.geocoder import get_coordinates
from services.fetcher import get_services
from services.ceil import get_ceil_signal

logger = get_logger(__name__)

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="RoadSoS -- Emergency Guidance",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# SESSION STATE INIT (Phase 7 rule: always setdefault)
# ──────────────────────────────────────────────
st.session_state.setdefault("data", {})
st.session_state.setdefault("location_input", "")
st.session_state.setdefault("lat", None)
st.session_state.setdefault("lon", None)
st.session_state.setdefault("severity", "low")
st.session_state.setdefault("services", [])
st.session_state.setdefault("decision", None)
st.session_state.setdefault("geocode_result", None)
st.session_state.setdefault("ceil_signal", "none")
st.session_state.setdefault("last_error", None)

# ──────────────────────────────────────────────
# CUSTOM CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

    /* Global */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* Hero banner */
    .hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .hero h1 {
        color: #e94560;
        font-size: 2.4rem;
        font-weight: 900;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hero p {
        color: #a8b2d1;
        font-size: 1.05rem;
        margin: 0.5rem 0 0 0;
    }

    /* Action cards */
    .action-card {
        border-radius: 14px;
        padding: 1.8rem;
        margin: 0.6rem 0;
        border-left: 5px solid;
        backdrop-filter: blur(6px);
    }
    .action-critical {
        background: linear-gradient(135deg, rgba(233,69,96,0.15), rgba(233,69,96,0.05));
        border-left-color: #e94560;
    }
    .action-medium {
        background: linear-gradient(135deg, rgba(255,183,77,0.15), rgba(255,183,77,0.05));
        border-left-color: #ffb74d;
    }
    .action-low {
        background: linear-gradient(135deg, rgba(102,187,106,0.15), rgba(102,187,106,0.05));
        border-left-color: #66bb6a;
    }
    .action-card h3 {
        margin: 0 0 0.3rem 0;
        font-weight: 700;
        font-size: 1.25rem;
    }
    .action-card p {
        margin: 0;
        font-size: 1rem;
        opacity: 0.85;
    }

    /* Status badges */
    .badge {
        display: inline-block;
        padding: 0.3rem 0.9rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.3px;
    }
    .badge-ok { background: #1b5e20; color: #a5d6a7; }
    .badge-fallback { background: #e65100; color: #ffcc80; }
    .badge-error { background: #b71c1c; color: #ef9a9a; }

    /* Service table */
    .svc-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border-radius: 12px;
        overflow: hidden;
        margin: 1rem 0;
    }
    .svc-table th {
        background: rgba(233,69,96,0.2);
        padding: 0.8rem 1rem;
        text-align: left;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .svc-table td {
        padding: 0.7rem 1rem;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        font-size: 0.9rem;
    }

    /* CEIL indicator */
    .ceil-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.4rem 1rem;
        border-radius: 8px;
        font-weight: 600;
    }
    .ceil-none   { background: rgba(102,187,106,0.15); color: #66bb6a; }
    .ceil-low    { background: rgba(255,238,88,0.15); color: #ffee58; }
    .ceil-medium { background: rgba(255,183,77,0.15); color: #ffb74d; }
    .ceil-high   { background: rgba(233,69,96,0.15); color: #e94560; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e, #16213e);
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────────
def _badge(status: str) -> str:
    cls = {"ok": "badge-ok", "fallback": "badge-fallback", "error": "badge-error"}.get(status, "badge-error")
    return f'<span class="badge {cls}">{status.upper()}</span>'


def _action_card(tier: str, primary: str, secondary: str) -> str:
    cls = {"critical": "action-critical", "medium": "action-medium", "low": "action-low"}.get(tier, "action-critical")
    return f"""
    <div class="action-card {cls}">
        <h3>&#9888; {primary}</h3>
        <p>{secondary}</p>
    </div>
    """


# ──────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>&#128680; RoadSoS</h1>
    <p>Fail-Safe Emergency Guidance System &mdash; always returns a safe response</p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Configuration")

    severity = st.selectbox(
        "Severity Level",
        options=SEVERITY_LEVELS,
        index=SEVERITY_LEVELS.index(st.session_state.get("severity", "low")),
        key="severity_select",
        help="Perceived severity of the emergency",
    )
    st.session_state["severity"] = severity

    st.markdown("---")
    st.markdown("### CEIL Status")
    ceil_sig = get_ceil_signal(logger)
    st.session_state["ceil_signal"] = ceil_sig
    ceil_cls = f"ceil-{ceil_sig}"
    st.markdown(f'<div class="ceil-indicator {ceil_cls}">CEIL: {ceil_sig.upper()}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### System Info")
    st.caption(f"Max Radius: {MAX_RADIUS} km")
    st.caption(f"Critical Distance: {CRITICAL_DISTANCE} km")
    st.caption(f"CEIL Map: {CEIL_MAP}")

# ──────────────────────────────────────────────
# MAIN INPUT
# ──────────────────────────────────────────────
col1, col2 = st.columns([3, 1])

with col1:
    location = st.text_input(
        "Enter location or address",
        value=st.session_state.get("location_input", ""),
        placeholder="e.g. Connaught Place, New Delhi",
        key="loc_input",
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    search_clicked = st.button("Get Guidance", type="primary", use_container_width=True, key="search_btn")

# ── Manual coordinates toggle ──
with st.expander("Or enter coordinates manually"):
    mc1, mc2 = st.columns(2)
    with mc1:
        manual_lat = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=28.6139, step=0.0001, key="manual_lat")
    with mc2:
        manual_lon = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=77.2090, step=0.0001, key="manual_lon")
    use_manual = st.button("Use these coordinates", key="use_manual_btn")

# ──────────────────────────────────────────────
# PROCESSING
# ──────────────────────────────────────────────
def _process(lat: float, lon: float) -> None:
    """Run the full pipeline and update session state."""
    start = time.time()
    logger.info("PIPELINE START lat=%.4f lon=%.4f severity=%s", lat, lon, st.session_state["severity"])

    try:
        # Validate
        lat, lon = validate_coordinates(lat, lon)
        st.session_state["lat"] = lat
        st.session_state["lon"] = lon

        # Fetch services
        svc_result = get_services(lat, lon, logger)
        services_list = svc_result.get("data", []) if isinstance(svc_result.get("data"), list) else []

        # If API returned nothing, try cache
        if not services_list:
            cache_result = get_cached_services(lat, lon, float(MAX_RADIUS), logger)
            if cache_result.get("status") == "ok" and isinstance(cache_result.get("data"), list):
                services_list = cache_result["data"]

        st.session_state["services"] = services_list

        # Get nearest distance
        nearest_dist = float(MAX_RADIUS)
        for svc in services_list:
            d = svc.get("distance_km", MAX_RADIUS)
            if d < nearest_dist:
                nearest_dist = d

        # Decision
        decision = make_decision(
            severity=st.session_state["severity"],
            distance=nearest_dist,
            services=services_list,
            ceil_signal=st.session_state["ceil_signal"],
            logger_=logger,
        )
        st.session_state["decision"] = decision
        st.session_state["last_error"] = None

    except ValueError as ve:
        logger.error("Validation error: %s", ve)
        st.session_state["decision"] = handle_error("invalid_input")
        st.session_state["last_error"] = str(ve)
    except Exception as exc:
        logger.error("PIPELINE FAILURE: %s", exc)
        st.session_state["decision"] = copy.deepcopy(FAILSAFE_RESPONSE)
        st.session_state["last_error"] = str(exc)
    finally:
        logger.info("PIPELINE END time_ms=%.2f", (time.time() - start) * 1000)


# ── Trigger processing ──
if search_clicked and location:
    with st.spinner("Geocoding location..."):
        geo = get_coordinates(location, logger)
        st.session_state["geocode_result"] = geo
        if geo.get("status") == "ok" and geo.get("data"):
            _process(geo["data"]["lat"], geo["data"]["lon"])
        else:
            st.session_state["decision"] = handle_error("api_failure")
            st.session_state["last_error"] = "Could not geocode location"

elif use_manual:
    with st.spinner("Fetching services..."):
        _process(manual_lat, manual_lon)

# ──────────────────────────────────────────────
# RESULTS DISPLAY
# ──────────────────────────────────────────────
decision = st.session_state.get("decision")

if decision:
    st.markdown("---")

    # Status badge
    status = decision.get("status", "error")
    st.markdown(f"### Response Status: {_badge(status)}", unsafe_allow_html=True)

    # Error message
    if st.session_state.get("last_error"):
        st.warning(f"Note: {st.session_state['last_error']}")

    # Action cards
    data = decision.get("data", {})
    primary = data.get("primary_action", FAILSAFE_RESPONSE["data"]["primary_action"])
    secondary = data.get("secondary_action", FAILSAFE_RESPONSE["data"]["secondary_action"])
    tier = data.get("tier_used", "critical")

    st.markdown(_action_card(tier, primary, secondary), unsafe_allow_html=True)

    st.markdown(f"**Tier:** `{tier}` &nbsp; | &nbsp; **Message:** {decision.get('message', '')}")

    # Services table
    services = st.session_state.get("services", [])
    if services:
        st.markdown("### Nearby Services")
        rows = ""
        for svc in services:
            rows += f"""<tr>
                <td>{svc.get('name', 'Unknown')}</td>
                <td>{svc.get('type', 'N/A')}</td>
                <td>{svc.get('distance_km', 'N/A')} km</td>
                <td>{svc.get('phone', svc.get('address', 'N/A'))}</td>
            </tr>"""
        st.markdown(f"""
        <table class="svc-table">
            <tr><th>Name</th><th>Type</th><th>Distance</th><th>Contact / Address</th></tr>
            {rows}
        </table>
        """, unsafe_allow_html=True)

    # Coordinates display
    lat_v = st.session_state.get("lat")
    lon_v = st.session_state.get("lon")
    if lat_v is not None and lon_v is not None:
        st.markdown(f"**Coordinates:** `{lat_v:.4f}, {lon_v:.4f}`")

else:
    # Landing state
    st.info("Enter a location above and click **Get Guidance** to receive emergency recommendations.")
    st.markdown("""
    > **How it works:**
    > 1. Enter a location or use manual coordinates
    > 2. Select the severity level in the sidebar
    > 3. The system finds nearby services and delivers imperative guidance
    > 4. If anything fails, you always get a safe fallback response
    """)


# ──────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────
st.markdown("---")
st.caption("RoadSoS v1.0 -- Fail-safe by design. System NEVER crashes, ALWAYS returns a safe response.")
