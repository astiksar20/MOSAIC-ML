import React from 'react';
import { Zap, AlertTriangle, ShieldCheck, ShieldAlert, Cpu, Activity, Database, Info, CheckCircle2 } from 'lucide-react';

export const RiskAnalysis = ({ data }) => {
  if (!data || !data.risk_analysis) return null;

  const { risk_analysis, ml_analysis, hids_analysis, cve_analysis } = data;
  const {
    risk_score = 0,
    risk_category = 'LOW',
    recommendation = 'Monitor application'
  } = risk_analysis;

  const numericScore = typeof risk_score === 'number' ? risk_score : parseFloat(risk_score) || 0;
  const normalizedScore = Math.min(100, Math.max(0, numericScore));

  // Circular gauge SVG calculations
  const radius = 70;
  const strokeWidth = 12;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  const getRiskColor = (cat) => {
    switch ((cat || '').toUpperCase()) {
      case 'HIGH':
        return {
          stroke: '#f43f5e',
          text: 'text-rose-400',
          badge: 'badge-high',
          glow: 'shadow-[0_0_40px_rgba(244,63,94,0.3)]',
          border: 'border-rose-500/40'
        };
      case 'MEDIUM':
        return {
          stroke: '#f59e0b',
          text: 'text-amber-400',
          badge: 'badge-medium',
          glow: 'shadow-[0_0_40px_rgba(245,158,11,0.3)]',
          border: 'border-amber-500/40'
        };
      default:
        return {
          stroke: '#10b981',
          text: 'text-emerald-400',
          badge: 'badge-low',
          glow: 'shadow-[0_0_40px_rgba(16,185,129,0.3)]',
          border: 'border-emerald-500/40'
        };
    }
  };

  const colors = getRiskColor(risk_category);

  // Extract individual signal inputs for transparency
  const mlProb = (ml_analysis?.malware_probability * 100).toFixed(1) || '0.0';
  const hidsVal = typeof hids_analysis?.hids_score === 'number' ? hids_analysis.hids_score.toFixed(1) : '0.0';
  const cveCount = cve_analysis?.cve_count || 0;

  return (
    <div id="risk" className="glass-card p-6 md:p-8 mb-8 border-cyan-500/30 shadow-2xl relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pb-6 border-b border-white/5 relative z-10">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <Zap className="w-3.5 h-3.5" />
            <span>Multi-Signal Synthesis Engine</span>
          </div>
          <h3 className="text-2xl font-extrabold text-white tracking-tight">
            MOSAIC-ML Risk Analysis
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Aggregated threat score computed from ML classification, HIDS telemetry, and CVSS vulnerability weights.
          </p>
        </div>

        <div className="px-4 py-2 rounded-xl bg-slate-900 border border-white/10 text-xs font-mono text-slate-300 flex items-center gap-2">
          <span>Engine Status: <strong className="text-emerald-400 font-bold">ACTIVE</strong></span>
        </div>
      </div>

      {/* Centerpiece Gauge & Recommendation Row */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center mb-8 relative z-10">
        {/* Left: Circular Score Gauge */}
        <div className="lg:col-span-5 flex flex-col items-center justify-center p-6 rounded-2xl bg-slate-950/70 border border-white/10 relative">
          <div className={`relative w-48 h-48 flex items-center justify-center rounded-full ${colors.glow} transition-all duration-700`}>
            <svg className="w-full h-full transform -rotate-90">
              {/* Gauge Track */}
              <circle
                cx="96"
                cy="96"
                r={radius}
                stroke="rgba(255, 255, 255, 0.08)"
                strokeWidth={strokeWidth}
                fill="transparent"
              />
              {/* Gauge Progress Fill */}
              <circle
                cx="96"
                cy="96"
                r={radius}
                stroke={colors.stroke}
                strokeWidth={strokeWidth}
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                fill="transparent"
                className="transition-all duration-1000 ease-out"
              />
            </svg>

            {/* Inner Gauge Text */}
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
              <span className="text-[10px] uppercase font-bold tracking-widest text-slate-400">
                Score
              </span>
              <span className="text-4xl font-black font-mono text-white tracking-tight my-0.5">
                {numericScore.toFixed(1)}
              </span>
              <span className={`badge ${colors.badge} text-[10px] mt-1`}>
                {risk_category} RISK
              </span>
            </div>
          </div>

          <div className="flex justify-between w-full max-w-xs text-[11px] font-mono text-slate-500 mt-4 px-2">
            <span>0 (Low Risk)</span>
            <span>50 (Medium)</span>
            <span>100 (Critical)</span>
          </div>
        </div>

        {/* Right: Recommendation & Categorization */}
        <div className="lg:col-span-7 space-y-6">
          <div className={`p-6 rounded-2xl bg-slate-900/80 border ${colors.border} space-y-3`}>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-cyan-400" />
                <span>Risk Engine Recommendation</span>
              </span>
              <span className="text-[10px] font-mono text-slate-500">Auto-Generated</span>
            </div>

            <h4 className="text-lg font-bold text-white tracking-tight capitalize">
              {recommendation}
            </h4>

            <p className="text-xs text-slate-300 leading-relaxed">
              Based on aggregated signals from Machine Learning, Host Intrusion Detection, and Vulnerability Intelligence,
              the engine advises: <strong className="text-cyan-300 font-semibold">{recommendation}</strong>.
            </p>
          </div>

          {/* Wording Title & Mandatory Academic Note */}
          <div className="p-4 rounded-xl bg-slate-950 border border-white/5 text-xs text-slate-400 space-y-2 font-mono">
            <div className="flex items-center justify-between text-slate-300 font-bold">
              <span>MOSAIC-ML Prototype Risk Score</span>
              <span className="text-cyan-400">Aggregation Engine</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
              Risk score is a prototype aggregation of available signals and has not yet been experimentally calibrated as a probability of compromise.
            </p>
          </div>
        </div>
      </div>

      {/* Contributing Signals Breakdown Cards */}
      <div>
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
          <span>Contributing Risk Signals</span>
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Signal 1: ML Signal */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="font-semibold uppercase tracking-wider flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                ML Signal
              </span>
              <span className="font-mono text-cyan-400 font-bold">{mlProb}%</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-normal">
              Random Forest malware classification probability from MH-100K feature vector space.
            </p>
          </div>

          {/* Signal 2: HIDS Signal */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="font-semibold uppercase tracking-wider flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-indigo-400" />
                HIDS Signal
              </span>
              <span className="font-mono text-indigo-400 font-bold">{hidsVal}</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-normal">
              Pattern rule alerts and Isolation Forest runtime behavioral anomaly indicators.
            </p>
          </div>

          {/* Signal 3: CVSS Signal */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="font-semibold uppercase tracking-wider flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-amber-400" />
                CVSS Signal
              </span>
              <span className="font-mono text-amber-400 font-bold">{cveCount} CVEs</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-normal">
              Published NVD vulnerability weights extracted from declared component strings.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
