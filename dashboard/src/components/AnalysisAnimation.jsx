import React, { useState, useEffect } from 'react';
import { Shield, Cpu, Database, Activity, Zap, CheckCircle2, Lock } from 'lucide-react';

export const AnalysisAnimation = ({ fileName }) => {
  const stages = [
    { label: "SCANNING APK", desc: "Parsing AndroidManifest.xml and binary bytecode structures...", icon: Shield },
    { label: "EXTRACTING COMPONENTS", desc: "Gathering declared permissions, activities, services, receivers, and providers...", icon: Lock },
    { label: "BUILDING FEATURE VECTOR", desc: "Mapping extracted attributes into 100,000-dimensional MH-100K feature space...", icon: Cpu },
    { label: "RUNNING ML CLASSIFIER", desc: "Executing Random Forest decision trees for malware probability estimation...", icon: Cpu },
    { label: "CHECKING CVE/NVD INTELLIGENCE", desc: "Querying National Vulnerability Database API for known component flaws...", icon: Database },
    { label: "ANALYZING HIDS SIGNALS", desc: "Evaluating Isolation Forest behavioral anomalies & pattern rule alerts...", icon: Activity },
    { label: "CALCULATING RISK", desc: "Synthesizing multi-signal weights into MOSAIC-ML aggregate score...", icon: Zap }
  ];

  const [currentStage, setCurrentStage] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStage((prev) => (prev < stages.length - 1 ? prev + 1 : prev));
    }, 1200);
    return () => clearInterval(interval);
  }, [stages.length]);

  const CurrentIcon = stages[currentStage].icon;

  return (
    <div className="saas-card p-10 md:p-16 mb-12 relative overflow-hidden border-cyan-500/30 text-center shadow-2xl">
      {/* Animated Scanning Line */}
      <div className="scan-line-anim" />

      {/* Floating particles simulation */}
      <div className="absolute top-10 left-10 w-2 h-2 rounded-full bg-cyan-400 animate-particle" />
      <div className="absolute bottom-12 right-16 w-3 h-3 rounded-full bg-violet-400 animate-particle" style={{ animationDelay: '1s' }} />
      <div className="absolute top-20 right-24 w-2 h-2 rounded-full bg-blue-400 animate-particle" style={{ animationDelay: '2s' }} />

      <div className="max-w-2xl mx-auto space-y-8 relative z-10">
        {/* Rotating Security Shield Centerpiece */}
        <div className="relative w-28 h-28 mx-auto flex items-center justify-center">
          {/* Outer Rotating Radar Ring */}
          <div className="absolute inset-0 rounded-full border-2 border-dashed border-cyan-400/40 animate-radar" />
          <div className="absolute inset-2 rounded-full border border-violet-500/30 animate-ping opacity-30" />

          {/* Inner Glowing Icon */}
          <div className="w-20 h-20 rounded-2xl bg-slate-900 border border-cyan-500/50 flex items-center justify-center text-cyan-400 shadow-[0_0_30px_rgba(6,182,212,0.3)]">
            <CurrentIcon className="w-10 h-10 animate-pulse" />
          </div>
        </div>

        {/* Status Text & File Indicator */}
        <div className="space-y-2">
          <span className="text-xs font-mono uppercase tracking-widest text-cyan-400 font-bold px-3 py-1 rounded-full bg-cyan-950/50 border border-cyan-500/30">
            {stages[currentStage].label}
          </span>
          <h3 className="text-xl md:text-2xl font-extrabold text-white tracking-tight mt-2">
            Inspecting Package: <span className="text-cyan-300 font-mono break-word-all">{fileName || 'APK File'}</span>
          </h3>
          <p className="text-xs md:text-sm text-slate-400 font-mono max-w-lg mx-auto leading-relaxed">
            {stages[currentStage].desc}
          </p>
        </div>

        {/* Stage Stepper Pipeline */}
        <div className="grid grid-cols-7 gap-1 pt-4 max-w-xl mx-auto">
          {stages.map((st, idx) => (
            <div key={idx} className="flex flex-col items-center gap-1.5">
              <div
                className={`w-full h-1.5 rounded-full transition-all duration-500 ${
                  idx <= currentStage
                    ? 'bg-gradient-to-r from-cyan-400 to-blue-500 shadow-[0_0_10px_#06b6d4]'
                    : 'bg-slate-800'
                }`}
              />
              <span className={`text-[9px] font-mono font-semibold ${idx <= currentStage ? 'text-cyan-300' : 'text-slate-600'}`}>
                0{idx + 1}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
