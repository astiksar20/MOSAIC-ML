import React from 'react';
import { Database, CheckCircle2, Info } from 'lucide-react';

export const CveAnalysis = ({ data }) => {
  if (!data || !data.cve_analysis) return null;

  const { cve_analysis } = data;
  const {
    components_searched = [],
    cve_count = 0,
    cve_results = []
  } = cve_analysis;

  const getCvssStyle = (score) => {
    const num = parseFloat(score);
    if (isNaN(num)) return 'pill-low';
    if (num >= 9.0) return 'pill-high';
    if (num >= 7.0) return 'pill-high';
    if (num >= 4.0) return 'pill-medium';
    return 'pill-low';
  };

  return (
    <div className="saas-card p-8 md:p-10 mb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pb-6 border-b border-white/5">
        <div>
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-bold uppercase tracking-wider mb-2">
            <Database className="w-4 h-4" />
            <span>National Vulnerability Database Intelligence</span>
          </div>
          <h3 className="text-2xl font-bold text-white tracking-tight">
            CVE / NVD Intelligence
          </h3>
          <p className="text-xs md:text-sm text-slate-400 mt-1">
            Automated lookup of component strings against published NVD CVE vulnerability records.
          </p>
        </div>

        <div className="px-4 py-2.5 rounded-2xl bg-slate-900 border border-white/10 text-xs font-mono text-amber-300 flex items-center gap-2 self-start md:self-auto">
          <span>CVE Records Found: <strong className="text-white text-sm">{cve_count}</strong></span>
        </div>
      </div>

      {/* Searched Component Tags */}
      {components_searched.length > 0 && (
        <div className="mb-8 p-5 rounded-2xl bg-slate-900/60 border border-white/5">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2 font-mono">
            <Info className="w-4 h-4 text-cyan-400" />
            <span>Queried Component Strings ({components_searched.length})</span>
          </h4>
          <div className="flex flex-wrap gap-2">
            {components_searched.map((comp, i) => (
              <span key={i} className="px-3 py-1.5 rounded-xl bg-slate-950 border border-white/10 text-xs font-mono text-slate-300 break-word-all">
                {comp}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* CVE Results Cards or Zero-Match State */}
      {cve_count === 0 || cve_results.length === 0 ? (
        <div className="p-10 rounded-3xl bg-slate-900/40 border border-white/5 text-center flex flex-col items-center justify-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <CheckCircle2 className="w-7 h-7" />
          </div>
          <div className="max-w-md">
            <h4 className="text-lg font-bold text-slate-200">
              No matching CVE/NVD records returned.
            </h4>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed font-sans">
              No published CVE matches were returned for the queried component strings in the National Vulnerability Database.
            </p>
          </div>
          <p className="text-[11px] text-slate-500 font-mono italic">
            Note: Lack of matching CVE records is not experimental proof that the APK has no vulnerabilities.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {cve_results.map((cve, idx) => (
            <div
              key={idx}
              className="p-6 rounded-2xl bg-slate-900/70 border border-white/10 hover:border-amber-500/30 transition-all duration-200 space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/5 pb-4">
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="text-lg font-bold font-mono text-amber-400">
                    {cve.id || cve.cve_id || 'CVE-UNKNOWN'}
                  </span>
                  <span className={`status-pill ${getCvssStyle(cve.cvss_score)} font-mono text-xs`}>
                    CVSS {cve.cvss_score ?? 'N/A'}
                  </span>
                  {cve.severity && (
                    <span className="px-3 py-1 rounded-lg bg-slate-800 border border-white/10 text-xs font-mono uppercase text-slate-300">
                      {cve.severity}
                    </span>
                  )}
                </div>

                <div className="text-xs font-mono text-slate-400">
                  Searched Component: <span className="text-cyan-300 font-semibold break-word-all">{cve.component || cve.searched_component || 'N/A'}</span>
                </div>
              </div>

              {cve.cwe && (
                <div className="text-xs font-mono text-slate-400">
                  <span className="text-slate-500">CWE Classification:</span> <span className="text-slate-200">{cve.cwe}</span>
                </div>
              )}

              <p className="text-xs md:text-sm text-slate-300 leading-relaxed font-sans">
                {cve.description || 'No vulnerability description returned.'}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
