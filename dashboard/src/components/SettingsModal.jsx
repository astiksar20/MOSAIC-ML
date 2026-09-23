import React from 'react';
import { X, Server, Sliders, Shield, RefreshCw } from 'lucide-react';

export const SettingsModal = ({ isOpen, onClose, onCheckHealth }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fade-in">
      <div className="glass-card w-full max-w-lg p-6 rounded-2xl border-cyan-500/30 relative shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-white/5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <Sliders className="w-4 h-4" />
            </div>
            <h3 className="text-lg font-bold text-white">System Settings</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="py-6 space-y-5">
          {/* Backend Connection */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-2">
              <Server className="w-3.5 h-3.5 text-cyan-400" />
              FastAPI Endpoint Target
            </label>
            <input
              type="text"
              readOnly
              value="http://127.0.0.1:8000"
              className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2.5 text-xs text-cyan-300 font-mono focus:outline-none"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Communicates with POST /analyze-apk multipart upload endpoint.
            </p>
          </div>

          {/* Proxy Mode */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-slate-300">Vite Dev Proxy</span>
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono text-[10px]">Active (/api)</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Requests to `/api` are automatically proxied to `http://127.0.0.1:8000` to prevent CORS restrictions.
            </p>
          </div>
        </div>

        <div className="pt-4 border-t border-white/5 flex justify-between items-center">
          <button
            onClick={() => {
              onCheckHealth();
              onClose();
            }}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors flex items-center gap-2"
          >
            <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
            <span>Test Connection</span>
          </button>

          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
