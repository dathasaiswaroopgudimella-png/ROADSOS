import React from 'react';
import { motion } from 'framer-motion';

interface Props {
  onPress: () => void;
}

export default function EmergencyButton({ onPress }: Props) {
  return (
    <div className="relative flex items-center justify-center">
      {/* Outer pulse ring */}
      <div className="absolute w-[240px] h-[240px] rounded-full border-2 border-rose-500/30 pulse-ring"></div>
      
      {/* Inner breathe ring */}
      <div className="absolute w-[260px] h-[260px] rounded-full border border-rose-500/10 breathe"></div>

      <motion.button
        className="sos-button"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.92 }}
        onClick={onPress}
      >
        SOS
      </motion.button>
    </div>
  );
}
