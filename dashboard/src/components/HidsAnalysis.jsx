import React from 'react';
import { Activity, AlertTriangle, Info, Terminal, ShieldCheck } from 'lucide-react';

export const HidsAnalysis = ({ data }) => {
  if (!data || !data.hids_analysis) return null;

  const { hids_analysis } = data;
  const {
    rule_score = 0,
    alerts = [],
    hids_score = 0
  } = hids_analysis;

  const alertCount = alerts.length;
  const isAnomaly = hids_score > 50 || alertCount > 2;

  return (
    <div className="saas-card p-8 md:p-10 mb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pb-6 border-b border-white/5">
        <div>
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-bold uppercase tracking-wider mb-2">
            <Activity className="w-4 h-4" />
            <span>Host-Based Intrusion Detection System</span>
          </div>
          <h3 className="text-2xl font-bold text-white tracking-tight">
            Host-Based Intrusion Detection
          </h3>
          <p className="text-xs md:text-sm text-slate-400 mt-1">
            Rule-based event engine combined with Isolation Forest behavioral anomaly detection.
          </p>
        </div>

        {/* Isolation Forest Status Pill */}
        <div className={`status-pill ${isAnomaly ? 'pill-high' : 'pill-low'} font-mono text-xs self-start md:self-auto`}>
          {isAnomaly ? 'ANOMALY DETECTED' : 'NORMAL BEHAVIOR'}
        </div>
      </div>

      {/* Spacious 3-Column Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-white/5">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">
            Combined HIDS Score
          </span>
          <h4 className="text-3xl font-black text-white font-mono mt-2">
            {typeof hids_score === 'number' ? hids_score.toFixed(2) : hids_score}
          </h4>
          <p className="text-xs text-slate-500 mt-1">Aggregated Rule & Behavioral Index</p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/60 border border-white/5">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">
            Rule-Based Score
          </span>
          <h4 className="text-3xl font-black text-cyan-400 font-mono mt-2">
            {typeof rule_score === 'number' ? rule_score.toFixed(2) : rule_score}
          </h4>
          <p className="text-xs text-slate-500 mt-1">Pattern Rule Engine Match</p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/60 border border-white/5">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">
            Alert Count
          </span>
          <h4 className="text-3xl font-black text-violet-400 font-mono mt-2">
            {alertCount}
          </h4>
          <p className="text-xs text-slate-500 mt-1">Event Anomaly Triggers</p>
        </div>
      </div>

      {/* Suspicious Alerts Section */}
      <div className="mb-8">
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2 font-mono">
          <Terminal className="w-4 h-4 text-cyan-400" />
          <span>Suspicious Events Log</span>
        </h4>

        {alertCount === 0 ? (
          <div className="p-6 rounded-2xl bg-slate-900/40 border border-white/5 text-xs text-slate-400 font-mono">
            No rule-based alerts triggered in evaluated telemetry stream.
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert, idx) => {
              const eventName = typeof alert === 'string' ? alert : alert.event || alert.alert || `Event ${idx + 1}`;
              const alertType = alert.type || alert.alert_type || 'SUSPICIOUS ACTIVITY';
              const severity = (alert.severity || 'HIGH').toUpperCase();

              const isHigh = severity.includes('HIGH') || severity.includes('CRITICAL');

              return (
                <div
                  key={idx}
                  className="p-5 rounded-2xl bg-slate-900/80 border border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs font-mono"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                      isHigh ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    }`}>
                      <AlertTriangle className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="text-slate-100 font-bold text-sm">{eventName}</span>
                      <p className="text-[11px] text-slate-400 mt-0.5">{alertType}</p>
                    </div>
                  </div>

                  <span className={`status-pill ${isHigh ? 'pill-high' : 'pill-medium'} text-[10px]`}>
                    {severity} SEVERITY
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Subtle Academic Prototype Note */}
      <div className="p-4 rounded-2xl bg-slate-950 border border-white/5 text-xs text-slate-400 flex items-start gap-3">
        <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong className="text-slate-300">Academic Prototype Notice:</strong> Runtime detection currently uses prototype telemetry. Actual device runtime telemetry is not yet connected.
        </p>
      </div>
    </div>
  );
};
