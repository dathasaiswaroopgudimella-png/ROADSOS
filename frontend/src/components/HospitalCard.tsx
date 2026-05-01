// RoadSoS — Hospital Card: Shows REAL data from the 10k hospital CSV
import React from 'react';
import { Navigation, Phone, Bed, Stethoscope, Building2, Ambulance, MapPin } from 'lucide-react';
import { motion } from 'framer-motion';
import { Hospital } from '../types';

interface Props {
  hospital: Hospital;
  index: number;
}

function getPhone(h: Hospital): string {
  return h.emergency_num || h.ambulance_phone || h.telephone || h.mobile_number || h.helpline || h.tollfree || '102';
}

export default function HospitalCard({ hospital: h, index }: Props) {
  const phone = getPhone(h);
  const hasEmergency = !!(h.emergency_num || h.ambulance_phone);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
      className="hospital-card"
    >
      {/* Header */}
      <div className="hospital-card-header">
        <div className="hospital-card-info">
          <h4 className="hospital-card-name">{h.hospital_name || 'Unknown Hospital'}</h4>
          <div className="hospital-card-meta">
            {h.hospital_care_type && (
              <span className="hospital-tag tag-type">
                <Stethoscope size={10} /> {h.hospital_care_type}
              </span>
            )}
            {h.discipline && (
              <span className="hospital-tag tag-discipline">{h.discipline}</span>
            )}
          </div>
        </div>
        {h.distance_km != null && (
          <div className="hospital-card-distance">
            <span className="distance-value">{h.distance_km}</span>
            <span className="distance-unit">km</span>
          </div>
        )}
      </div>

      {/* Address */}
      <div className="hospital-card-address">
        <MapPin size={12} />
        <span>
          {[h.address, h.town, h.district, h.state, h.pincode]
            .filter(Boolean)
            .join(', ')}
        </span>
      </div>

      {/* Stats Row */}
      <div className="hospital-card-stats">
        {h.total_beds > 0 && (
          <div className="stat-item">
            <Bed size={14} />
            <span>{h.total_beds} beds</span>
          </div>
        )}
        {h.num_doctors > 0 && (
          <div className="stat-item">
            <Stethoscope size={14} />
            <span>{h.num_doctors} doctors</span>
          </div>
        )}
        {hasEmergency && (
          <div className="stat-item stat-emergency">
            <Ambulance size={14} />
            <span>Emergency</span>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="hospital-card-actions">
        <a
          href={`tel:${phone.split(',')[0].trim()}`}
          className="action-btn action-call"
        >
          <Phone size={16} />
          <div className="action-btn-text">
            <span className="action-label">Call Now</span>
            <span className="action-detail">{phone.split(',')[0].trim()}</span>
          </div>
        </a>

        {h.lat && h.lon && (
          <a
            href={`https://www.google.com/maps/dir/?api=1&destination=${h.lat},${h.lon}`}
            target="_blank"
            rel="noreferrer"
            className="action-btn action-navigate"
          >
            <Navigation size={16} />
            <div className="action-btn-text">
              <span className="action-label">Navigate</span>
              <span className="action-detail">{h.distance_km ? `${h.distance_km} km` : 'Directions'}</span>
            </div>
          </a>
        )}
      </div>

      {/* Extra phones */}
      {h.ambulance_phone && h.ambulance_phone !== phone && (
        <div className="hospital-card-extra">
          <Ambulance size={12} />
          <span>Ambulance: </span>
          <a href={`tel:${h.ambulance_phone.split(',')[0].trim()}`}>{h.ambulance_phone}</a>
        </div>
      )}
    </motion.div>
  );
}
