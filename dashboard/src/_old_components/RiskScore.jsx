import React from 'react';
import { Zap, ShieldCheck, Info } from 'lucide-react';

export const RiskScore = ({ data }) => {
  if (!data || !data.risk_analysis) return null;

  const { risk_analysis } = data;
  const {
    risk_score = 0,
    risk_category = 'LOW'
  } = risk_analysis;

  const numericScore = typeof risk_score === 'number' ? risk_score : parseFloat(risk_score) || 0;
  const normalizedScore = Math.min(100, Math.max(0, numericScore));

  // Circular gauge SVG metrics
  const radius = 80;
  const strokeWidth = 14;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  const getRiskTheme = (cat) => {
    switch ((cat || '').toUpperCase()) {
      case 'HIGH':
        return {
          stroke: '#f43f5e',
          textColor: 'text-rose-400',
          badgeClass: 'pill-high',
          glow: 'shadow-[0_0_60px_rgba(244,63,94,0.35)]',
          border: 'border-rose-500/40'
        };
      case 'MEDIUM':
        return {
          stroke: '#f59e0b',
          textColor: 'text-amber-400',
          badgeClass: 'pill-medium',
          glow: 'shadow-[0_0_60px_rgba(245,158,11,0.35)]',
          border: 'border-amber-500/40'
        };
      default: // LOW
        return {
          stroke: '#10b981',
          textColor: 'text-emerald-400',
          badgeClass: 'pill-low',
          glow: 'shadow-[0_0_60px_rgba(16,185,129,0.35)]',
          border: 'border-emerald-500/40'
        };
    }
  };

  const theme = getRiskTheme(risk_category);

  return (
    <div className="saas-card p-8 md:p-12 mb-12 border-cyan-500/30 relative overflow-hidden">
      {/* Background Lighting Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="flex flex-col items-center text-center max-w-3xl mx-auto space-y-6 relative z-10">
        {/* Title */}
        <div>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-bold uppercase tracking-wider mb-3">
            <Zap className="w-4 h-4" />
            <span>MOSAIC-ML Prototype Risk Score</span>
          </div>
          <p className="text-slate-400 text-xs md:text-sm font-mono">
            Aggregate Security Threat Calculation
          </p>
        </div>

        {/* Large Radial Score Visualization */}
        <div className={`relative w-64 h-64 flex items-center justify-center rounded-full ${theme.glow} transition-all duration-1000 my-4`}>
          <svg className="w-full h-full transform -rotate-90">
            {/* Background Track */}
            <circle
              cx="128"
              cy="128"
              r={radius}
              stroke="rgba(255, 255, 255, 0.08)"
              strokeWidth={strokeWidth}
              fill="transparent"
            />
            {/* Animated Gauge Ring */}
            <circle
              cx="128"
              cy="128"
              r={radius}
              stroke={theme.stroke}
              strokeWidth={strokeWidth}
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="transparent"
              className="transition-all duration-1000 ease-out"
            />
          </svg>

          {/* Inner Text Values */}
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="text-[10px] uppercase font-bold tracking-widest text-slate-400 font-mono">
              Risk Score
            </span>
            <span className="text-5xl md:text-6xl font-black font-mono text-white tracking-tight my-1">
              {numericScore.toFixed(1)}
            </span>
            <span className={`status-pill ${theme.badgeClass} text-xs mt-1 font-mono`}>
              {risk_category}
            </span>
          </div>
        </div>

        {/* Subtitle Label */}
        <div className="space-y-2">
          <h4 className="text-base font-bold text-slate-200">
            Prototype risk aggregation
          </h4>
          <p className="text-xs text-slate-400 max-w-xl mx-auto leading-relaxed font-sans">
            Synthesized from static manifest features, Random Forest ML decision boundaries, NVD vulnerability lookups, and HIDS runtime rules.
          </p>
        </div>

        {/* Mandatory Academic Disclaimer Note */}
        <div className="w-full max-w-xl p-4 rounded-2xl bg-slate-950/80 border border-white/10 text-xs text-slate-400 flex items-start gap-3 text-left font-mono">
          <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            This is a prototype aggregation of available security signals and has not been experimentally calibrated as a probability of compromise.
          </p>
        </div>
      </div>
    </div>
  );
};
