import React, { useState } from 'react';
import { DealData } from '../../types';
import { createProtectionLink } from '../../api';
import { ShieldCheck, Copy, Check, ExternalLink, ArrowRight, Loader2, AlertCircle, RefreshCw, Send } from 'lucide-react';

interface ProtectStepProps {
  deal: DealData;
  onDealUpdated: (deal: DealData) => void;
  onNext: () => void;
}

export const ProtectStep: React.FC<ProtectStepProps> = ({
  deal,
  onDealUpdated,
  onNext,
}) => {
  const [isCreatingLink, setIsCreatingLink] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);
  const [copiedMsg, setCopiedMsg] = useState(false);

  // If order already created
  const hasOrder = Boolean(deal.paypal_order_id && deal.paypal_approval_url);

  const handleCreateOrder = async () => {
    setIsCreatingLink(true);
    setErrorMsg(null);

    try {
      const res = await createProtectionLink(deal.id);
      // Update local deal state
      const updated: DealData = {
        ...deal,
        paypal_order_id: res.order_id,
        paypal_approval_url: res.approval_url,
        paypal_status: res.status,
        drafted_message: res.drafted_message,
      };
      onDealUpdated(updated);
    } catch (err: any) {
      setErrorMsg(err.message || 'PayPal Sandbox order creation failed. Please check credentials or retry.');
    } finally {
      setIsCreatingLink(false);
    }
  };

  const copyToClipboard = (text: string, type: 'link' | 'msg') => {
    navigator.clipboard.writeText(text);
    if (type === 'link') {
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    } else {
      setCopiedMsg(true);
      setTimeout(() => setCopiedMsg(false), 2000);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6 pb-20 sm:pb-0">
      {/* Title */}
      <div className="text-center space-y-1">
        <h2 className="text-2xl font-black text-slate-900 dark:text-white">
          Step 3: Generate PayPal Protection & Seller Litmus Test
        </h2>
        <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 max-w-xl mx-auto">
          DealCheck creates an authentic PayPal Sandbox Goods & Services checkout order. Send this link to the seller.
          Their response will expose whether they are legitimate or attempting to evade protection.
        </p>
      </div>

      {/* Sandbox Notice Banner */}
      <div className="p-3 bg-blue-50 dark:bg-slate-800 border border-blue-200 dark:border-blue-900 rounded-xl flex items-center justify-between text-xs text-paypal-deep dark:text-blue-300">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-paypal-blue flex-shrink-0" />
          <span>
            <strong>PayPal Sandbox Environment:</strong> Real Orders v2 REST API integration. Real order IDs generated. No real money charged.
          </span>
        </div>
        <span className="font-bold text-[10px] uppercase bg-paypal-blue text-white px-2 py-0.5 rounded">
          Sandbox
        </span>
      </div>

      {/* Error Banner with Retry */}
      {errorMsg && (
        <div className="p-4 bg-red-50 dark:bg-red-950/70 border border-red-200 dark:border-red-900 rounded-xl text-red-800 dark:text-red-200 text-sm flex items-start justify-between shadow-sm">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-600 mt-0.5" />
            <div>
              <p className="font-bold">PayPal Integration Error</p>
              <p className="text-xs opacity-90 mt-0.5">{errorMsg}</p>
            </div>
          </div>
          <button
            onClick={handleCreateOrder}
            className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-xs font-bold transition-colors ml-4 flex-shrink-0"
          >
            Retry
          </button>
        </div>
      )}

      {/* Generate Order Action if not created yet */}
      {!hasOrder ? (
        <div className="bg-white dark:bg-slate-900 p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-soft text-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-paypal-light dark:bg-paypal-deep/30 mx-auto flex items-center justify-center text-paypal-deep dark:text-blue-400">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Create Protected PayPal Order for &ldquo;{deal.item_name}&rdquo;
            </h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              DealCheck will call PayPal&apos;s REST Orders v2 API to generate an authentic Goods & Services checkout session for <strong>${deal.price.toFixed(2)} USD</strong>.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <button
              disabled={isCreatingLink}
              onClick={handleCreateOrder}
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-paypal-blue hover:bg-paypal-deep text-white font-extrabold text-sm shadow-soft inline-flex items-center justify-center space-x-2 transition-all cursor-pointer disabled:opacity-50"
            >
              {isCreatingLink ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Calling PayPal Sandbox Orders v2...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>Generate Official PayPal Sandbox Link</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={onNext}
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-bold text-sm transition-all flex items-center justify-center space-x-1.5 cursor-pointer"
            >
              <span>Skip to Step 4: Test Seller Reaction</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      ) : (
        /* Order Generated Success View */
        <div className="space-y-6">
          {/* Order Details Card */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-soft space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 dark:border-slate-800 pb-3 gap-2">
              <div className="flex items-center space-x-2 text-emerald-600 dark:text-emerald-400">
                <ShieldCheck className="w-5 h-5 flex-shrink-0" />
                <span className="font-extrabold text-sm">Real PayPal Sandbox Order Active</span>
              </div>
              <div className="flex items-center space-x-2 text-xs">
                <span className="text-slate-400">Order ID:</span>
                <span className="font-mono font-bold text-slate-800 dark:text-slate-200 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
                  {deal.paypal_order_id}
                </span>
              </div>
            </div>

            {/* Generated Link Box */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-500">
                PayPal Goods & Services Approval Link
              </label>
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  readOnly
                  value={deal.paypal_approval_url || ''}
                  className="flex-1 px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg font-mono text-slate-700 dark:text-slate-300 truncate"
                />
                <button
                  type="button"
                  onClick={() => copyToClipboard(deal.paypal_approval_url || '', 'link')}
                  className="px-3 py-2 bg-paypal-light text-paypal-deep dark:bg-slate-800 dark:text-blue-300 hover:bg-blue-100 font-bold text-xs rounded-lg flex items-center space-x-1.5 transition-colors border border-blue-200 dark:border-slate-700 flex-shrink-0"
                >
                  {copiedLink ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                  <span>{copiedLink ? 'Copied!' : 'Copy Link'}</span>
                </button>
              </div>
            </div>

            {/* Drafted Polite Message to Seller */}
            <div className="space-y-1.5 pt-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center space-x-1.5">
                  <Send className="w-3.5 h-3.5 text-paypal-blue" />
                  <span>Drafted Polite Message to Seller (The Litmus Test)</span>
                </label>
                <button
                  type="button"
                  onClick={() => copyToClipboard(deal.drafted_message || '', 'msg')}
                  className="text-xs font-bold text-paypal-blue hover:underline flex items-center space-x-1"
                >
                  {copiedMsg ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedMsg ? 'Message Copied!' : 'Copy Full Message'}</span>
                </button>
              </div>

              <div className="p-3.5 bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-xl text-xs sm:text-sm text-slate-800 dark:text-slate-200 font-sans leading-relaxed whitespace-pre-wrap">
                {deal.drafted_message}
              </div>
            </div>
          </div>

          {/* Explanation of Litmus Test Strategy */}
          <div className="p-4 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 rounded-xl text-xs text-amber-900 dark:text-amber-300 space-y-1">
            <p className="font-bold flex items-center space-x-1.5">
              <span>💡 How the Seller Litmus Test Works:</span>
            </p>
            <p className="leading-relaxed opacity-90">
              Scammers rely on coercing buyers to use Friends & Family because F&F payments cannot be reversed or disputed.
              When you send this official Goods & Services link, an honest seller will accept it, while a fraudster will make excuses to reject it.
            </p>
          </div>

          {/* Action to proceed to seller reaction */}
          <div className="flex justify-end pt-2">
            <button
              onClick={onNext}
              className="w-full sm:w-auto py-3.5 px-6 rounded-xl bg-paypal-blue hover:bg-paypal-deep text-white font-extrabold text-sm shadow-soft flex items-center justify-center space-x-2 transition-all cursor-pointer"
            >
              <span>Step 4: Test Seller Reaction with Model B</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Mobile Sticky Bottom */}
      {hasOrder && (
        <div className="sm:hidden fixed bottom-0 left-0 right-0 p-3 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-t border-slate-200 dark:border-slate-800 z-30 shadow-lg">
          <button
            onClick={onNext}
            className="w-full py-3 px-4 rounded-xl bg-paypal-blue text-white font-extrabold text-sm shadow-md flex items-center justify-center space-x-2"
          >
            <span>Proceed to Test Seller Reaction</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
