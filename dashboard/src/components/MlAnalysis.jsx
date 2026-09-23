import React from 'react';
import { Cpu, ShieldCheck, ShieldAlert, Sparkles, BarChart3 } from 'lucide-react';

export const MlAnalysis = ({ data }) => {
  if (!data || !data.ml_analysis) return null;

  const { ml_analysis } = data;
  const {
    matched_features = 0,
    prediction = 0,
    label = 'BENIGN',
    malware_probability = 0,
    benign_probability = 1.0
  } = ml_analysis;

  const isMalware = label === 'MALWARE';
  const malwarePct = (malware_probability * 100).toFixed(2);
  const benignPct = (benign_probability * 100).toFixed(2);

  return (
    <div className="saas-card p-8 md:p-10 mb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pb-6 border-b border-white/5">
        <div>
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-xs font-bold uppercase tracking-wider mb-2">
            <Cpu className="w-4 h-4" />
            <span>MH-100K High-Dimensional Feature Space</span>
          </div>
          <h3 className="text-2xl font-bold text-white tracking-tight">
            Machine Learning Analysis
          </h3>
          <p className="text-xs md:text-sm text-slate-400 mt-1">
            Random Forest model classification trained on Android application feature vectors.
          </p>
        </div>

        <div className="px-4 py-2.5 rounded-2xl bg-slate-900 border border-white/10 text-xs font-mono text-cyan-300 flex items-center gap-2.5 self-start md:self-auto">
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <span>Matched Features: <strong className="text-white text-sm">{matched_features}</strong></span>
        </div>
      </div>

      {/* Grid Content */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
        {/* Left: Classification Badge */}
        <div className={`lg:col-span-5 p-8 rounded-3xl border flex flex-col justify-between relative overflow-hidden ${
          isMalware
            ? 'bg-rose-950/20 border-rose-500/40'
            : 'bg-emerald-950/20 border-emerald-500/40'
        }`}>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono">
              Model Classification Output
            </span>

            <div className="mt-6 flex items-center gap-4">
              {isMalware ? (
                <div className="w-14 h-14 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 shrink-0">
                  <ShieldAlert className="w-8 h-8 animate-pulse" />
                </div>
              ) : (
                <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
                  <ShieldCheck className="w-8 h-8" />
                </div>
              )}

              <div>
                <span className={`text-3xl font-black font-mono tracking-wide ${
                  isMalware ? 'text-rose-400' : 'text-emerald-400'
                }`}>
                  {label}
                </span>
                <p className="text-xs text-slate-400 font-mono mt-1">
                  Prediction Target Index: {prediction}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-8 pt-4 border-t border-white/10 text-xs text-slate-300 leading-relaxed font-sans">
            {isMalware
              ? 'Feature attributes closely align with known malware family patterns within decision tree thresholds.'
              : 'Feature attributes align with standard benign application profiles in the MH-100K vector space.'}
          </div>
        </div>

        {/* Right: Probability Visualizer Bars */}
        <div className="lg:col-span-7 p-8 rounded-3xl bg-slate-900/60 border border-white/5 flex flex-col justify-between space-y-6">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2 font-mono">
            <BarChart3 className="w-4 h-4 text-cyan-400" />
            <span>Model Probability Distribution</span>
          </h4>

          <div className="space-y-6">
            {/* Benign Bar */}
            <div>
              <div className="flex justify-between items-center text-xs font-mono mb-2">
                <span className="text-emerald-400 font-bold flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                  Benign Probability
                </span>
                <span className="text-white font-extrabold text-sm">{benignPct}%</span>
              </div>
              <div className="w-full bg-slate-950 rounded-full h-3.5 overflow-hidden border border-white/5 p-0.5">
                <div
                  className="bg-gradient-to-r from-emerald-500 to-teal-400 h-full rounded-full transition-all duration-1000 shadow-[0_0_15px_#10b981]"
                  style={{ width: `${benignPct}%` }}
                />
              </div>
            </div>

            {/* Malware Bar */}
            <div>
              <div className="flex justify-between items-center text-xs font-mono mb-2">
                <span className="text-rose-400 font-bold flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-400" />
                  Malware Probability
                </span>
                <span className="text-white font-extrabold text-sm">{malwarePct}%</span>
              </div>
              <div className="w-full bg-slate-950 rounded-full h-3.5 overflow-hidden border border-white/5 p-0.5">
                <div
                  className="bg-gradient-to-r from-rose-600 to-rose-400 h-full rounded-full transition-all duration-1000 shadow-[0_0_15px_#f43f5e]"
                  style={{ width: `${malwarePct}%` }}
                />
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-white/5 text-[11px] text-slate-400 font-mono flex items-center justify-between">
            <span>Classifier: Random Forest</span>
            <span>Feature Mapping: 100,000 Dimensions</span>
          </div>
        </div>
      </div>
    </div>
  );
};
