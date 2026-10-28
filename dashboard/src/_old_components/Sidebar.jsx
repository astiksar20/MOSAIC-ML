import React from 'react';
import { 
  ShieldAlert, 
  LayoutDashboard, 
  FileSearch, 
  Cpu, 
  Database, 
  Activity, 
  Zap, 
  Settings, 
  Info,
  ChevronRight
} from 'lucide-react';

export const Sidebar = ({ activeTab, setActiveTab, onOpenAbout, onOpenSettings }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'apk', label: 'APK Analysis', icon: FileSearch },
    { id: 'ml', label: 'ML Detection', icon: Cpu },
    { id: 'cve', label: 'CVE / NVD', icon: Database },
    { id: 'hids', label: 'HIDS Engine', icon: Activity },
    { id: 'risk', label: 'Risk Analysis', icon: Zap },
  ];

  const handleNavClick = (id) => {
    setActiveTab(id);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <aside className="w-64 bg-[#090d16] border-r border-white/5 flex flex-col justify-between p-4 sticky top-0 h-screen z-30 shrink-0">
      <div>
        {/* Brand Logo */}
        <div className="flex items-center gap-3 px-3 py-4 mb-6 border-b border-white/5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <ShieldAlert className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              MOSAIC-ML
            </h1>
            <p className="text-[10px] font-medium tracking-wider uppercase text-cyan-400">
              Cyber Risk Engine
            </p>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="space-y-1">
          <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
            Analysis Modules
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 shadow-sm shadow-cyan-500/10'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
                  <span>{item.label}</span>
                </div>
                {isActive && <ChevronRight className="w-3.5 h-3.5 text-cyan-400" />}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Nav Controls */}
      <div className="pt-4 border-t border-white/5 space-y-1">
        <button
          onClick={onOpenSettings}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-white/5 transition-colors"
        >
          <Settings className="w-4 h-4 text-slate-500" />
          <span>Settings</span>
        </button>

        <button
          onClick={onOpenAbout}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-white/5 transition-colors"
        >
          <Info className="w-4 h-4 text-slate-500" />
          <span>About Project</span>
        </button>

        {/* Academic Version Tag */}
        <div className="mt-3 px-3 py-2.5 rounded-xl bg-slate-900/80 border border-white/5 text-[11px] text-slate-500">
          <div className="flex justify-between items-center mb-1">
            <span className="font-semibold text-slate-400">Framework</span>
            <span className="text-[10px] text-cyan-400 font-mono">v1.0.0</span>
          </div>
          <p className="text-[10px] text-slate-500 leading-tight">
            FastAPI • Random Forest • NVD • HIDS Engine
          </p>
        </div>
      </div>
    </aside>
  );
};
