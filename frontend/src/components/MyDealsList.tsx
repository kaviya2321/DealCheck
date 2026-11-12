import React, { useState, useEffect } from 'react';
import { DealData, User } from '../types';
import { fetchMyDeals, deleteDeal } from '../api';

interface MyDealsListProps {
  currentUser: User;
  onSelectDeal: (deal: DealData) => void;
  onNewDeal: () => void;
}

const statusColors: Record<string, string> = {
  INVITED: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  ACTIVE: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  PAYMENT_PENDING: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  COMPLETED: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  CANCELLED: 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-500',
};

const verdictColors: Record<string, string> = {
  LOW: 'text-green-600 dark:text-green-400',
  MEDIUM: 'text-amber-600 dark:text-amber-400',
  HIGH: 'text-red-600 dark:text-red-400',
};

export function MyDealsList({ currentUser, onSelectDeal, onNewDeal }: MyDealsListProps) {
  const [deals, setDeals] = useState<DealData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    fetchMyDeals()
      .then(ds => {
        // Filter to only deals user is part of
        const mine = ds.filter(d => d.buyer_id === currentUser.id || d.seller_id === currentUser.id);
        setDeals(mine);
      })
      .catch(err => setError(err.message))
      .finally(() => setIsLoading(false));
  }, [currentUser.id]);

  async function handleDelete(deal: DealData, e: React.MouseEvent) {
    e.stopPropagation();
    if (!window.confirm(`Delete the deal for "${deal.item_name}"? This cannot be undone.`)) return;
    setDeletingId(deal.id);
    try {
      await deleteDeal(deal.id);
      setDeals(prev => prev.filter(d => d.id !== deal.id));
    } catch (err) {
      alert('Failed to delete deal. Please try again.');
    } finally {
      setDeletingId(null);
    }
  }

  if (isLoading) return (
    <div className="flex items-center justify-center py-20 text-slate-400 dark:text-slate-600">
      <svg className="animate-spin w-6 h-6 mr-2" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      Loading your deals…
    </div>
  );

  if (error) return (
    <div className="text-center py-16 text-red-500 dark:text-red-400">
      <p>{error}</p>
      <button onClick={() => window.location.reload()} className="mt-3 text-sm underline">Retry</button>
    </div>
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-100">My Deal Rooms</h2>
        <button
          onClick={onNewDeal}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Deal
        </button>
      </div>

      {deals.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
          <div className="text-5xl mb-4">🤝</div>
          <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-300 mb-2">No deals yet</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-5">Create a secure deal room to start protected negotiations.</p>
          <button onClick={onNewDeal}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold text-sm transition-colors">
            Start a New Deal →
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {deals.map(deal => {
            const isMyDeal = deal.buyer_id === currentUser.id;
            const role = isMyDeal ? 'Buyer' : 'Seller';
            const statusColor = statusColors[deal.status ?? 'ACTIVE'] || statusColors.ACTIVE;

            return (
              <div
                key={deal.id}
                onClick={() => onSelectDeal(deal)}
                className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 cursor-pointer hover:border-blue-400 dark:hover:border-blue-600 hover:shadow-md transition-all group"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <h3 className="font-semibold text-slate-800 dark:text-slate-100 truncate">{deal.item_name}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${statusColor}`}>
                        {deal.status ?? 'ACTIVE'}
                      </span>
                      <span className="text-xs bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 px-2 py-0.5 rounded-full shrink-0">
                        {role}
                      </span>
                    </div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      ${deal.price.toFixed(2)} {deal.currency}
                      {deal.buyer_name && role === 'Seller' && (
                        <span className="text-slate-400 dark:text-slate-500"> • Buyer: {deal.buyer_name}</span>
                      )}
                      {deal.seller_name && role === 'Buyer' && deal.seller_id && (
                        <span className="text-slate-400 dark:text-slate-500"> • Seller: {deal.seller_name}</span>
                      )}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <div className="text-right">
                      <span className={`text-sm font-bold ${verdictColors[deal.verdict] || verdictColors.LOW}`}>
                        {deal.risk_score}/100
                      </span>
                      <p className="text-xs text-slate-400 dark:text-slate-600">risk</p>
                    </div>
                    {deal.buyer_id === currentUser.id && (
                      <button
                        onClick={(e) => handleDelete(deal, e)}
                        disabled={deletingId === deal.id}
                        className="p-1.5 text-slate-300 hover:text-red-500 dark:text-slate-700 dark:hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                        aria-label="Delete deal"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    )}
                    <svg className="w-5 h-5 text-slate-400 dark:text-slate-600 group-hover:text-blue-500 dark:group-hover:text-blue-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>

                {/* PayPal status indicator */}
                {deal.paypal_order_id && (
                  <div className="mt-2 flex items-center gap-1.5 text-xs text-blue-600 dark:text-blue-400">
                    <span>💳</span>
                    <span>PayPal {deal.paypal_status ?? 'CREATED'} • {deal.paypal_order_id.substring(0, 12)}…</span>
                  </div>
                )}

                <p className="text-xs text-slate-400 dark:text-slate-600 mt-2">
                  {new Date(deal.created_at).toLocaleDateString()} {new Date(deal.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
