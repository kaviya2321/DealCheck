import React from 'react';
import { DealData } from '../../types';
import { RiskGauge } from '../RiskGauge';
import { ChatHighlighter } from '../ChatHighlighter';
import { ShieldCheck, AlertTriangle, ArrowRight, CheckCircle2, Info, ChevronRight } from 'lucide-react';

interface AnalysisStepProps {
  deal: DealData;
  onNext: () => void;
}

export const AnalysisStep: React.FC<AnalysisStepProps> = ({ deal, onNext }) => {
  return (
    <div className="w-full max-w-6xl mx-auto space-y-6 pb-20 sm:pb-0">
      {/* Title Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-black text-slate-900 dark:text-white">
            Deal Risk Analysis: {deal.item_name}
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Deal ID: <span className="font-mono text-paypal-blue font-bold">{deal.id}</span> • Price: ${deal.price.toFixed(2)} USD
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
            deal.verdict === 'HIGH'
              ? 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300'
              : deal.verdict === 'MEDIUM'
              ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
              : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
          }`}>
            {deal.verdict} Risk Detected
          </span>
        </div>
      </div>

      {/* Two Panel Layout on Desktop (Chat Left, Live Gauge & Breakdown Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Panel: Chat Transcript & Token Explainability (col-span-7) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-soft">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center space-x-2">
                <span>Negotiation Transcript & Token Highlights</span>
              </h3>
              <span className="text-[11px] font-semibold text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 px-2 py-0.5 rounded">
                {deal.highlighted_phrases.length} Risk Signal{deal.highlighted_phrases.length === 1 ? '' : 's'}
              </span>
            </div>

            <ChatHighlighter
              chatText={deal.chat_text}
              highlights={deal.highlighted_phrases}
            />
          </div>

          {/* Plain-Language Explanation */}
          <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-soft space-y-2">
            <div className="flex items-center space-x-2 text-paypal-deep dark:text-blue-400">
              <Info className="w-4 h-4 flex-shrink-0" />
              <h3 className="text-sm font-bold">DealCheck Security Assessment</h3>
            </div>
            <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
              {deal.explanation}
            </p>
          </div>
        </div>

        {/* Right Panel: Risk Gauge, Model Probability, Rules (col-span-5) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Custom SVG Risk Gauge */}
          <RiskGauge
            score={deal.risk_score}
            verdict={deal.verdict}
            verdictTitle={deal.verdict_title}
            initialScore={deal.initial_risk_score}
          />

          {/* Score Calculation Breakdown */}
          <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-soft space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Transparent Risk Formula Breakdown
            </h3>

            {/* Model A Component */}
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
              <div>
                <div className="text-xs font-bold text-slate-800 dark:text-slate-200">
                  Model A Base Score
                </div>
                <div className="text-[11px] text-slate-500">
                  TF-IDF + Calibrated Logistic Regression ({deal.model_probability ? (deal.model_probability * 100).toFixed(1) : 0}% prob)
                </div>
              </div>
              <span className="text-sm font-black font-mono text-paypal-deep dark:text-blue-400">
                +{deal.model_base_points || Math.round(deal.model_probability * 55)} pts
              </span>
            </div>

            {/* Deterministic Rule Violations */}
            <div className="space-y-1.5">
              <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                Deterministic Rule Violations ({deal.rules_triggered.length})
              </div>

              {deal.rules_triggered.length === 0 ? (
                <div className="p-2.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 text-emerald-800 dark:text-emerald-300 text-xs font-medium flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-600" />
                  <span>No deterministic fraud patterns detected.</span>
                </div>
              ) : (
                deal.rules_triggered.map((rule) => (
                  <div
                    key={rule.id}
                    className="p-2.5 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-100 dark:border-red-900/60 flex items-start justify-between gap-2"
                  >
                    <div>
                      <div className="text-xs font-bold text-red-900 dark:text-red-200">
                        {rule.name}
                      </div>
                      <div className="text-[11px] text-red-700 dark:text-red-400 mt-0.5 leading-tight">
                        {rule.explanation}
                      </div>
                    </div>
                    <span className="text-xs font-black font-mono text-red-600 dark:text-red-400 flex-shrink-0">
                      +{rule.points}
                    </span>
                  </div>
                ))
              )}
            </div>

            {/* Formula Summary Line */}
            <div className="border-t border-slate-200 dark:border-slate-800 pt-2 flex items-center justify-between text-xs font-extrabold text-slate-900 dark:text-white">
              <span>Final Initial Score (max 100)</span>
              <span className="text-base text-paypal-blue font-mono">{deal.initial_risk_score}/100</span>
            </div>
          </div>

          {/* Desktop Next Step Button */}
          <div className="hidden sm:block">
            <button
              onClick={onNext}
              className="w-full py-3.5 px-6 rounded-xl bg-paypal-blue hover:bg-paypal-deep text-white font-extrabold text-sm shadow-soft flex items-center justify-center space-x-2 transition-all cursor-pointer"
            >
              <span>Step 3: Generate PayPal Protection & Litmus Link</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Sticky Bottom Action Bar */}
      <div className="sm:hidden fixed bottom-0 left-0 right-0 p-3 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-t border-slate-200 dark:border-slate-800 z-30 shadow-lg">
        <button
          onClick={onNext}
          className="w-full py-3 px-4 rounded-xl bg-paypal-blue text-white font-extrabold text-sm shadow-md flex items-center justify-center space-x-2 active:scale-95 transition-all"
        >
          <span>Step 3: Generate PayPal Protected Link</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
