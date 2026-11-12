import React from 'react';
import { ShieldCheck, Moon, Sun, Database, History, MessageSquare, LogOut, User as UserIcon, PlusCircle } from 'lucide-react';
import { HealthStatus, User } from '../types';

interface NavbarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  darkMode: boolean;
  setDarkMode: (val: boolean | ((prev: boolean) => boolean)) => void;
  health: HealthStatus | null;
  currentUser?: User | null;
  onLogin?: () => void;
  onLogout?: () => void;
  onNewDeal?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  darkMode,
  setDarkMode,
  health,
  currentUser,
  onLogin,
  onLogout,
  onNewDeal,
}) => {
  return (
    <header className="sticky top-0 z-40 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setCurrentTab('deals')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-800 to-blue-500 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-xl tracking-tight text-blue-800 dark:text-white">
                  Deal<span className="text-blue-500">Check</span>
                </span>
                <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-blue-50 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200 rounded-full border border-blue-200 dark:border-blue-700">
                  Sandbox Active
                </span>
              </div>
              <p className="hidden sm:block text-[11px] text-slate-500 dark:text-slate-400 font-medium">
                PayPal AI Hackathon • Live Buyer Protection & Collaborative Deal Rooms
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center space-x-1 sm:space-x-2">
            {/* Primary Deal Rooms tab */}
            <button
              onClick={() => setCurrentTab('deals')}
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
                currentTab === 'deals'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              <span>Deal Rooms</span>
            </button>

            {/* Quick Action: New Deal */}
            {onNewDeal && (
              <button
                onClick={onNewDeal}
                className="hidden sm:flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs sm:text-sm font-semibold bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-all border border-blue-200 dark:border-blue-700"
              >
                <PlusCircle className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <span>+ New Deal</span>
              </button>
            )}

            <button
              onClick={() => setCurrentTab('history')}
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
                currentTab === 'history'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              <History className="w-4 h-4" />
              <span className="hidden md:inline">Audit History</span>
              <span className="md:hidden">History</span>
            </button>

            <button
              onClick={() => setCurrentTab('model')}
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
                currentTab === 'model'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              <Database className="w-4 h-4" />
              <span className="hidden lg:inline">Model Card & Metrics</span>
              <span className="lg:hidden hidden sm:inline">Model</span>
            </button>

            {/* Dark Mode Toggle */}
            <button
              onClick={() => setDarkMode(prev => !prev)}
              aria-label="Toggle Dark Mode"
              className="p-2 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
            >
              {darkMode ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5 text-slate-600" />}
            </button>

            {/* Auth: User menu or Login button */}
            {currentUser ? (
              <div className="flex items-center gap-2 ml-1">
                <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 rounded-lg">
                  <UserIcon className="w-4 h-4 text-blue-500" />
                  <span className="text-xs font-medium text-slate-700 dark:text-slate-300 max-w-[90px] truncate">
                    {currentUser.name}
                  </span>
                </div>
                <button
                  onClick={onLogout}
                  className="p-2 text-slate-500 hover:text-red-500 dark:text-slate-400 dark:hover:text-red-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                  aria-label="Sign out"
                  title="Sign out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={onLogin}
                className="ml-1 px-3 py-2 text-xs sm:text-sm font-semibold text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg transition-colors"
              >
                Sign In
              </button>
            )}
          </nav>
        </div>
      </div>

      {/* Subheader status bar */}
      <div className="hidden sm:flex border-t border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/50 px-4 sm:px-6 lg:px-8 py-1.5 text-[11px] items-center justify-between text-slate-500 dark:text-slate-400">
        <div className="flex items-center space-x-4">
          <span className="flex items-center space-x-1.5">
            <span className={`w-2 h-2 rounded-full ${health?.models_loaded !== false ? 'bg-emerald-500' : 'bg-red-500 animate-pulse'}`} />
            <span>Local Models: <strong>{health?.models_loaded !== false ? 'Ready (A + B)' : 'Not Loaded'}</strong></span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>PayPal Sandbox: <strong>Ready (Orders v2 {health?.paypal_live ? '• Live API' : '• Active'})</strong></span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>Encrypted at Rest: <strong>Fernet AES-128</strong></span>
          </span>
        </div>
        <div className="text-[11px] font-medium text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded border border-amber-200 dark:border-amber-900/50">
          Sandbox checkout, no real money.
        </div>
      </div>
    </header>
  );
};
