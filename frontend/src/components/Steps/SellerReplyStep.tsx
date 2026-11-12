import React, { useState } from 'react';
import { DealData } from '../../types';
import { sendSellerReply } from '../../api';
import { RiskGauge } from '../RiskGauge';
import { MessageSquare, ShieldAlert, CheckCircle2, AlertOctagon, ArrowRight, Loader2, RefreshCw } from 'lucide-react';

interface SellerReplyStepProps {
  deal: DealData;
  onDealUpdated: (deal: DealData) => void;
  onNext: () => void;
}

const SAMPLE_REPLIES = [
  {
    label: '🚨 Seller Pushes F&F (Scam Coercion)',
    text: 'No, send it as Friends and Family so we avoid fees. PayPal takes a 3.5% cut and holds my money for 21 days! Send F&F or deal is cancelled.',
    desc: 'Triggers Model B: pushes_friends_and_family (+40 risk points)'
  },
  {
    label: '✅ Seller Accepts Protected Payment (Legit)',
    text: "Sure, send the PayPal Goods and Services link and I'll confirm receipt. I will pack it up and ship with tracking tomorrow morning.",
    desc: 'Triggers Model B: accepts_protected (-40 risk points)'
  },
  {
    label: '⚠️ Seller Refuses Online Payments (Cash Only)',
    text: 'No PayPal. Strictly cash only in person upon local meetup. No apps, no links.',
    desc: 'Triggers Model B: refuses_protected (+20 risk points)'
  }
];

