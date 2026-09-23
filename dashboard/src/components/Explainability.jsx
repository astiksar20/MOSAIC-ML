import React from 'react';
import { HelpCircle, FileText, Cpu, Activity, Database, Sparkles, AlertCircle } from 'lucide-react';

export const Explainability = ({ data }) => {
  if (!data) return null;

  const { apk_analysis, ml_analysis, cve_analysis, hids_analysis, risk_analysis } = data;

  const permissionsCount = apk_analysis?.permissions?.length || 0;
  const componentsCount = (apk_analysis?.activities?.length || 0) +
                          (apk_analysis?.services?.length || 0) +
                          (apk_analysis?.receivers?.length || 0) +
                          (apk_analysis?.providers?.length || 0);

  const mlLabel = ml_analysis?.label || 'BENIGN';
  const mlProb = ((ml_analysis?.malware_probability || 0) * 100).toFixed(2) + '%';
  const matchedFeatures = ml_analysis?.matched_features || 0;

  const hidsScore = typeof hids_analysis?.hids_score === 'number' ? hids_analysis.hids_score.toFixed(2) : '0';
  const hidsAlertsCount = hids_analysis?.alerts?.length || 0;

  const cveCount = cve_analysis?.cve_count || 0;

  return (
    <div className="saas-card p-8 md:p-10 mb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pb-6 border-b border-white/5">
        <div>
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-xs font-bold uppercase tracking-wider mb-2">
            <HelpCircle className="w-4 h-4" />
            <span>Explainable Security Audit Trail</span>
          </div>
          <h3 className="text-2xl font-bold text-white tracking-tight">
            Why did MOSAIC-ML produce this result?
          </h3>
          <p className="text-xs md:text-sm text-slate-400 mt-1">
            Empirical evidence breakdown across all security evaluation modules.
          </p>
        </div>

        <div className="px-4 py-2 rounded-xl bg-slate-900 border border-white/10 text-xs font-mono text-cyan-300">
          Evaluated Signals: <strong className="text-white">4 Pipeline Modules</strong>
        </div>
      </div>

      {/* Spacious 2-Column Evidence Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* 1. Static Analysis Evidence */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-white/5 space-y-3">
          <div className="flex items-center gap-3 text-sm font-bold text-slate-200">
            <div className="w-8 h-8 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <FileText className="w-4 h-4" />
            </div>
            <span>STATIC ANALYSIS EVIDENCE</span>
          </div>
          <ul className="text-xs text-slate-300 space-y-2 font-mono pl-2">
            <li>• Matched MH-100K Features: <span className="text-cyan-400 font-bold">{matchedFeatures}</span></li>
            <li>• Declared Permissions: <span className="text-slate-100">{permissionsCount}</span></li>
            <li>• Application Components: <span className="text-slate-100">{componentsCount}</span></li>
          </ul>
        </div>

        {/* 2. ML Signal Evidence */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-white/5 space-y-3">
          <div className="flex items-center gap-3 text-sm font-bold text-slate-200">
            <div className="w-8 h-8 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400">
              <Cpu className="w-4 h-4" />
            </div>
            <span>ML CLASSIFICATION SIGNAL</span>
          </div>
          <ul className="text-xs text-slate-300 space-y-2 font-mono pl-2">
            <li>• ML Classification: <span className="text-white font-bold">{mlLabel}</span></li>
            <li>• Malware Probability: <span className="text-rose-400 font-bold">{mlProb}</span></li>
            <li>• Algorithm: Random Forest Decision Trees</li>
          </ul>
        </div>

        {/* 3. HIDS Signal Evidence */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-white/5 space-y-3">
          <div className="flex items-center gap-3 text-sm font-bold text-slate-200">
            <div className="w-8 h-8 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <Activity className="w-4 h-4" />
            </div>
            <span>HIDS INTRUSION SIGNAL</span>
          </div>
          <ul className="text-xs text-slate-300 space-y-2 font-mono pl-2">
            <li>• HIDS Score: <span className="text-cyan-400 font-bold">{hidsScore}</span></li>
            <li>• Telemetry Rule Alerts: <span className="text-white font-bold">{hidsAlertsCount}</span></li>
            <li>• Isolation Forest Behavioral Anomaly Evaluation</li>
          </ul>
        </div>

        {/* 4. CVE/NVD Signal Evidence */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-white/5 space-y-3">
          <div className="flex items-center gap-3 text-sm font-bold text-slate-200">
            <div className="w-8 h-8 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <Database className="w-4 h-4" />
            </div>
            <span>CVE / NVD INTELLIGENCE SIGNAL</span>
          </div>
          <ul className="text-xs text-slate-300 space-y-2 font-mono pl-2">
            <li>• Matching CVE Records Found: <span className="text-amber-400 font-bold">{cveCount}</span></li>
            <li>• Component Strings Searched: <span className="text-white">{cve_analysis?.components_searched?.length || 0}</span></li>
          </ul>
        </div>
      </div>

      {/* Factual Disclaimer */}
      <div className="p-5 rounded-2xl bg-slate-950 border border-white/5 text-xs text-slate-400 space-y-2 font-sans">
        <div className="flex items-center gap-2 text-cyan-400 font-bold">
          <AlertCircle className="w-4 h-4" />
          <span>Factual Security Evidence Note</span>
        </div>
        <p className="leading-relaxed">
          These outputs represent aggregated empirical signals and heuristic indicators evaluated by MOSAIC-ML. They provide transparent research evidence rather than unverified assertions of intent.
        </p>
      </div>
    </div>
  );
};
