import React from 'react';
import { Search, UploadCloud, CheckSquare, Download, ShieldCheck, Database } from 'lucide-react';

interface NavbarProps {
  activeTab: 'search' | 'upload' | 'verification' | 'export';
  setActiveTab: (tab: 'search' | 'upload' | 'verification' | 'export') => void;
  totalLinesCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, totalLinesCount }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* App Brand Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-blue-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg text-white tracking-wide">
                  Sri Lanka Customs Tariff
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 font-mono border border-indigo-500/20">
                  HS 2022
                </span>
              </div>
              <p className="text-xs text-slate-400">Digitized Import Schedule (Chapters 1–97)</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center gap-1 bg-slate-950/60 p-1.5 rounded-xl border border-slate-800/80">
            <button
              onClick={() => setActiveTab('search')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'search'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Search className="w-4 h-4" />
              <span>Search & Browse</span>
            </button>

            <button
              onClick={() => setActiveTab('verification')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'verification'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <CheckSquare className="w-4 h-4" />
              <span>Verification Studio</span>
            </button>

            <button
              onClick={() => setActiveTab('upload')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'upload'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <UploadCloud className="w-4 h-4" />
              <span>PDF Ingestion</span>
            </button>

            <button
              onClick={() => setActiveTab('export')}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === 'export'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Download className="w-4 h-4" />
              <span>Export</span>
            </button>
          </nav>

          {/* Database Counter Badge */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-slate-950/80 rounded-lg border border-slate-800 text-xs text-slate-300">
            <Database className="w-3.5 h-3.5 text-indigo-400" />
            <span>Indexed Lines:</span>
            <span className="font-bold text-white font-mono">{totalLinesCount.toLocaleString()}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
