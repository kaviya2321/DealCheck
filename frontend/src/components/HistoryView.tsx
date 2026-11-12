import React, { useState, useEffect } from 'react';
import { DealData } from '../types';
import { fetchDeals, clearAllData } from '../api';
import { History, ShieldAlert, ShieldCheck, Trash2, ArrowUpRight, Search, Loader2 } from 'lucide-react';

interface HistoryViewProps {
  onSelectDeal: (deal: DealData) => void;
  onNewCheck: () => void;
}

export const HistoryView: React.FC<HistoryViewProps> = ({
  onSelectDeal,
  onNewCheck,
}) => {
  const [deals, setDeals] = useState<DealData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [verdictFilter, setVerdictFilter] = useState<'ALL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL');
  const [isClearing, setIsClearing] = useState(false);

  const loadDeals = async () => {
    setIsLoading(true);
    try {
      const data = await fetchDeals();
      setDeals(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDeals();
  }, []);

  const handleClearHistory = async () => {
    if (!window.confirm('Are you sure you want to clear all past deal records from SQLite?')) return;
    setIsClearing(true);
    try {
      await clearAllData();
      setDeals([]);
    } catch (e) {
      console.error(e);
    } finally {
      setIsClearing(false);
    }
  };

  const filtered = deals.filter(d => {
    const matchesSearch = d.item_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          d.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesVerdict = verdictFilter === 'ALL' || d.verdict === verdictFilter;
    return matchesSearch && matchesVerdict;
  });

  return (
    <div className="w-full max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <h2 className="text-2xl font-black text-slate-900 dark:text-white flex items-center space-x-2">
            <History className="w-6 h-6 text-paypal-blue" />
            <span>DealCheck History & Audit Trail</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Persisted locally in SQLite database. Total recorded deals: {deals.length}.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {deals.length > 0 && (
            <button
              disabled={isClearing}
              onClick={handleClearHistory}
              className="px-3 py-1.5 bg-red-50 hover:bg-red-100 dark:bg-red-950/40 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-900 rounded-lg text-xs font-bold flex items-center space-x-1.5 transition-colors cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear History</span>
            </button>
          )}

          <button
            onClick={onNewCheck}
            className="px-4 py-2 bg-paypal-blue hover:bg-paypal-deep text-white rounded-lg text-xs font-extrabold shadow-sm transition-all cursor-pointer"
          >
            + New Check
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search deals by item or ID..."
            className="w-full pl-9 pr-3 py-2 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-paypal-blue focus:outline-none"
          />
        </div>

        <div className="flex items-center space-x-1 bg-white dark:bg-slate-900 p-1 rounded-xl border border-slate-200 dark:border-slate-800 text-xs w-full sm:w-auto">
          {(['ALL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((filter) => (
            <button
              key={filter}
              onClick={() => setVerdictFilter(filter)}
              className={`px-3 py-1.5 rounded-lg font-bold text-xs transition-colors flex-1 sm:flex-initial ${
                verdictFilter === filter
                  ? 'bg-paypal-blue text-white shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              {filter}
            </button>
          ))}
        </div>
      </div>

      {/* Deals List */}
      {isLoading ? (
        <div className="p-12 text-center flex flex-col items-center space-y-2">
          <Loader2 className="w-8 h-8 text-paypal-blue animate-spin" />
          <p className="text-xs text-slate-400">Loading deals from SQLite...</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-soft space-y-3">
          <div className="w-12 h-12 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto text-slate-400">
            <History className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">No deals found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {deals.length === 0
              ? 'You have not checked any marketplace deals yet. Run a check to see it saved here.'
              : 'No deals matched your search filters.'}
          </p>
          <button
            onClick={onNewCheck}
            className="px-4 py-2 bg-paypal-blue text-white rounded-lg text-xs font-bold inline-block mt-2"
          >
            Check a Deal Now
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((d) => {
            const isHigh = d.verdict === 'HIGH';
            const isMed = d.verdict === 'MEDIUM';

            return (
              <div
                key={d.id}
                onClick={() => onSelectDeal(d)}
                className="p-4 bg-white dark:bg-slate-900 hover:border-paypal-blue dark:hover:border-paypal-blue border border-slate-200 dark:border-slate-800 rounded-2xl shadow-soft transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 group"
              >
                <div className="flex items-start space-x-3.5">
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 text-white font-black text-sm ${
                      isHigh ? 'bg-red-600' : isMed ? 'bg-amber-500' : 'bg-emerald-600'
                    }`}
                  >
                    {d.risk_score}
                  </div>

                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-extrabold text-sm text-slate-900 dark:text-white group-hover:text-paypal-blue transition-colors">
                        {d.item_name}
                      </span>
                      <span
                        className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                          isHigh
                            ? 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300'
                            : isMed
                            ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                            : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                        }`}
                      >
                        {d.verdict}
                      </span>
                    </div>

                    <div className="text-xs text-slate-500 dark:text-slate-400 mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">
                      <span>${d.price.toFixed(2)} {d.currency}</span>
                      <span>•</span>
                      <span className="font-mono text-[11px]">{d.id}</span>
                      <span>•</span>
                      <span>{d.created_at ? new Date(d.created_at).toLocaleDateString() : 'Recent'}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between sm:justify-end space-x-3 pt-2 sm:pt-0 border-t sm:border-0 border-slate-100 dark:border-slate-800">
                  {d.paypal_order_id && (
                    <span className="text-[10px] font-mono bg-blue-50 text-paypal-deep dark:bg-slate-800 dark:text-blue-300 px-2 py-1 rounded border border-blue-100 dark:border-slate-700">
                      PP: {d.paypal_order_id.slice(-8)}
                    </span>
                  )}

                  {d.seller_litmus_verdict && (
                    <span className={`text-[10px] font-bold uppercase px-2 py-1 rounded ${
                      d.seller_litmus_verdict === 'PASSED'
                        ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                        : d.seller_litmus_verdict === 'FAILED'
                        ? 'bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300'
                        : 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300'
                    }`}>
                      Litmus: {d.seller_litmus_verdict}
                    </span>
                  )}

                  <span className="text-slate-400 group-hover:text-paypal-blue transition-colors flex items-center text-xs font-semibold">
                    <span>Inspect</span>
                    <ArrowUpRight className="w-4 h-4 ml-0.5" />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
