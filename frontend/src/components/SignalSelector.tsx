import React from 'react';
import { Activity, Flame, HeartPulse, Brain, AlertTriangle, ShieldAlert, Droplets, Bone, Thermometer, Skull, Wind, Zap } from 'lucide-react';
import { motion } from 'framer-motion';

const SIGNALS = [
  { id: 'bleeding', label: 'Bleeding', icon: Droplets },
  { id: 'unconscious', label: 'Unconscious', icon: Brain },
  { id: 'chest_pain', label: 'Chest Pain', icon: AlertTriangle },
  { id: 'breathing', label: 'Breathing Issue', icon: Wind },
  { id: 'head_injury', label: 'Head Injury', icon: Skull },
  { id: 'fracture', label: 'Fracture', icon: Bone },
  { id: 'burns', label: 'Burns', icon: Flame },
  { id: 'seizure', label: 'Seizure', icon: Zap },
  { id: 'choking', label: 'Choking', icon: ShieldAlert },
  { id: 'high_fever', label: 'High Fever', icon: Thermometer },
  { id: 'poisoning', label: 'Poisoning', icon: Activity },
  { id: 'allergic_reaction', label: 'Allergy', icon: HeartPulse },
];

interface Props {
  selected: string[];
  onChange: (signals: string[]) => void;
}

export default function SignalSelector({ selected, onChange }: Props) {
  const toggle = (id: string) => {
    onChange(selected.includes(id) ? selected.filter(s => s !== id) : [...selected, id]);
  };

  return (
    <div className="signal-grid">
      {SIGNALS.map(({ id, label, icon: Icon }) => (
        <motion.button
          key={id}
          whileTap={{ scale: 0.95 }}
          onClick={() => toggle(id)}
          className={`signal-btn ${selected.includes(id) ? 'signal-active' : ''}`}
        >
          <Icon size={16} className="signal-icon" />
          <span>{label}</span>
        </motion.button>
      ))}
    </div>
  );
}
