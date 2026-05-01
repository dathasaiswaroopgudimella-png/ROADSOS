"""
RoadSoS — Omniscient Architect Protocol v5.0
Deterministic Decision Engine: Rule-based triage in <50ms.

This is the GUARANTEED fallback that never fails. The AI layer enhances it,
but this engine alone can save lives.
"""

from backend.config import CRITICAL_DISTANCE_KM


# Signal severity classification
CRITICAL_SIGNALS = {
    "bleeding", "unconscious", "breathing", "chest_pain", "head_injury",
    "seizure", "choking", "drowning", "cardiac_arrest", "severe_burn",
    "poisoning", "stroke", "anaphylaxis"
}

HIGH_SIGNALS = {
    "fracture", "burns", "high_fever", "abdominal_pain", "fall",
    "animal_bite", "electric_shock", "eye_injury", "allergic_reaction"
}

MEDIUM_SIGNALS = {
    "minor_cut", "sprain", "nausea", "dizziness", "mild_pain",
    "rash", "cough", "headache"
}


def make_decision(signals: list[str], hospitals: list[dict], vehicle_available: bool) -> dict:
    """Deterministic rule-based triage. Always returns in <50ms.

    Logic:
    1. Classify signal severity
    2. Factor in hospital proximity
    3. Consider vehicle availability
    4. Generate action plan
    """
    sig_set = {s.lower().strip() for s in signals if s}

    # Classify severity
    has_critical = any(s in CRITICAL_SIGNALS for s in sig_set)
    has_high = any(s in HIGH_SIGNALS for s in sig_set)
    num_signals = len(sig_set)

    # Get nearest hospital info
    nearest = hospitals[0] if hospitals else None
    nearest_dist = nearest["distance_km"] if nearest else 999
    nearest_name = nearest.get("hospital_name", "nearest hospital") if nearest else "emergency services"
    nearest_phone = _get_best_phone(nearest) if nearest else "102"
    nearest_beds = nearest.get("total_beds", 0) if nearest else 0

    # Build action plan based on severity
    if has_critical or (num_signals >= 3):
        # CRITICAL: Life-threatening
        if nearest_dist <= CRITICAL_DISTANCE_KM and vehicle_available:
            primary = f"Drive IMMEDIATELY to {nearest_name} ({nearest_dist}km away)"
            secondary = f"Call ahead: {nearest_phone}. If condition worsens, stop and call 102."
        else:
            primary = "Call ambulance (102) NOW — do not wait"
            secondary = f"Nearest: {nearest_name} ({nearest_dist}km). Ambulance: {nearest_phone}"

        return {
            "primary_action": primary,
            "secondary_action": secondary,
            "reason": f"Critical signals detected: {', '.join(sig_set & CRITICAL_SIGNALS) or ', '.join(sig_set)}. "
                      f"{'Multiple symptoms indicate compound emergency. ' if num_signals >= 3 else ''}"
                      f"Nearest facility has {nearest_beds} beds at {nearest_dist}km.",
            "severity": "critical",
            "confidence": 0.95,
            "tier_used": "deterministic_critical"
        }

    elif has_high:
        # HIGH: Urgent but not immediately life-threatening
        if nearest_dist <= 5 and vehicle_available:
            primary = f"Proceed to {nearest_name} emergency room immediately"
            secondary = f"Call {nearest_phone} while en route. Distance: {nearest_dist}km"
        else:
            primary = f"Call {nearest_phone} for ambulance dispatch"
            secondary = f"{nearest_name} is {nearest_dist}km away with {nearest_beds} beds"

        return {
            "primary_action": primary,
            "secondary_action": secondary,
            "reason": f"Urgent signals: {', '.join(sig_set & HIGH_SIGNALS)}. "
                      f"Professional medical attention required promptly.",
            "severity": "high",
            "confidence": 0.88,
            "tier_used": "deterministic_high"
        }

    elif sig_set:
        # MEDIUM: Non-emergency but needs attention
        primary = f"Visit {nearest_name} for medical evaluation"
        secondary = f"Contact: {nearest_phone}. Distance: {nearest_dist}km"

        return {
            "primary_action": primary,
            "secondary_action": secondary,
            "reason": f"Moderate symptoms reported: {', '.join(sig_set)}. "
                      f"Medical evaluation recommended to prevent escalation.",
            "severity": "medium",
            "confidence": 0.80,
            "tier_used": "deterministic_medium"
        }

    else:
        # No signals — provide general guidance
        return {
            "primary_action": f"Contact {nearest_name} for medical consultation",
            "secondary_action": f"Phone: {nearest_phone}. Emergency: 102/108",
            "reason": "No specific emergency signals detected. Providing nearest facility information.",
            "severity": "low",
            "confidence": 0.70,
            "tier_used": "deterministic_low"
        }


def _get_best_phone(hospital: dict) -> str:
    """Extract the best contact number from hospital record."""
    for field in ["emergency_num", "ambulance_phone", "telephone", "mobile_number", "helpline", "tollfree"]:
        val = hospital.get(field, "")
        if val and val.strip():
            return val.strip()
    return "102"
