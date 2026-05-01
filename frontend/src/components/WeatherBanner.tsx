// RoadSoS — Weather Banner: Shows real-time weather conditions from WeatherAPI
import React from 'react';
import { CloudRain, Wind, Eye, Thermometer, AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';
import { WeatherInfo } from '../types';

interface Props {
  weather: WeatherInfo;
}

export default function WeatherBanner({ weather }: Props) {
  if (weather.status !== 'ok') return null;

  const impactColor = weather.impact === 'severe'
    ? 'weather-severe'
    : weather.impact === 'moderate'
    ? 'weather-moderate'
    : 'weather-normal';

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      className={`weather-banner ${impactColor}`}
    >
      <div className="weather-banner-main">
        <div className="weather-condition">
          {weather.condition_icon && (
            <img src={`https:${weather.condition_icon}`} alt="" className="weather-icon" />
          )}
          <div>
            <span className="weather-temp">{weather.temperature_c}°C</span>
            <span className="weather-desc">{weather.condition}</span>
          </div>
        </div>
        <div className="weather-stats">
          <span><Wind size={12} /> {weather.wind_kph} kph</span>
          <span><Eye size={12} /> {weather.visibility_km} km</span>
          {weather.precipitation_mm != null && weather.precipitation_mm > 0 && (
            <span><CloudRain size={12} /> {weather.precipitation_mm}mm</span>
          )}
        </div>
      </div>

      {weather.warnings && weather.warnings.length > 0 && (
        <div className="weather-warnings">
          {weather.warnings.map((w, i) => (
            <div key={i} className="weather-warning-item">
              <AlertTriangle size={12} />
              <span>{w}</span>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
