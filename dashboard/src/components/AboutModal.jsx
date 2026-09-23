import React from 'react';
import { X, ShieldAlert, Cpu, Database, Activity, Zap, CheckCircle2 } from 'lucide-react';

export const AboutModal = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fade-in">
      <div className="glass-card w-full max-w-2xl p-6 md:p-8 rounded-2xl border-cyan-500/30 relative shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between pb-4 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <ShieldAlert className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-extrabold text-white">About MOSAIC-ML</h3>
              <p className="text-xs text-cyan-400 font-mono">Academic Android Vulnerability & Risk Framework</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="py-6 space-y-6 text-xs text-slate-300 leading-relaxed">
          <p>
            <strong>MOSAIC-ML</strong> is a multi-stage cybersecurity research framework engineered for static APK analysis, 
            machine learning classification over high-dimensional feature vectors, vulnerability intelligence lookup, 
            and runtime intrusion anomaly detection.
          </p>

          <div className="space-y-3">
            <h4 className="font-bold text-slate-100 uppercase tracking-wider text-[11px] text-cyan-400">
              Architecture Pipeline Flow
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono">
              <div className="p-3 rounded-xl bg-slate-900 border border-white/5 space-y-1">
                <span className="text-cyan-400 font-bold">1. APK Static Extraction</span>
                <p className="text-[11px] text-slate-400 font-sans">
                  Parses AndroidManifest.xml for permissions, activities, services, receivers, and providers.
                </p>
              </div>

              <div className="p-3 rounded-xl bg-slate-900 border border-white/5 space-y-1">
                <span className="text-cyan-400 font-bold">2. MH-100K Feature Mapping</span>
                <p className="text-[11px] text-slate-400 font-sans">
                  Maps extracted manifest components into a 100,000-dimensional sparse feature space.
                </p>
              </div>

              <div className="p-3 rounded-xl bg-slate-900 border border-white/5 space-y-1">
                <span className="text-cyan-400 font-bold">3. Random Forest ML</span>
                <p className="text-[11px] text-slate-400 font-sans">
                  Evaluates benign vs. malware probability distribution via trained decision trees.
                </p>
              </div>

              <div className="p-3 rounded-xl bg-slate-900 border border-white/5 space-y-1">
                <span className="text-cyan-400 font-bold">4. NVD CVE Intelligence</span>
                <p className="text-[11px] text-slate-400 font-sans">
                  Queries National Vulnerability Database for component string matches and CVSS metrics.
                </p>
              </div>

              <div className="p-3 rounded-xl bg-slate-900 border border-white/5 space-y-1">
                <span className="text-cyan-400 font-bold">5. HIDS Rule & Anomaly</span>
                <p className="text-[11px] text-slate-400 font-sans">
                  Evaluates rule patterns & Isolation Forest algorithm against runtime telemetry streams.
                </p>
              </div>

              <div className="p-3 rounded-xl bg-slate-900 border border-white/5 space-y-1">
                <span className="text-cyan-400 font-bold">6. Risk Engine Synthesis</span>
                <p className="text-[11px] text-slate-400 font-sans">
                  Aggregates all module signals into a unified MOSAIC-ML prototype risk index (0–100).
                </p>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-white/5 text-[11px] text-slate-400">
            <span className="text-slate-200 font-bold">Academic Integrity Statement:</span> Designed for research evaluation and security analysis. Explanations avoid definitive unverified claims of compromise while providing transparent evidence trails.
          </div>
        </div>

        <div className="pt-4 border-t border-white/5 flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
