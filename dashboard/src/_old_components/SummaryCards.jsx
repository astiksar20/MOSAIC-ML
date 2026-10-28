import React from 'react';
import { Shield, Activity, Database, Sparkles, Layers, Cpu } from 'lucide-react';

export const SummaryCards = ({ data }) => {
  if (!data) return null;

  const { apk_analysis, ml_analysis, cve_analysis, hids_analysis } = data;

  const mlLabel = ml_analysis?.label || 'BENIGN';
  const isMalware = mlLabel === 'MALWARE';
  const malwareProb = ((ml_analysis?.malware_probability || 0) * 100).toFixed(1) + '%';
  const hidsScore = typeof hids_analysis?.hids_score === 'number' ? hids_analysis.hids_score.toFixed(1) : '0.0';
  const cveCount = cve_analysis?.cve_count ?? 0;
  const matchedFeatures = ml_analysis?.matched_features || 0;

  const totalComponents = (apk_analysis?.activities?.length || 0) +
                          (apk_analysis?.services?.length || 0) +
                          (apk_analysis?.receivers?.length || 0) +
                          (apk_analysis?.providers?.length || 0);

  return (
    <div className="mb-12">
      <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6">
        Executive Security Summary
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Card 1: ML Classification */}
        <div className="saas-card saas-card-hover p-7 flex flex-col justify-between border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-4">
            <span className="text-xs font-bold uppercase tracking-wider">ML Classification</span>
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${
              isMalware ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
            }`}>
              <Shield className="w-5 h-5" />
            </div>
          </div>
          <div>
            <span className={`status-pill ${isMalware ? 'pill-high' : 'pill-low'} text-sm font-mono font-bold`}>
              {mlLabel}
            </span>
            <p className="text-xs text-slate-400 mt-2 font-mono">
              Random Forest Decision Model
            </p>
          </div>
        </div>

        {/* Card 2: Malware Probability */}
        <div className="saas-card saas-card-hover p-7 flex flex-col justify-between border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-4">
            <span className="text-xs font-bold uppercase tracking-wider">Malware Probability</span>
            <div className="w-9 h-9 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400">
              <Cpu className="w-5 h-5" />
            </div>
          </div>
          <div>
            <h4 className="text-3xl font-black text-white font-mono">
              {malwareProb}
            </h4>
            <p className="text-xs text-slate-400 mt-2 font-mono">
              Model Probability Estimation
            </p>
          </div>
        </div>

        {/* Card 3: HIDS Score */}
        <div className="saas-card saas-card-hover p-7 flex flex-col justify-between border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-4">
            <span className="text-xs font-bold uppercase tracking-wider">HIDS Score</span>
            <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <Activity className="w-5 h-5" />
            </div>
          </div>
          <div>
            <h4 className="text-3xl font-black text-white font-mono">
              {hidsScore}
            </h4>
            <p className="text-xs text-slate-400 mt-2 font-mono">
              {hids_analysis?.alerts?.length || 0} Telemetry Alert Triggers
            </p>
          </div>
        </div>

        {/* Card 4: CVE Records */}
        <div className="saas-card saas-card-hover p-7 flex flex-col justify-between border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-4">
            <span className="text-xs font-bold uppercase tracking-wider">CVE Records Found</span>
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <Database className="w-5 h-5" />
            </div>
          </div>
          <div>
            <h4 className="text-3xl font-black text-white font-mono">
              {cveCount}
            </h4>
            <p className="text-xs text-slate-400 mt-2 font-mono">
              NVD Component Matches
            </p>
          </div>
        </div>

        {/* Card 5: Matched Features */}
        <div className="saas-card saas-card-hover p-7 flex flex-col justify-between border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-4">
            <span className="text-xs font-bold uppercase tracking-wider">Matched Features</span>
            <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <Sparkles className="w-5 h-5" />
            </div>
          </div>
          <div>
            <h4 className="text-3xl font-black text-white font-mono">
              {matchedFeatures}
            </h4>
            <p className="text-xs text-slate-400 mt-2 font-mono">
              MH-100K Vector Attributes
            </p>
          </div>
        </div>

        {/* Card 6: APK Components */}
        <div className="saas-card saas-card-hover p-7 flex flex-col justify-between border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-4">
            <span className="text-xs font-bold uppercase tracking-wider">APK Components</span>
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Layers className="w-5 h-5" />
            </div>
          </div>
          <div>
            <h4 className="text-3xl font-black text-white font-mono">
              {totalComponents}
            </h4>
            <p className="text-xs text-slate-400 mt-2 font-mono">
              Declared Manifest Services & Views
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
