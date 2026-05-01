// RoadSoS — Omniscient Architect Protocol v5.0
// API Service: Full integration with ALL backend endpoints

import { EmergencyResponse, SearchResult, GeocodeResult, HealthStatus } from '../types';

const BASE_URL = 'http://localhost:8000/api';
const TIMEOUT_MS = 8000;

async function fetchWithTimeout(url: string, options: RequestInit = {}, timeout = TIMEOUT_MS): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

export class ApiService {
  /**
   * POST /api/emergency/guidance
   * Full emergency triage: GPS → hospitals → AI racing + weather
   */
  static async getGuidance(
    lat: number,
    lon: number,
    signals: string[],
    vehicle_available: boolean
  ): Promise<EmergencyResponse> {
    const response = await fetchWithTimeout(`${BASE_URL}/emergency/guidance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lat, lon, signals, vehicle_available }),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return await response.json();
  }

  /**
   * POST /api/search
   * Search hospitals by pincode, district, town, name
   */
  static async searchHospitals(
    query: string,
    lat?: number | null,
    lon?: number | null
  ): Promise<SearchResult> {
    const body: any = { query };
    if (lat != null && lon != null) {
      body.lat = lat;
      body.lon = lon;
    }

    const response = await fetchWithTimeout(`${BASE_URL}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Search Error: ${response.status}`);
    }

    return await response.json();
  }

  /**
   * POST /api/geocode
   * Geocode address/pincode to lat/lon (OpenCage + Geoapify)
   */
  static async geocode(query: string): Promise<GeocodeResult> {
    const response = await fetchWithTimeout(`${BASE_URL}/geocode`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error(`Geocode Error: ${response.status}`);
    }

    return await response.json();
  }

  /**
   * GET /api/weather
   */
  static async getWeather(lat: number, lon: number): Promise<any> {
    const response = await fetchWithTimeout(
      `${BASE_URL}/weather?lat=${lat}&lon=${lon}`
    );
    if (!response.ok) return null;
    return await response.json();
  }

  /**
   * GET /api/health
   */
  static async checkHealth(): Promise<HealthStatus | null> {
    try {
      const res = await fetchWithTimeout(`${BASE_URL}/health`, {}, 3000);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }
}
