import React, { useState } from 'react';
import { 
  FileSearch, 
  ShieldAlert, 
  Radio, 
  Layers, 
  Server, 
  Database, 
  ChevronDown, 
  ChevronUp, 
  Search, 
  Filter,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';

export const ApkAnalysis = ({ data }) => {
  const [activeTab, setActiveTab] = useState('permissions');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedSections, setExpandedSections] = useState({
    permissions: true,
    activities: true,
    services: false,
    receivers: false,
    providers: false
  });

  if (!data) return null;

  const { apk_analysis } = data;
  if (!apk_analysis) return null;

  const {
    package_name = 'N/A',
    permissions = [],
    activities = [],
    services = [],
    receivers = [],
    providers = []
  } = apk_analysis;

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  // Known dangerous permissions for highlight
  const isDangerousPermission = (perm) => {
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

  const renderComponentList = (title, items, icon, colorClass, sectionKey) => {
    const isExpanded = expandedSections[sectionKey];
    const filteredItems = filterList(items);

    const IconComponent = icon;

    return (
      <div className="border border-white/5 rounded-xl bg-slate-900/50 overflow-hidden transition-all duration-200">
        {/* Accordion Header */}
        <button
          onClick={() => toggleSection(sectionKey)}
          className="w-full flex items-center justify-between p-4 text-left hover:bg-white/5 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${colorClass}`}>
              <IconComponent className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-200 tracking-tight flex items-center gap-2">
                {title}
                <span className="px-2 py-0.5 rounded-full bg-slate-800 border border-white/10 text-[10px] font-mono text-cyan-400">
                  {items.length}
                </span>
              </h4>
              <p className="text-[11px] text-slate-400 mt-0.5">
                {items.length === 0 ? 'None declared in AndroidManifest' : `Extracted ${title.toLowerCase()}`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-slate-400">
            <span className="text-xs font-mono">{isExpanded ? 'Hide' : 'Expand'}</span>
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </button>

        {/* Accordion Body */}
        {isExpanded && (
          <div className="p-4 pt-0 border-t border-white/5">
            {items.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-3 font-mono">
                No {title.toLowerCase()} declared in manifest.
              </p>
            ) : (
              <div className="mt-3 space-y-1.5 max-h-60 overflow-y-auto pr-1">
                {filteredItems.map((item, idx) => {
                  const dangerous = sectionKey === 'permissions' && isDangerousPermission(item);
                  return (
                    <div
                      key={idx}
                      className={`p-2.5 rounded-lg text-xs font-mono break-all flex items-start gap-2 border transition-colors ${
                        dangerous
                          ? 'bg-rose-950/20 border-rose-500/20 text-rose-300'
                          : 'bg-slate-950/60 border-white/5 text-slate-300 hover:border-white/10'
                      }`}
                    >
                      {dangerous ? (
                        <AlertTriangle className="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" />
                      ) : (
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400/60 shrink-0 mt-1.5" />
                      )}
                      <span className="flex-1">{item}</span>
                      {dangerous && (
                        <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 font-semibold shrink-0">
                          Sensitive
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div id="apk" className="glass-card p-6 md:p-8 mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 pb-6 border-b border-white/5">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <FileSearch className="w-3.5 h-3.5" />
            <span>Static Manifest & Component Inspection</span>
          </div>
          <h3 className="text-xl font-bold text-white tracking-tight">
            APK Static Analysis
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Package structure, declared permissions, components, and security boundary indicators.
          </p>
        </div>

        {/* Search bar inside APK components */}
        <div className="relative w-full md:w-64">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Filter permissions/components..."
            className="w-full bg-slate-900 border border-white/10 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
          />
        </div>
      </div>

      {/* Package Header Card */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-slate-900 to-slate-950 border border-white/10 mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
            Target Package Identifier
          </span>
          <h4 className="text-base font-extrabold text-cyan-300 font-mono break-all mt-0.5">
            {package_name}
          </h4>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
          <div className="px-3 py-1.5 rounded-lg bg-slate-900 border border-white/5">
            Total Components: <span className="text-white font-bold">{activities.length + services.length + receivers.length + providers.length}</span>
          </div>
          <div className="px-3 py-1.5 rounded-lg bg-slate-900 border border-white/5">
            Permissions: <span className="text-cyan-400 font-bold">{permissions.length}</span>
          </div>
        </div>
      </div>

      {/* Collapsible Component Lists Grid */}
      <div className="space-y-4">
        {renderComponentList(
          'Permissions',
          permissions,
          ShieldAlert,
          'bg-rose-500/10 text-rose-400 border border-rose-500/20',
          'permissions'
        )}

        {renderComponentList(
          'Activities',
          activities,
          Layers,
          'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20',
          'activities'
        )}

        {renderComponentList(
          'Services',
          services,
          Server,
          'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20',
          'services'
        )}

        {renderComponentList(
          'Broadcast Receivers',
          receivers,
          Radio,
          'bg-amber-500/10 text-amber-400 border border-amber-500/20',
          'receivers'
        )}

        {renderComponentList(
          'Content Providers',
          providers,
          Database,
          'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
          'providers'
        )}
      </div>
    </div>
  );
};
