// RoadSoS — Omniscient Architect Protocol v5.0
// Type definitions matching the full hospital CSV schema + API responses

export interface Hospital {
  sr_no: number;
  lat: number | null;
  lon: number | null;
  location: string;
  hospital_name: string;
  hospital_category: string;
  hospital_care_type: string;
  discipline: string;
  address: string;
  state: string;
  district: string;
  subdistrict: string;
  pincode: string;
  telephone: string;
  mobile_number: string;
  emergency_num: string;
  ambulance_phone: string;
  bloodbank_phone: string;
  tollfree: string;
  helpline: string;
  email: string;
  website: string;
  specialties: string;
  facilities: string;
  accreditation: string;
  town: string;
  village: string;
  established_year: string;
  num_doctors: number;
  num_consultants: number;
  total_beds: number;
  private_wards: number;
  beds_eco_weaker: number;
  emergency_services: string;
  tariff_range: string;
  distance_km: number | null;
}

export interface AIInsight {
  recommended_hospital: string | null;
  estimated_response_time: string | null;
  first_aid_tips: string[];
  source: string;
}

export interface ActionPlan {
  primary_action: string;
  secondary_action: string;
  reason: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  tier_used: string;
  ai_insight: AIInsight | null;
  weather_context: string | null;
}

export interface WeatherInfo {
  status: string;
  temperature_c: number | null;
  condition: string | null;
  condition_icon: string | null;
  humidity: number | null;
  wind_kph: number | null;
  visibility_km: number | null;
  precipitation_mm: number | null;
  feels_like_c: number | null;
  impact: string | null;
  warnings: string[];
  summary: string | null;
}

export interface EmergencyResponse {
  status: string;
  plan: ActionPlan;
  hospitals: Hospital[];
  weather: WeatherInfo | null;
  metadata: Record<string, any>;
}

export interface GeocodeResult {
  status: string;
  lat: number | null;
  lon: number | null;
  formatted: string | null;
  state: string | null;
  district: string | null;
  source: string | null;
  message: string | null;
}

export interface SearchResult {
  status: string;
  count: number;
  hospitals: Hospital[];
}

export interface HealthStatus {
  status: string;
  db_stats: {
    total_hospitals: number;
    states: number;
    districts: number;
    pincodes: number;
    kdtree_nodes: number;
  };
  api_keys: Record<string, boolean>;
}

export type EmergencyState = 'IDLE' | 'SEARCHING' | 'LOCATING' | 'TRIAGING' | 'DECIDED';

export type LocationSource = 'gps' | 'search' | 'ip' | 'manual' | null;
