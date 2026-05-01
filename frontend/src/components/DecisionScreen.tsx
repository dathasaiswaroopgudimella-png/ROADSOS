// RoadSoS — Decision Screen: Shows triage result + AI insight + first aid tips
import React from 'react';
import { AlertCircle, Brain, Shield, Lightbulb, Zap } from 'lucide-react';
import { motion } from 'framer-motion';
import { ActionPlan } from '../types';

interface Props {
  plan: ActionPlan;
}

const severityConfig: Record<string, { color: string; bg: string; border: string; label: string }> = {
  critical: { color: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/30', label: '🔴 CRITICAL' },
  high:     { color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30', label: '🟠 HIGH' },
  medium:   { color: 'text-sky-400', bg: 'bg-sky-500/10', border: 'border-sky-500/30', label: '🔵 MEDIUM' },
  low:      { color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', label: '🟢 LOW' },
};

export default function DecisionScreen({ plan }: Props) {
  const sev = severityConfig[plan.severity] || severityConfig.medium;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
      className="decision-card"
    >
      {/* Severity Strip */}
      <div className={`decision-severity-strip ${plan.severity === 'critical' ? 'strip-critical' : plan.severity === 'high' ? 'strip-high' : 'strip-normal'}`} />

      {/* Severity Badge + Engine Tag */}
      <div className="decision-header">
        <div className={`decision-badge ${sev.bg} ${sev.border} ${sev.color}`}>
          <AlertCircle size={14} />
          <span>{sev.label}</span>
        </div>
        <div className="decision-engine-tag">
          <Zap size={10} />
          <span>{plan.tier_used.replace(/_/g, ' ')}</span>
        </div>
      </div>

      {/* Primary Action */}
      <h2 className="decision-primary">{plan.primary_action}</h2>

      {/* Secondary Action */}
      <p className="decision-secondary">{plan.secondary_action}</p>

      {/* AI Reasoning */}
      <div className="decision-reasoning">
        <div className="decision-reasoning-header">
          <Brain size={14} />
          <span>Analysis</span>
          <span className="decision-confidence">{Math.round(plan.confidence * 100)}% confidence</span>
        </div>
        <p>{plan.reason}</p>
      </div>

      {/* AI Expert Insight (if LLM succeeded) */}
      {plan.ai_insight && (
        <div className="decision-ai-insight">
          <div className="decision-reasoning-header">
            <Shield size={14} />
            <span>AI Expert Insight</span>
            <span className="decision-source">{plan.ai_insight.source}</span>
          </div>

          {plan.ai_insight.recommended_hospital && (
            <p className="ai-recommendation">
              <strong>Recommended:</strong> {plan.ai_insight.recommended_hospital}
            </p>
          )}

          {plan.ai_insight.estimated_response_time && (
            <p className="ai-eta">
              <strong>Estimated response:</strong> {plan.ai_insight.estimated_response_time}
            </p>
          )}

          {plan.ai_insight.first_aid_tips && plan.ai_insight.first_aid_tips.length > 0 && (
            <div className="ai-tips">
              <div className="ai-tips-header">
                <Lightbulb size={12} />
                <span>First Aid Tips</span>
              </div>
              <ul>
                {plan.ai_insight.first_aid_tips.map((tip, i) => (
                  <li key={i}>{tip}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Weather Context */}
      {plan.weather_context && (
        <div className="decision-weather-note">
          <span>⛅ Weather factor: {plan.weather_context}</span>
        </div>
      )}
    </motion.div>
  );
}
