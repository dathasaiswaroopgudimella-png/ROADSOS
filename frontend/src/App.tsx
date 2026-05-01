// RoadSoS — Omniscient Architect Protocol v5.0
// Vulkan Command Center: Full emergency guidance UI
import React, { useState, useEffect, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Shield, Activity, MapPin, Wifi, WifiOff, Zap, Database, RotateCcw, Search } from 'lucide-react';
import CommandSearch from './components/CommandSearch';
import EmergencyButton from './components/EmergencyButton';
import SignalSelector from './components/SignalSelector';
import DecisionScreen from './components/DecisionScreen';
import HospitalCard from './components/HospitalCard';
import WeatherBanner from './components/WeatherBanner';
import { useHaptics } from './hooks/useHaptics';
import { ApiService } from './services/api';
import { EmergencyResponse, EmergencyState, Hospital, HealthStatus, LocationSource } from './types';

export default function App() {
  // Core state
  const [state, setState] = useState<EmergencyState>('IDLE');
  const [signals, setSignals] = useState<string[]>([]);
  const [response, setResponse] = useState<EmergencyResponse | null>(null);

  // Location state (multi-source)
  const [lat, setLat] = useState<number | null>(null);
  const [lon, setLon] = useState<number | null>(null);
  const [locationLabel, setLocationLabel] = useState<string>('');
  const [locationSource, setLocationSource] = useState<LocationSource>(null);
  const [gpsLoading, setGpsLoading] = useState(true);

  // Search results (from CommandSearch)
  const [searchHospitals, setSearchHospitals] = useState<Hospital[]>([]);

  // System health
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isOnline, setIsOnline] = useState(true);

  const haptics = useHaptics();

  // ─── GPS Location (Tier 1) ───
  useEffect(() => {
    if (!navigator.geolocation) {
      setGpsLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLat(pos.coords.latitude);
        setLon(pos.coords.longitude);
        setLocationSource('gps');
        setLocationLabel(`GPS: ${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`);
        setGpsLoading(false);
      },
      () => {
        setGpsLoading(false);
        // GPS failed — user can use Command Search (Tier 2)
      },
      { timeout: 8000, maximumAge: 60000, enableHighAccuracy: true }
    );
  }, []);

  // ─── Health Check ───
  useEffect(() => {
    const check = async () => {
      const h = await ApiService.checkHealth();
      setHealth(h);
      setIsOnline(!!h);
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  // ─── Search handlers (Tier 2: Command Search) ───
  const handleLocationResolved = useCallback((newLat: number, newLon: number, label: string) => {
    setLat(newLat);
    setLon(newLon);
    setLocationLabel(label);
    setLocationSource('search');
  }, []);

  const handleHospitalsFound = useCallback((hospitals: Hospital[]) => {
    setSearchHospitals(hospitals);
  }, []);

  // ─── Emergency SOS ───
  const handleSOS = async () => {
    haptics.emergency();

    if (lat == null || lon == null) {
      haptics.alert();
      return;
    }

    setState('TRIAGING');

    try {
      const res = await ApiService.getGuidance(lat, lon, signals, false);
      setResponse(res);
      haptics.alert();
      setState('DECIDED');
    } catch (err) {
      // Failsafe: rule engine on client
      haptics.alert();
      setResponse({
        status: 'fallback',
        plan: {
          primary_action: 'Call Emergency Services (102) NOW',
          secondary_action: 'System could not connect to server. Do not wait.',
          reason: 'Communication failure. Safety override activated.',
          severity: 'critical',
          confidence: 1.0,
          tier_used: 'client_failsafe',
          ai_insight: null,
          weather_context: null,
        },
        hospitals: searchHospitals.length > 0 ? searchHospitals : [],
        weather: null,
        metadata: { error: true },
      });
      setState('DECIDED');
    }
  };

  const reset = () => {
    haptics.tap();
    setSignals([]);
    setResponse(null);
    setSearchHospitals([]);
    setState('IDLE');
  };

  const hasLocation = lat != null && lon != null;
  const dbTotal = health?.db_stats?.total_hospitals || 0;

  return (
    <div className="app-container">
      {/* Mesh Background */}
      <div className="mesh-bg">
        <div className="mesh-blob blob-1" />
        <div className="mesh-blob blob-2" />
        <div className="mesh-blob blob-3" />
      </div>

      {/* ─── Top Status Bar ─── */}
      <header className="status-bar">
        <div className="status-bar-left">
          <div className={`status-indicator ${hasLocation ? 'status-active' : gpsLoading ? 'status-loading' : 'status-error'}`}>
            <MapPin size={11} />
            <span>
              {gpsLoading ? 'GPS...' : hasLocation
                ? (locationSource === 'gps' ? 'GPS' : 'SEARCH')
                : 'NO LOC'}
            </span>
          </div>
          <div className="status-divider" />
          <div className={`status-indicator ${isOnline ? 'status-active' : 'status-error'}`}>
            {isOnline ? <Wifi size={11} /> : <WifiOff size={11} />}
            <span>{isOnline ? 'ONLINE' : 'OFFLINE'}</span>
          </div>
          {dbTotal > 0 && (
            <>
              <div className="status-divider" />
              <div className="status-indicator status-db">
                <Database size={11} />
                <span>{dbTotal.toLocaleString()}</span>
              </div>
            </>
          )}
        </div>
        <div className="status-bar-right">
          <Shield size={14} className="text-white/15" />
        </div>
      </header>

      {/* ─── Main Content ─── */}
      <main className="main-content">
        <AnimatePresence mode="wait">

          {/* ═══ IDLE STATE ═══ */}
          {state === 'IDLE' && (
            <motion.div
              key="idle"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 1.05, filter: 'blur(8px)' }}
              transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
              className="idle-screen"
            >
              {/* Logo */}
              <div className="app-logo">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', stiffness: 260, damping: 20, delay: 0.1 }}
                  className="logo-icon-wrapper"
                >
                  <div className="logo-glow" />
                  <Zap size={48} className="logo-icon" fill="currentColor" />
                </motion.div>
                <h1 className="app-title">RoadSoS</h1>
                <p className="app-subtitle">Emergency Guidance Command Center</p>
              </div>

              {/* ─── Command Search (Tier 2 Location) ─── */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="w-full flex justify-center"
              >
                <CommandSearch
                  onLocationResolved={handleLocationResolved}
                  onHospitalsFound={handleHospitalsFound}
                />
              </motion.div>

              {/* Location Label */}
              {hasLocation && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="location-badge"
                >
                  <MapPin size={12} />
                  <span>{locationLabel || `${lat!.toFixed(4)}, ${lon!.toFixed(4)}`}</span>
                </motion.div>
              )}

              {/* ─── Signal Selector ─── */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
              >
                <SignalSelector selected={signals} onChange={(s) => { haptics.tap(); setSignals(s); }} />
              </motion.div>

              {/* ─── SOS Button ─── */}
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.4, type: 'spring' }}
                className="sos-wrapper"
              >
                <div className={`sos-glow ${!hasLocation ? 'sos-disabled-glow' : ''}`} />
                <EmergencyButton onPress={handleSOS} />
                {!hasLocation && (
                  <p className="sos-hint">Enter location or enable GPS to activate</p>
                )}
              </motion.div>

              {/* ─── Search Results Preview ─── */}
              {searchHospitals.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="search-results-preview"
                >
                  <h3 className="section-title">
                    <Search size={14} />
                    <span>Hospitals Found ({searchHospitals.length})</span>
                  </h3>
                  <div className="hospital-list">
                    {searchHospitals.slice(0, 5).map((h, i) => (
                      <HospitalCard key={h.sr_no} hospital={h} index={i} />
                    ))}
                  </div>
                </motion.div>
              )}
            </motion.div>
          )}

          {/* ═══ TRIAGING STATE ═══ */}
          {state === 'TRIAGING' && (
            <motion.div
              key="triaging"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="triaging-screen"
            >
              <div className="triaging-spinner">
                <Activity className="animate-spin" size={72} />
                <div className="triaging-glow" />
              </div>
              <h2 className="triaging-title">Analyzing Emergency</h2>
              <p className="triaging-subtitle">Racing AI + Rule Engine for fastest response...</p>
              <div className="triaging-signals">
                {signals.map(s => (
                  <span key={s} className="triaging-signal-tag">{s}</span>
                ))}
              </div>
            </motion.div>
          )}

          {/* ═══ DECIDED STATE ═══ */}
          {state === 'DECIDED' && response && (
            <motion.div
              key="decided"
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, ease: [0.23, 1, 0.32, 1] }}
              className="decided-screen"
            >
              {/* Weather Banner */}
              {response.weather && <WeatherBanner weather={response.weather} />}

              {/* Decision Card */}
              <DecisionScreen plan={response.plan} />

              {/* Hospital List */}
              {response.hospitals.length > 0 && (
                <div className="decided-hospitals">
                  <h3 className="section-title">
                    <Database size={14} />
                    <span>Nearest Facilities ({response.hospitals.length})</span>
                  </h3>
                  <div className="hospital-list">
                    {response.hospitals.map((h, i) => (
                      <HospitalCard key={h.sr_no || i} hospital={h} index={i} />
                    ))}
                  </div>
                </div>
              )}

              {/* Metadata */}
              {response.metadata && (
                <div className="metadata-bar">
                  <span>Engine: {response.metadata.engine_version || 'v5'}</span>
                  <span>•</span>
                  <span>{response.metadata.time_ms}ms</span>
                  <span>•</span>
                  <span>{response.metadata.hospitals_found} hospitals scanned</span>
                </div>
              )}

              {/* Reset Button */}
              <button onClick={reset} className="reset-btn">
                <RotateCcw size={14} />
                <span>New Emergency</span>
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
