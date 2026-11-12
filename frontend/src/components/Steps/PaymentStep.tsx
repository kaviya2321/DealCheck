import React, { useState } from 'react';
import { DealData } from '../../types';
import { capturePayPalOrder } from '../../api';
import { ShieldCheck, ExternalLink, CheckCircle2, Download, Printer, ArrowRight, Loader2, AlertCircle } from 'lucide-react';
import confetti from 'canvas-confetti';

interface PaymentStepProps {
  deal: DealData;
  onDealUpdated: (deal: DealData) => void;
  onNewCheck: () => void;
}

export const PaymentStep: React.FC<PaymentStepProps> = ({
  deal,
  onDealUpdated,
  onNewCheck,
}) => {
  const [isCapturing, setIsCapturing] = useState(false);
  const [captureError, setCaptureError] = useState<string | null>(null);

  const isCompleted = deal.paypal_status === 'COMPLETED';

  const handleSimulateReturnAndCapture = async () => {
    if (!deal.paypal_order_id) {
      setCaptureError('No active PayPal order to capture.');
      return;
    }

    setIsCapturing(true);
    setCaptureError(null);

    try {
      const res = await capturePayPalOrder(deal.paypal_order_id, deal.id);
      const updated: DealData = {
        ...deal,
        paypal_status: res.status,
        paypal_capture_id: res.capture_id,
      };
      onDealUpdated(updated);

      // Trigger celebratory confetti on completion
      confetti({
        particleCount: 80,
        spread: 70,
        origin: { y: 0.6 }
      });
    } catch (err: any) {
      setCaptureError(err.message || 'PayPal capture failed.');
    } finally {
      setIsCapturing(false);
    }
  };

  const openEvidenceHtml = () => {
    window.open(`/api/evidence/${deal.id}?format=html`, '_blank');
  };

  const downloadEvidenceJson = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(deal, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `dealcheck_evidence_${deal.id}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6 pb-20 sm:pb-0">
      {/* Title */}
      <div className="text-center space-y-1">
        <h2 className="text-2xl font-black text-slate-900 dark:text-white">
          Step 5: PayPal Sandbox Payment & Evidence Dossier
        </h2>
        <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 max-w-xl mx-auto">
          Complete the sandbox transaction securely or inspect the verified dispute evidence timeline.
        </p>
      </div>

      {/* Sandbox Notice Banner */}
      <div className="p-3 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-xl flex items-center justify-between text-xs text-amber-900 dark:text-amber-300">
        <span className="font-medium">
          ⚠️ <strong>Notice:</strong> Sandbox checkout, no real money. Does not simulate actual buyer-protection arbitration claims.
        </span>
        <span className="font-bold text-[10px] uppercase bg-amber-200 text-amber-900 px-2 py-0.5 rounded">
          Sandbox
        </span>
      </div>

      {/* Payment Action Card */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-soft space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 dark:border-slate-800 pb-4 gap-2">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Item</span>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">{deal.item_name}</h3>
          </div>
          <div className="sm:text-right">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Total Amount</span>
            <div className="text-2xl font-black font-mono text-paypal-deep dark:text-blue-400">
              ${deal.price.toFixed(2)} USD
            </div>
          </div>
        </div>

        {/* Order IDs & Status */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800">
            <span className="text-[10px] font-bold text-slate-400 uppercase">PayPal Order ID</span>
            <div className="text-xs font-bold font-mono text-slate-800 dark:text-slate-200 truncate mt-0.5">
              {deal.paypal_order_id || 'Not Generated'}
            </div>
          </div>

          <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800">
            <span className="text-[10px] font-bold text-slate-400 uppercase">Status</span>
            <div className="text-xs font-bold text-slate-800 dark:text-slate-200 mt-0.5 flex items-center space-x-1.5">
              <span className={`w-2 h-2 rounded-full ${isCompleted ? 'bg-emerald-500' : 'bg-paypal-blue animate-pulse'}`} />
              <span>{deal.paypal_status || 'CREATED'}</span>
            </div>
          </div>

          <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800">
            <span className="text-[10px] font-bold text-slate-400 uppercase">Capture ID</span>
            <div className="text-xs font-bold font-mono text-slate-800 dark:text-slate-200 truncate mt-0.5">
              {deal.paypal_capture_id || (isCompleted ? 'Captured' : 'Pending Payer Approval')}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        {!isCompleted ? (
          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            <a
              href={deal.paypal_approval_url || '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 py-3.5 px-4 rounded-xl bg-paypal-blue hover:bg-paypal-deep text-white font-extrabold text-sm shadow-soft flex items-center justify-center space-x-2 transition-all cursor-pointer"
            >
              <span>1. Open PayPal Sandbox Approval Window</span>
              <ExternalLink className="w-4 h-4" />
            </a>

            <button
              disabled={isCapturing}
              onClick={handleSimulateReturnAndCapture}
              className="flex-1 py-3.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold text-sm shadow-soft flex items-center justify-center space-x-2 transition-all cursor-pointer disabled:opacity-50"
            >
              {isCapturing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Capturing Order on PayPal REST API...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>2. Confirm Approval & Capture Order</span>
                </>
              )}
            </button>
          </div>
        ) : (
          <div className="p-4 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-xl flex items-center justify-between text-emerald-900 dark:text-emerald-200">
            <div className="flex items-center space-x-3">
              <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0" />
              <div>
                <p className="font-extrabold text-sm text-emerald-800 dark:text-emerald-300">
                  Payment Captured Successfully!
                </p>
                <p className="text-xs opacity-90">
                  Order verified in PayPal Sandbox. Capture ID: <strong>{deal.paypal_capture_id}</strong>
                </p>
              </div>
            </div>
            <span className="font-bold text-xs uppercase bg-emerald-600 text-white px-3 py-1 rounded-full">
              COMPLETED
            </span>
          </div>
        )}

        {/* Capture Error Banner */}
        {captureError && (
          <div className="p-3 bg-red-50 dark:bg-red-950/70 border border-red-200 dark:border-red-900 rounded-xl text-red-800 dark:text-red-200 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
            <span>{captureError}</span>
          </div>
        )}
      </div>

      {/* Evidence Export & Audit Trail */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-soft space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Official Dispute Evidence Dossier
            </h3>
            <p className="text-xs text-slate-500">
              Verified cryptographic timeline and risk audit trail for PayPal claims or dispute resolution.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={openEvidenceHtml}
              className="px-3 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded-lg text-xs font-bold flex items-center space-x-1.5 transition-colors cursor-pointer"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print / Export PDF</span>
            </button>

            <button
              onClick={downloadEvidenceJson}
              className="px-3 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded-lg text-xs font-bold flex items-center space-x-1.5 transition-colors cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download JSON</span>
            </button>
          </div>
        </div>

        {/* Chronological Audit Timeline */}
        <div className="space-y-3 pt-2">
          {deal.timeline.map((ev, i) => (
            <div key={i} className="flex items-start space-x-3 text-xs">
              <div className="w-2 h-2 rounded-full bg-paypal-blue mt-1.5 flex-shrink-0" />
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-800 dark:text-slate-200">{ev.title}</span>
                  <span className="text-[10px] text-slate-400 font-mono">{ev.timestamp.split('T')[1]?.replace('Z', '') || ''}</span>
                </div>
                <p className="text-slate-600 dark:text-slate-400 mt-0.5 leading-relaxed">{ev.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Start New Check Button */}
      <div className="pt-2 flex justify-center">
        <button
          onClick={onNewCheck}
          className="px-6 py-3 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-bold text-xs transition-colors cursor-pointer"
        >
          Check Another Deal
        </button>
      </div>
    </div>
  );
};
