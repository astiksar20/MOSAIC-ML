import React, { useState } from 'react';
import { FileSearch, ShieldAlert, Layers, Server, Radio, Database, ChevronDown, ChevronUp, Search, AlertTriangle } from 'lucide-react';

export const ApkStaticAnalysis = ({ data }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedSection, setExpandedSection] = useState('permissions');

  if (!data || !data.apk_analysis) return null;

  const { apk_analysis } = data;
  const {
    package_name = 'N/A',
    permissions = [],
    activities = [],
    services = [],
    receivers = [],
    providers = []
  } = apk_analysis;

  const isSensitivePermission = (perm) => {
    const dangerousKeywords = [
      'SMS', 'CALL', 'CAMERA', 'LOCATION', 'CONTACTS', 'STORAGE',
      'RECORD_AUDIO', 'READ_PHONE_STATE', 'SYSTEM_ALERT_WINDOW', 'RECEIVE_BOOT_COMPLETED'
    ];
    return dangerousKeywords.some(keyword => perm.toUpperCase().includes(keyword));
  };

  const filterList = (list) => {
    if (!searchTerm) return list;
    return list.filter(item => item.toLowerCase().includes(searchTerm.toLowerCase()));
  };

  const toggleSection = (sec) => {
    setExpandedSection(prev => (prev === sec ? null : sec));
  };

  const categories = [
    { id: 'permissions', label: 'Permissions', items: permissions, icon: ShieldAlert, color: 'text-rose-400', bg: 'bg-rose-500/10 border-rose-500/20' },
    { id: 'activities', label: 'Activities', items: activities, icon: Layers, color: 'text-cyan-400', bg: 'bg-cyan-500/10 border-cyan-500/20' },
    { id: 'services', label: 'Services', items: services, icon: Server, color: 'text-violet-400', bg: 'bg-violet-500/10 border-violet-500/20' },
    { id: 'receivers', label: 'Broadcast Receivers', items: receivers, icon: Radio, color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/20' },
    { id: 'providers', label: 'Content Providers', items: providers, icon: Database, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' }
  ];

  return (
    <div className="saas-card p-8 md:p-10 mb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pb-6 border-b border-white/5">
        <div>
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-bold uppercase tracking-wider mb-2">
            <FileSearch className="w-4 h-4" />
            <span>Static Manifest Component Inspection</span>
          </div>
          <h3 className="text-2xl font-bold text-white tracking-tight">
            APK Static Analysis
          </h3>
          <p className="text-xs md:text-sm text-slate-400 mt-1">
            Package name, permission declarations, and component structure extracted from AndroidManifest.xml.
          </p>
        </div>

        {/* Filter Input */}
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search permissions or classes..."
            className="w-full bg-slate-900 border border-white/10 rounded-2xl pl-10 pr-4 py-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
          />
        </div>
      </div>

      {/* Target Package Banner */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-white/10 mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest font-mono">
            Package Name
          </span>
          <h4 className="text-base md:text-lg font-extrabold text-cyan-300 font-mono break-word-all mt-1">
            {package_name}
          </h4>
        </div>

        <div className="px-4 py-2 rounded-xl bg-slate-950 border border-white/5 text-xs font-mono text-slate-300 shrink-0">
          Total Declared: <strong className="text-white font-bold">{permissions.length + activities.length + services.length + receivers.length + providers.length}</strong>
        </div>
      </div>

      {/* Spacious Component Statistic Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
        {categories.map((cat) => {
          const IconComp = cat.icon;
          const isSelected = expandedSection === cat.id;

          return (
            <button
              key={cat.id}
              onClick={() => toggleSection(cat.id)}
              className={`p-5 rounded-2xl border text-left transition-all duration-200 ${
                isSelected
                  ? 'bg-slate-900 border-cyan-500/40 shadow-lg shadow-cyan-500/10'
                  : 'bg-slate-900/50 border-white/5 hover:border-white/10'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center border ${cat.bg} ${cat.color}`}>
                  <IconComp className="w-4 h-4" />
                </div>
                <span className="text-xs font-mono text-slate-500">
                  {isSelected ? <ChevronUp className="w-4 h-4 text-cyan-400" /> : <ChevronDown className="w-4 h-4" />}
                </span>
              </div>
              <h5 className="text-2xl font-black text-white font-mono">
                {cat.items.length}
              </h5>
              <p className="text-[11px] font-semibold text-slate-400 mt-1 truncate">
                {cat.label}
              </p>
            </button>
          );
        })}
      </div>

      {/* Expandable Lists Container */}
      {categories.map((cat) => {
        if (expandedSection !== cat.id) return null;
        const filtered = filterList(cat.items);

        return (
          <div key={cat.id} className="p-6 rounded-2xl bg-slate-900/60 border border-white/10 animate-fade-in space-y-4">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <h4 className="text-sm font-bold text-slate-200 uppercase tracking-wider font-mono flex items-center gap-2">
                <span>{cat.label} List ({filtered.length})</span>
              </h4>
              {searchTerm && (
                <span className="text-xs text-cyan-400 font-mono">Filtered by: "{searchTerm}"</span>
              )}
            </div>

            {filtered.length === 0 ? (
              <p className="text-xs text-slate-500 italic font-mono py-4">
                No matching entries found.
              </p>
            ) : (
              <div className="space-y-2 max-h-80 overflow-y-auto pr-2">
                {filtered.map((item, idx) => {
                  const sensitive = cat.id === 'permissions' && isSensitivePermission(item);

                  return (
                    <div
                      key={idx}
                      className={`p-3 rounded-xl text-xs font-mono break-word-all flex items-start gap-3 border ${
                        sensitive
                          ? 'bg-rose-950/20 border-rose-500/30 text-rose-300'
                          : 'bg-slate-950/80 border-white/5 text-slate-300'
                      }`}
                    >
                      {sensitive ? (
                        <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                      ) : (
                        <span className="w-2 h-2 rounded-full bg-cyan-400 shrink-0 mt-1.5" />
                      )}
                      <span className="flex-1 leading-relaxed">{item}</span>
                      {sensitive && (
                        <span className="status-pill pill-high text-[9px] shrink-0">
                          SENSITIVE PERMISSION
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
