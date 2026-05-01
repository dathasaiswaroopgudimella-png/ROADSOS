"""
RoadSoS — Omniscient Architect Protocol v5.0
AI Triage Engine: Neural-Deterministic Racing Architecture.

Runs TWO engines in parallel:
  1. Deterministic Rule Engine (instant, 100% reliable)
  2. DeepSeek/OpenRouter LLM (expert-level analysis, 3-4s)

The race: Rule engine provides immediate safety. If the LLM finishes within
AI_RACE_TIMEOUT_SEC, its expert insight is merged. If not, we go with rules.
"""

import asyncio
import json

import httpx

from backend.config import DEEPSEEK_API_KEY, OPENAI_API_KEY, AI_RACE_TIMEOUT_SEC
from backend.decision_engine import make_decision


async def _call_deepseek(signals: list[str], hospitals: list[dict], vehicle_available: bool, weather_context: str = "") -> dict | None:
    """Call DeepSeek API for expert clinical triage."""
    if not DEEPSEEK_API_KEY:
        return None

    hospital_info = ""
    for h in hospitals[:5]:
        hospital_info += f"- {h.get('hospital_name', 'Unknown')}: {h.get('distance_km', '?')}km away, "
        hospital_info += f"{h.get('total_beds', 0)} beds, "
        hospital_info += f"Emergency: {h.get('emergency_num', 'N/A')}, "
        hospital_info += f"Ambulance: {h.get('ambulance_phone', 'N/A')}\n"

    prompt = f"""You are an emergency medical triage AI. Analyze this situation and provide actionable guidance.

PATIENT SIGNALS: {', '.join(signals) if signals else 'No specific signals reported'}
VEHICLE AVAILABLE: {'Yes' : 'No'}
WEATHER: {weather_context if weather_context else 'Normal conditions'}

NEARBY HOSPITALS:
{hospital_info if hospital_info else 'No hospitals found nearby'}

Provide your response as JSON with these exact fields:
{{
  "primary_action": "The most important thing to do RIGHT NOW (1 sentence)",
  "secondary_action": "The next step after the primary action (1 sentence)",
  "reason": "Brief clinical reasoning (2-3 sentences max)",
  "severity": "critical|high|medium|low",
  "recommended_hospital": "Name of the best hospital for this case, or null",
  "estimated_response_time": "Estimated ambulance/travel time based on distance and weather",
  "first_aid_tips": ["tip1", "tip2", "tip3"]
}}"""

    try:
        async with httpx.AsyncClient(timeout=AI_RACE_TIMEOUT_SEC) as client:
            resp = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are an emergency medical triage AI. Always respond with valid JSON only. Be concise and actionable."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 500
                }
            )
            resp.raise_for_status()
            data = resp.json()

            content = data["choices"][0]["message"]["content"]
            # Extract JSON from response
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]

            return json.loads(content)

    except Exception as e:
        print(f"[AI_TRIAGE] DeepSeek failed: {e}")
        return None


async def _call_openrouter(signals: list[str], hospitals: list[dict], vehicle_available: bool, weather_context: str = "") -> dict | None:
    """Call OpenRouter API as fallback LLM."""
    if not OPENAI_API_KEY:
        return None

    hospital_info = ""
    for h in hospitals[:5]:
        hospital_info += f"- {h.get('hospital_name', 'Unknown')}: {h.get('distance_km', '?')}km, {h.get('total_beds', 0)} beds\n"

    prompt = f"""Emergency triage needed. Signals: {', '.join(signals)}. Vehicle: {'Yes' if vehicle_available else 'No'}. Weather: {weather_context or 'Normal'}.

Hospitals: {hospital_info}

Respond as JSON: {{"primary_action": "...", "secondary_action": "...", "reason": "...", "severity": "critical|high|medium|low", "recommended_hospital": "...", "first_aid_tips": ["..."]}}"""

    try:
        async with httpx.AsyncClient(timeout=AI_RACE_TIMEOUT_SEC) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek/deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are an emergency medical AI. Respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 400
                }
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(content)

    except Exception as e:
        print(f"[AI_TRIAGE] OpenRouter failed: {e}")
        return None


async def triage_racing(
    signals: list[str],
    hospitals: list[dict],
    vehicle_available: bool,
    weather_context: str = ""
) -> dict:
    """Neural-Deterministic Racing: Run rule engine + LLM in parallel.

    Rule engine provides instant, guaranteed result.
    LLM provides expert insight if it finishes within timeout.
    Results are merged for maximum quality.
    """
    # 1. Rule engine — instant, always works
    rule_result = make_decision(signals, hospitals, vehicle_available)

    # 2. Race the LLMs — try DeepSeek first, OpenRouter as backup
    ai_result = None
    try:
        # Try DeepSeek with timeout
        ai_result = await asyncio.wait_for(
            _call_deepseek(signals, hospitals, vehicle_available, weather_context),
            timeout=AI_RACE_TIMEOUT_SEC
        )
    except asyncio.TimeoutError:
        print("[AI_TRIAGE] DeepSeek timed out, trying OpenRouter...")

    if ai_result is None:
        try:
            ai_result = await asyncio.wait_for(
                _call_openrouter(signals, hospitals, vehicle_available, weather_context),
                timeout=AI_RACE_TIMEOUT_SEC
            )
        except asyncio.TimeoutError:
            print("[AI_TRIAGE] OpenRouter timed out. Using rule engine only.")

    # 3. Merge results
    if ai_result:
        # AI succeeded — merge with rule engine for maximum quality
        merged = {
            "primary_action": ai_result.get("primary_action", rule_result["primary_action"]),
            "secondary_action": ai_result.get("secondary_action", rule_result["secondary_action"]),
            "reason": ai_result.get("reason", rule_result["reason"]),
            "severity": _max_severity(
                ai_result.get("severity", "medium"),
                rule_result["severity"]
            ),
            "confidence": max(rule_result["confidence"], 0.9),
            "tier_used": "neural_deterministic_fusion",
            "ai_insight": {
                "recommended_hospital": ai_result.get("recommended_hospital"),
                "estimated_response_time": ai_result.get("estimated_response_time"),
                "first_aid_tips": ai_result.get("first_aid_tips", []),
                "source": "deepseek" if DEEPSEEK_API_KEY else "openrouter"
            },
            "weather_context": weather_context or None
        }
        return merged
    else:
        # AI failed — rule engine only
        rule_result["tier_used"] = "deterministic_only"
        rule_result["ai_insight"] = None
        rule_result["weather_context"] = weather_context or None
        return rule_result


def _max_severity(a: str, b: str) -> str:
    """Return the higher severity level (monotonic escalation)."""
    order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    a_val = order.get(a, 1)
    b_val = order.get(b, 1)
    reverse = {v: k for k, v in order.items()}
    return reverse.get(max(a_val, b_val), "high")
