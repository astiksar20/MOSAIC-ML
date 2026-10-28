import React from 'react';
import { ShieldAlert, RefreshCw } from 'lucide-react';

export const Header = ({ isOnline, onCheckHealth, isCheckingHealth }) => {
  return (
    <header className="w-full py-6 mb-8 border-b border-white/5 bg-[#060913]/90 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-[1440px] mx-auto px-6 md:px-12 lg:px-16 flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Left Brand & Title */}
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-violet-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 shrink-0">
            <ShieldAlert className="w-7 h-7 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-black text-white tracking-tight">
                MOSAIC-ML
              </h1>
            </div>
            <p className="text-xs font-medium text-slate-400 mt-0.5">
              Android Vulnerability & Intrusion Risk Analyzer
            </p>
          </div>
        </div>

        {/* Subtitle Tech Sequence */}
        <div className="hidden xl:flex items-center gap-2 text-xs font-mono text-slate-400 bg-slate-900/60 px-4 py-2 rounded-xl border border-white/5">
          <span>Static Analysis</span>
          <span className="text-cyan-500">•</span>
          <span>Machine Learning</span>
          <span className="text-cyan-500">•</span>
          <span>CVE/NVD Intelligence</span>
          <span className="text-cyan-500">•</span>
          <span>HIDS</span>
        </div>

        {/* Right Status Badge */}
        <div className="flex items-center gap-3 self-start md:self-auto">
          <div className="flex items-center gap-2.5 px-4 py-2 rounded-full bg-slate-900/90 border border-white/10 text-xs shadow-inner">
            <span className="relative flex h-2.5 w-2.5">
              {isOnline ? (
                <>
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500 shadow-[0_0_10px_#10b981]"></span>
                </>
              ) : (
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500 shadow-[0_0_10px_#f43f5e]"></span>
              )}
            </span>
            <span className={`font-bold tracking-wider ${isOnline ? 'text-emerald-400' : 'text-rose-400'}`}>
              {isOnline ? 'API ONLINE' : 'API OFFLINE'}
            </span>

            <button
              onClick={onCheckHealth}
              disabled={isCheckingHealth}
              title="Refresh API Status"
              className="ml-1 text-slate-400 hover:text-cyan-400 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isCheckingHealth ? 'animate-spin text-cyan-400' : ''}`} />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
