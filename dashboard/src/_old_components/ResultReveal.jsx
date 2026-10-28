import React from 'react';
import { CheckCircle2, AlertTriangle, ShieldAlert, RotateCcw } from 'lucide-react';

export const ResultReveal = ({ data, onReset }) => {
  if (!data || !data.risk_analysis) return null;

  const category = (data.risk_analysis.risk_category || 'LOW').toUpperCase();

  const renderContent = () => {
    switch (category) {
      case 'HIGH':
        return {
          title: 'SECURITY WARNING',
          badge: 'HIGH RISK',
          desc: 'High-risk indicators detected across static features, ML decision vectors, or telemetry rules.',
          border: 'border-rose-500/50',
          bg: 'bg-gradient-to-r from-rose-950/40 via-slate-900 to-slate-950',
          textColor: 'text-rose-400',
          badgeClass: 'pill-high',
          icon: ShieldAlert,
          shadow: 'shadow-[0_0_50px_rgba(244,63,94,0.25)]'
        };
      case 'MEDIUM':
        return {
          title: 'ANALYSIS COMPLETE',
          badge: 'MEDIUM RISK',
          desc: 'Moderate risk indicators detected. Elevated permission profile or component vulnerability signals observed.',
          border: 'border-amber-500/50',
          bg: 'bg-gradient-to-r from-amber-950/40 via-slate-900 to-slate-950',
          textColor: 'text-amber-400',
          badgeClass: 'pill-medium',
          icon: AlertTriangle,
          shadow: 'shadow-[0_0_50px_rgba(245,158,11,0.25)]'
        };
      default: // LOW
        return {
          title: 'ANALYSIS COMPLETE',
          badge: 'LOW RISK',
          desc: 'Low risk based on available signals across static analysis, ML models, CVE lookups, and HIDS rules.',
          border: 'border-emerald-500/50',
          bg: 'bg-gradient-to-r from-emerald-950/40 via-slate-900 to-slate-950',
          textColor: 'text-emerald-400',
          badgeClass: 'pill-low',
          icon: CheckCircle2,
          shadow: 'shadow-[0_0_50px_rgba(16,185,129,0.25)]'
        };
    }
  };

  const config = renderContent();
  const IconComponent = config.icon;

  return (
    <div className={`saas-card p-8 md:p-10 mb-12 border ${config.border} ${config.bg} ${config.shadow} transition-all duration-700 animate-fade-in`}>
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center gap-6">
          <div className={`w-16 h-16 rounded-2xl bg-slate-900 border border-white/10 flex items-center justify-center ${config.textColor} shrink-0`}>
            <IconComponent className="w-9 h-9 animate-pulse" />
          </div>

          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h3 className="text-xl md:text-2xl font-black text-white tracking-tight">
                {config.title}
              </h3>
              <span className={`status-pill ${config.badgeClass} font-mono text-xs`}>
                {config.badge}
              </span>
            </div>
            <p className="text-xs md:text-sm text-slate-300 mt-1.5 max-w-2xl leading-relaxed">
              {config.desc}
            </p>
          </div>
        </div>

        {/* Analyze Another APK Reset Button */}
        <button
          onClick={onReset}
          className="px-6 py-3 rounded-2xl bg-slate-800 hover:bg-slate-700 border border-white/10 text-slate-200 text-xs font-extrabold transition-all flex items-center justify-center gap-2.5 shrink-0 shadow-lg hover:text-cyan-300"
        >
          <RotateCcw className="w-4 h-4 text-cyan-400" />
          <span>Analyze Another APK</span>
        </button>
      </div>
    </div>
  );
};
