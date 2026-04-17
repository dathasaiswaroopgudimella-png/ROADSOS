# RoadSoS — Fail-Safe Emergency Guidance System 🚨

RoadSoS is a safety-critical emergency guidance system designed to **NEVER crash** and **ALWAYS return a safe response**. It provides human-readable imperative guidance based on severity, distance, and community impact signals (CEIL).

## 🔒 Global Non-Negotiable Rules
1. **Always Safe**: Returns a mandatory fallback response if any part of the system fails.
2. **Strict Logging**: Every function logs entry, exit, errors, and execution time.
3. **Timed API Calls**: All external service calls are wrapped in hard timeouts.
4. **Strict Response Format**: All modules communicate using a unified status/data/message JSON structure.

## 📁 System Structure
- `core/`: Config, Logger, Validator, Timeout, Edge Handler, Decision Engine.
- `services/`: Geocoder (OpenCage), Fetcher (Geoapify), CEIL (Static signals).
- `data/`: Offline cache and pre-seeded demo data for Delhi area.
- `tests/`: 17 comprehensive assert-based test cases.
- `app.py`: Streamlit-powered premium dark UI with state-safe session management.

## 🛠️ Performance & Resilience
- **Query Time**: Offline cache queries consistently < 100ms.
- **Fail-Safe**: If API or network fails, the system immediately switches to offline demo data or a terminal "Call ambulance now" fallback.
- **CEIL Integration**: Severity is dynamically adjusted based on community emergency impact levels.

## 🚀 Getting Started

### Prerequisites
```bash
pip install streamlit requests
```

### Running the App
```bash
streamlit run app.py
```

### Running Tests
```bash
python -m tests.test_cases
```

---
*RoadSoS v1.0 — Fail-safe by design.*
