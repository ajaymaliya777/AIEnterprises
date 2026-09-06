import React from 'react';
import {
  LayoutDashboard,
  Files,
  MessageSquare,
  SlidersHorizontal,
  BarChart3,
  Activity,
  ChevronRight,
  Brain,
  ShieldCheck
} from 'lucide-react';

export type TabType = 'dashboard' | 'documents' | 'chat' | 'debug' | 'evaluation' | 'observability';

interface SidebarProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  documentCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  documentCount
}) => {
  const menuItems = [
    {
      id: 'dashboard' as TabType,
      label: 'Executive Dashboard',
      icon: LayoutDashboard,
      badge: null
    },
    {
      id: 'documents' as TabType,
      label: 'Document Intelligence',
      icon: Files,
      badge: documentCount > 0 ? documentCount : null
    },
    {
      id: 'chat' as TabType,
      label: 'Enterprise AI Chat',
      icon: MessageSquare,
      badge: 'Grounded'
    },
    {
      id: 'debug' as TabType,
      label: 'Retrieval Debugger',
      icon: SlidersHorizontal,
      badge: 'Hybrid'
    },
    {
      id: 'evaluation' as TabType,
      label: 'RAGAS Benchmarks',
      icon: BarChart3,
      badge: 'v1.0'
    },
    {
      id: 'observability' as TabType,
      label: 'Langfuse Observability',
      icon: Activity,
      badge: 'Live'
    },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col flex-shrink-0 h-screen sticky top-0">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20 text-white">
          <Brain className="w-6 h-6" />
        </div>
        <div>
          <h1 className="font-bold text-base text-white tracking-tight flex items-center gap-1.5">
            EnterpriseDoc <span className="text-xs px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-400 font-mono">AI</span>
          </h1>
          <p className="text-xs text-slate-400">Document Intelligence & RAG</p>
        </div>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
          Core Platform
        </div>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-sky-600 text-white shadow-md shadow-sky-600/30'
                  : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
              <span className="flex-1 text-left">{item.label}</span>
              {item.badge !== null && (
                <span
                  className={`text-[11px] px-2 py-0.5 rounded-full font-mono font-medium ${
                    isActive
                      ? 'bg-white/20 text-white'
                      : 'bg-slate-800 text-slate-400 border border-slate-700'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Bottom Status Card */}
      <div className="p-4 border-t border-slate-800">
        <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-xs text-slate-400 flex items-center gap-2.5">
          <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <div className="leading-tight">
            <p className="text-slate-200 font-medium">Enterprise Grounding</p>
            <p className="text-[11px] text-slate-400">Anti-hallucination enabled</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
