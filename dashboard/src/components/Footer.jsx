import React from 'react';
import { ShieldAlert } from 'lucide-react';

export const Footer = () => {
  return (
    <footer className="w-full py-12 border-t border-white/5 bg-[#060913]">
      <div className="max-w-[1440px] mx-auto px-6 md:px-12 lg:px-16 flex flex-col sm:flex-row items-center justify-between gap-4 text-center sm:text-left">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-200">MOSAIC-ML</h4>
            <p className="text-xs text-slate-400">
              Android Vulnerability & Intrusion Risk Analyzer
            </p>
          </div>
        </div>

        <div className="text-xs font-mono text-slate-400">
          Academic Prototype Evaluation System
        </div>
      </div>
    </footer>
  );
};
