"""
RoadSoS — Omniscient Architect Protocol v5.0
Pydantic Models: Rich, validated data structures matching the full CSV schema.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class EmergencyRequest(BaseModel):
    """Request containing location and emergency signals."""
    lat: float = Field(..., ge=-90, le=90, description="WGS84 Latitude")
    lon: float = Field(..., ge=-180, le=180, description="WGS84 Longitude")
    signals: List[str] = Field(default_factory=list, description="Emergency symptom signals")
    vehicle_available: bool = Field(default=False, description="Is private vehicle available?")


class SearchRequest(BaseModel):
    """Text search request for hospitals."""
    query: str = Field(..., min_length=1, description="Pincode, district, town, or hospital name")
    lat: Optional[float] = Field(None, ge=-90, le=90, description="Optional lat for distance calculation")
    lon: Optional[float] = Field(None, ge=-180, le=180, description="Optional lon for distance calculation")


class GeocodeRequest(BaseModel):
    """Geocoding request."""
    query: str = Field(..., min_length=1, description="Address, pincode, or place name to geocode")


class HospitalResponse(BaseModel):
    """Full hospital record with all metadata from the CSV dataset."""
    sr_no: int
    lat: Optional[float] = None
    lon: Optional[float] = None
    location: str = ""
    hospital_name: str = ""
    hospital_category: str = ""
    hospital_care_type: str = ""
    discipline: str = ""
    address: str = ""
    state: str = ""
    district: str = ""
    subdistrict: str = ""
    pincode: str = ""
    telephone: str = ""
    mobile_number: str = ""
    emergency_num: str = ""
    ambulance_phone: str = ""
    bloodbank_phone: str = ""
    tollfree: str = ""
    helpline: str = ""
    email: str = ""
    website: str = ""
    specialties: str = ""
    facilities: str = ""
    accreditation: str = ""
    town: str = ""
    village: str = ""
    established_year: str = ""
    num_doctors: int = 0
    num_consultants: int = 0
    total_beds: int = 0
    private_wards: int = 0
    beds_eco_weaker: int = 0
    emergency_services: str = ""
    tariff_range: str = ""
    distance_km: Optional[float] = None


class AIInsight(BaseModel):
    """AI-generated triage insight."""
    recommended_hospital: Optional[str] = None
    estimated_response_time: Optional[str] = None
    first_aid_tips: List[str] = Field(default_factory=list)
    source: str = ""


class ActionPlan(BaseModel):
    """Triage action plan from the Neural-Deterministic Racing engine."""
    primary_action: str
    secondary_action: str
    reason: str
    severity: str = Field(..., pattern="^(critical|high|medium|low)$")
    confidence: float = Field(..., ge=0, le=1)
    tier_used: str
    ai_insight: Optional[AIInsight] = None
    weather_context: Optional[str] = None


class WeatherInfo(BaseModel):
    """Weather conditions at the emergency location."""
    status: str
    temperature_c: Optional[float] = None
    condition: Optional[str] = None
    condition_icon: Optional[str] = None
    humidity: Optional[int] = None
    wind_kph: Optional[float] = None
    visibility_km: Optional[float] = None
    precipitation_mm: Optional[float] = None
    feels_like_c: Optional[float] = None
    impact: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    summary: Optional[str] = None


class EmergencyResponse(BaseModel):
    """Complete emergency guidance response."""
    status: str = Field(..., pattern="^(ok|fallback|error)$")
    plan: ActionPlan
    hospitals: List[HospitalResponse]
    weather: Optional[WeatherInfo] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GeocodeResponse(BaseModel):
    """Geocoding response."""
    status: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    formatted: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    source: Optional[str] = None
    message: Optional[str] = None


class SearchResponse(BaseModel):
    """Hospital search response."""
    status: str
    count: int
    hospitals: List[HospitalResponse]


class HealthResponse(BaseModel):
    """System health check."""
    status: str
    db_stats: Dict[str, Any]
    api_keys: Dict[str, bool]
