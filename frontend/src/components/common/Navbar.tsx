import React from 'react';
import { Upload, Database, Cpu, CheckCircle2, AlertCircle } from 'lucide-react';
import { SystemHealth } from '../../types';

interface NavbarProps {
  health: SystemHealth | null;
  onOpenUpload: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ health, onOpenUpload }) => {
  const isOnline = health?.status === 'online';

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-10">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${isOnline ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
          <span className="text-xs font-medium text-slate-300">
            {isOnline ? 'System Operational' : 'Backend Offline'}
          </span>
        </div>

        {health && (
          <div className="hidden md:flex items-center gap-3 text-xs text-slate-400 border-l border-slate-800 pl-4">
            <div className="flex items-center gap-1.5 bg-slate-800/60 px-2.5 py-1 rounded-md">
              <Database className="w-3.5 h-3.5 text-sky-400" />
              <span>Chunks: <strong className="text-slate-200">{health.vector_store_chunks}</strong></span>
            </div>
            <div className="flex items-center gap-1.5 bg-slate-800/60 px-2.5 py-1 rounded-md">
              <Cpu className="w-3.5 h-3.5 text-indigo-400" />
              <span>Model: <strong className="text-slate-200">{health.gemini_model}</strong></span>
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={onOpenUpload}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-md shadow-sky-600/20 transition-all cursor-pointer"
        >
          <Upload className="w-4 h-4" />
          <span>Upload Document</span>
        </button>
      </div>
    </header>
  );
};
