// RoadSoS — Command Search: Search by pincode, district, town, or hospital name
import React, { useState, useCallback } from 'react';
import { Search, MapPin, Loader2, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { ApiService } from '../services/api';
import { Hospital } from '../types';

interface Props {
  onLocationResolved: (lat: number, lon: number, label: string) => void;
  onHospitalsFound: (hospitals: Hospital[]) => void;
}

export default function CommandSearch({ onLocationResolved, onHospitalsFound }: Props) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [resultCount, setResultCount] = useState<number | null>(null);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    setResultCount(null);

    try {
      // 1. Try geocoding the query (for pincodes, districts, towns)
      const geoResult = await ApiService.geocode(query.trim());

      if (geoResult.status === 'ok' && geoResult.lat && geoResult.lon) {
        onLocationResolved(geoResult.lat, geoResult.lon, geoResult.formatted || query);

        // 2. Also search hospitals matching the query text
        const searchResult = await ApiService.searchHospitals(
          query.trim(), geoResult.lat, geoResult.lon
        );
        if (searchResult.hospitals.length > 0) {
          onHospitalsFound(searchResult.hospitals);
          setResultCount(searchResult.count);
        }
      } else {
        // Geocode failed — try direct hospital search
        const searchResult = await ApiService.searchHospitals(query.trim());
        if (searchResult.hospitals.length > 0) {
          onHospitalsFound(searchResult.hospitals);
          setResultCount(searchResult.count);

          // Use first hospital's coords as location
          const first = searchResult.hospitals[0];
          if (first.lat && first.lon) {
            onLocationResolved(first.lat, first.lon, `${first.district}, ${first.state}`);
          }
        } else {
          setError('No hospitals found. Try a pincode, district, or city name.');
        }
      }
    } catch (e: any) {
      setError('Search failed. Check your connection and try again.');
    } finally {
      setLoading(false);
    }
  }, [query, onLocationResolved, onHospitalsFound]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch();
  };

  const clearSearch = () => {
    setQuery('');
    setError('');
    setResultCount(null);
  };

  return (
    <div className="w-full max-w-md">
      <div className="command-search-wrapper">
        <div className="command-search-icon">
          {loading ? (
            <Loader2 size={18} className="animate-spin" />
          ) : (
            <Search size={18} />
          )}
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter pincode, district, town, or hospital..."
          className="command-search-input"
          id="command-search"
          disabled={loading}
        />
        {query && (
          <button onClick={clearSearch} className="command-search-clear">
            <X size={14} />
          </button>
        )}
        <button
          onClick={handleSearch}
          disabled={loading || !query.trim()}
          className="command-search-btn"
        >
          <MapPin size={16} />
          <span>Locate</span>
        </button>
      </div>

      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="text-rose-400 text-xs mt-2 px-2"
          >
            {error}
          </motion.p>
        )}
        {resultCount !== null && (
          <motion.p
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="text-emerald-400 text-xs mt-2 px-2 font-medium"
          >
            ✓ Found {resultCount} hospitals matching "{query}"
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
}