export const SellerReplyStep: React.FC<SellerReplyStepProps> = ({
  deal,
  onDealUpdated,
  onNext,
}) => {
  const [replyText, setReplyText] = useState(deal.seller_reply_text || '');
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleEvaluateReply = async (textToUse?: string) => {
    const text = textToUse || replyText;
    if (!text.trim()) {
      setErrorMsg('Please paste the seller\'s response or select a test reply.');
      return;
    }

    setErrorMsg(null);
    setIsEvaluating(true);

    try {
      const res = await sendSellerReply(deal.id, text);
      const updated: DealData = {
        ...deal,
        seller_reply_text: text,
        seller_classification: res.seller_classification,
        seller_confidence: res.confidence,
        seller_litmus_verdict: res.litmus_verdict,
        risk_score: res.new_score,
        verdict: res.verdict,
      };
      onDealUpdated(updated);
    } catch (err: any) {
      setErrorMsg(err.message || 'Evaluation of seller reply failed.');
    } finally {
      setIsEvaluating(false);
    }
  };

  const getLitmusVerdictBadge = () => {
    if (!deal.seller_litmus_verdict) return null;

    if (deal.seller_litmus_verdict === 'PASSED') {
      return (
        <div className="p-4 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-xl flex items-start space-x-3 text-emerald-900 dark:text-emerald-200">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-600 mt-0.5" />
          <div className="space-y-0.5 text-xs">
            <p className="font-extrabold text-sm text-emerald-800 dark:text-emerald-300">
              Litmus Test PASSED: Verified Seller Behavior
            </p>
            <p className="leading-relaxed">
              Model B classified response as <strong>accepts_protected</strong> (Confidence: {((deal.seller_confidence || 0.98) * 100).toFixed(1)}%).
              The seller agreed to PayPal Goods & Services. Risk score dropped by 40 points!
            </p>
          </div>
        </div>
      );
    }

    if (deal.seller_litmus_verdict === 'FAILED') {
      return (
        <div className="p-4 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-xl flex items-start space-x-3 text-red-900 dark:text-red-200">
          <AlertOctagon className="w-5 h-5 flex-shrink-0 text-red-600 mt-0.5" />
          <div className="space-y-0.5 text-xs">
            <p className="font-extrabold text-sm text-red-800 dark:text-red-300">
              Litmus Test FAILED: Critical Scam Flag Raised
            </p>
            <p className="leading-relaxed">
              Model B classified response as <strong>pushes_friends_and_family</strong> (Confidence: {((deal.seller_confidence || 0.99) * 100).toFixed(1)}%).
              The seller actively refused buyer protection and pressured for Friends & Family. Risk score surged to {deal.risk_score}/100!
            </p>
          </div>
        </div>
      );
    }

    return (
      <div className="p-4 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-xl flex items-start space-x-3 text-amber-900 dark:text-amber-200">
        <ShieldAlert className="w-5 h-5 flex-shrink-0 text-amber-600 mt-0.5" />
        <div className="space-y-0.5 text-xs">
          <p className="font-extrabold text-sm text-amber-800 dark:text-amber-300">
            Litmus Test WARNING: Refused Protected Online Payment
          </p>
          <p className="leading-relaxed">
            Model B classified response as <strong>refuses_protected</strong> (Confidence: {((deal.seller_confidence || 0.95) * 100).toFixed(1)}%).
            Seller declined PayPal and demands in-person cash. If proceeding, meet only in a secure public location.
          </p>
        </div>
      </div>
    );
  };

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6 pb-20 sm:pb-0">
      {/* Title */}
      <div className="text-center space-y-1">
        <h2 className="text-2xl font-black text-slate-900 dark:text-white">
          Step 4: Seller Reaction Litmus Test
        </h2>
        <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 max-w-xl mx-auto">
          Paste what the seller replied after you sent the protected PayPal checkout link.
          Our trained Model B (SellerReplyModel) classifies their behavior and dynamically updates the risk gauge.
        </p>
      </div>

      {/* Main Grid: Input Left, Gauge Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Reply Input & Quick Test Buttons (col-span-7) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-soft space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center space-x-1.5">
                <MessageSquare className="w-4 h-4 text-paypal-blue" />
                <span>Seller&apos;s Actual Reply</span>
              </label>
              <span className="text-[11px] text-slate-400">Classified by Model B</span>
            </div>

            <textarea
              rows={4}
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              placeholder="Paste seller's message, e.g. 'No I don't use goods and services, send as friends and family'..."
              className="w-full p-3 text-sm bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-paypal-blue focus:outline-none font-mono text-slate-800 dark:text-slate-200"
            />

            {/* Test Simulation Buttons */}
            <div className="space-y-2 pt-1 border-t border-slate-100 dark:border-slate-800">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                Or simulate typical seller responses:
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {SAMPLE_REPLIES.map((sample, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => {
                      setReplyText(sample.text);
                      handleEvaluateReply(sample.text);
                    }}
                    className="p-2.5 text-left rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 hover:bg-blue-50 dark:bg-slate-800/60 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs transition-colors flex flex-col justify-between"
                  >
                    <span className="font-bold text-[11px] leading-snug">{sample.label}</span>
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">{sample.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Evaluate Button */}
            <button
              disabled={isEvaluating || !replyText.trim()}
              onClick={() => handleEvaluateReply()}
              className="w-full py-3.5 px-4 rounded-xl bg-paypal-blue hover:bg-paypal-deep text-white font-extrabold text-xs sm:text-sm shadow-soft flex items-center justify-center space-x-2 transition-all cursor-pointer disabled:opacity-50"
            >
              {isEvaluating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Evaluating with Model B Classifier...</span>
                </>
              ) : (
                <>
                  <span>Evaluate Reply with Model B</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>

          {/* Litmus Verdict Card */}
          {getLitmusVerdictBadge()}
        </div>

        {/* Right Column: Live Recalibrated Risk Gauge (col-span-5) */}
        <div className="lg:col-span-5 space-y-4">
          <RiskGauge
            score={deal.risk_score}
            verdict={deal.verdict}
            verdictTitle={deal.verdict_title}
            initialScore={deal.initial_risk_score}
          />

          <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-soft text-xs space-y-2">
            <h4 className="font-bold text-slate-800 dark:text-slate-200">
              Why the Litmus Test Works:
            </h4>
            <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
              Legitimate sellers are happy to use PayPal Goods & Services because it also protects them against fraudulent chargebacks.
              Only scammers insist on Friends & Family to guarantee non-refundable transfers.
            </p>
          </div>

          {/* Next Step Button */}
          <div className="hidden sm:block">
            <button
              onClick={onNext}
              className="w-full py-3.5 px-6 rounded-xl bg-paypal-blue hover:bg-paypal-deep text-white font-extrabold text-sm shadow-soft flex items-center justify-center space-x-2 transition-all cursor-pointer"
            >
              <span>Step 5: Pay with Sandbox & Export Evidence</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Sticky Bottom */}
      <div className="sm:hidden fixed bottom-0 left-0 right-0 p-3 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-t border-slate-200 dark:border-slate-800 z-30 shadow-lg">
        <button
          onClick={onNext}
          className="w-full py-3 px-4 rounded-xl bg-paypal-blue text-white font-extrabold text-sm shadow-md flex items-center justify-center space-x-2"
        >
          <span>Step 5: Pay & Export Evidence</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
