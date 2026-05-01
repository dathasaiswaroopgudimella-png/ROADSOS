import { useState, useEffect } from 'react';

export function useLocation() {
  const [lat, setLat] = useState<number | null>(null);
  const [lon, setLon] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Try GPS first
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLat(pos.coords.latitude);
          setLon(pos.coords.longitude);
        },
        (err) => {
          console.warn('GPS failed, using fallback Delhi coordinates.', err);
          // Delhi Fallback
          setLat(28.6139);
          setLon(77.2090);
          setError('GPS disabled. Using default location.');
        },
        { timeout: 5000, maximumAge: 60000 }
      );
    } else {
      setLat(28.6139);
      setLon(77.2090);
    }
  }, []);

  return { lat, lon, error };
}
