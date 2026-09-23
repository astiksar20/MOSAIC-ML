import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle } from 'lucide-react';

export const Recommendation = ({ data }) => {
  if (!data || !data.risk_analysis) return null;

  const { risk_analysis } = data;
  const {
    risk_category = 'LOW',
    recommendation = 'Monitor application'
  } = risk_analysis;

  const getStyle = (cat) => {
    switch ((cat || '').toUpperCase()) {
      case 'HIGH':
        return {
          border: 'border-rose-500/40',
          bg: 'bg-gradient-to-r from-rose-950/30 via-slate-900 to-slate-950',
          badgeClass: 'pill-high',
          iconColor: 'text-rose-400',
          iconBg: 'bg-rose-500/10 border-rose-500/20',
          icon: ShieldAlert
        };
      case 'MEDIUM':
        return {
          border: 'border-amber-500/40',
          bg: 'bg-gradient-to-r from-amber-950/30 via-slate-900 to-slate-950',
          badgeClass: 'pill-medium',
          iconColor: 'text-amber-400',
          iconBg: 'bg-amber-500/10 border-amber-500/20',
          icon: AlertTriangle
        };
      default: // LOW
        return {
          border: 'border-emerald-500/40',
          bg: 'bg-gradient-to-r from-emerald-950/30 via-slate-900 to-slate-950',
          badgeClass: 'pill-low',
          iconColor: 'text-emerald-400',
          iconBg: 'bg-emerald-500/10 border-emerald-500/20',
          icon: ShieldCheck
        };
    }
  };

  const style = getStyle(risk_category);
  const IconComp = style.icon;

  return (
    <div className={`saas-card p-8 md:p-12 mb-12 border ${style.border} ${style.bg} relative overflow-hidden`}>
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-start gap-6">
          <div className={`w-14 h-14 rounded-2xl border flex items-center justify-center ${style.iconBg} ${style.iconColor} shrink-0 mt-1`}>
            <IconComp className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-3 flex-wrap">
              <h3 className="text-2xl font-bold text-white tracking-tight">
                Recommended Action
              </h3>
              <span className={`status-pill ${style.badgeClass} font-mono text-xs`}>
                {risk_category} RISK
              </span>
            </div>

            <h4 className="text-xl font-extrabold text-cyan-300 font-mono capitalize pt-1">
              "{recommendation}"
            </h4>

            <p className="text-xs md:text-sm text-slate-300 max-w-2xl leading-relaxed">
              Based on synthesized static permissions, Random Forest ML prediction, NVD vulnerability lookups, and HIDS telemetry, the engine advises: <strong className="text-white">{recommendation}</strong>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
