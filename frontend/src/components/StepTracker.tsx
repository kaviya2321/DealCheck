import React from 'react';
import { Check, ShieldAlert, Link2, MessageSquareCode, CheckCircle2 } from 'lucide-react';

interface StepTrackerProps {
  currentStep: number;
  setStep: (step: number) => void;
  maxStepReached: number;
}

const STEPS = [
  { id: 1, title: 'Input & OCR', short: 'Input', icon: MessageSquareCode },
  { id: 2, title: 'Risk Analysis', short: 'Risk', icon: ShieldAlert },
  { id: 3, title: 'PayPal Protection', short: 'Protect', icon: Link2 },
  { id: 4, title: 'Seller Reaction', short: 'Litmus', icon: MessageSquareCode },
  { id: 5, title: 'Pay & Evidence', short: 'Payment', icon: CheckCircle2 },
];

export const StepTracker: React.FC<StepTrackerProps> = ({
  currentStep,
  setStep,
  maxStepReached,
}) => {
  return (
    <div className="w-full bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 py-3 px-4 sm:px-6 shadow-sm">
      {/* Mobile Compact Progress Bar (<= 640px) */}
      <div className="sm:hidden">
        <div className="flex items-center justify-between text-xs font-semibold mb-2">
          <span className="text-paypal-deep dark:text-blue-400">
            Step {currentStep} of {STEPS.length}: {STEPS[currentStep - 1]?.title}
          </span>
          <span className="text-slate-500 text-[11px]">
            {Math.round((currentStep / STEPS.length) * 100)}% Complete
          </span>
        </div>
        <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
          <div
            className="bg-paypal-blue h-full transition-all duration-300 rounded-full"
            style={{ width: `${(currentStep / STEPS.length) * 100}%` }}
          />
        </div>
        {/* Quick mobile touch pills */}
        <div className="flex justify-between mt-2 pt-1 border-t border-slate-100 dark:border-slate-800">
          {STEPS.map((s) => {
            const isClickable = s.id <= maxStepReached;
            const isCurrent = s.id === currentStep;
            return (
              <button
                key={s.id}
                disabled={!isClickable}
                onClick={() => setStep(s.id)}
                className={`text-[11px] font-medium px-2 py-1 rounded transition-colors ${
                  isCurrent
                    ? 'text-paypal-blue font-bold underline underline-offset-4'
                    : isClickable
                    ? 'text-slate-600 dark:text-slate-300'
                    : 'text-slate-300 dark:text-slate-700 cursor-not-allowed'
                }`}
              >
                {s.short}
              </button>
            );
          })}
        </div>
      </div>

      {/* Desktop / Tablet Breadcrumbs (>= 640px) */}
      <nav aria-label="Progress Steps" className="hidden sm:block max-w-5xl mx-auto">
        <ol className="flex items-center justify-between w-full">
          {STEPS.map((step, idx) => {
            const isCompleted = step.id < currentStep;
            const isCurrent = step.id === currentStep;
            const isClickable = step.id <= maxStepReached;
            const Icon = step.icon;

            return (
              <li key={step.id} className="flex-1 relative flex items-center">
                <button
                  type="button"
                  disabled={!isClickable}
                  onClick={() => setStep(step.id)}
                  aria-current={isCurrent ? 'step' : undefined}
                  className={`group flex items-center space-x-2.5 text-left focus:outline-none focus:ring-2 focus:ring-paypal-blue rounded-lg p-1 transition-all ${
                    isClickable ? 'cursor-pointer' : 'cursor-not-allowed opacity-60'
                  }`}
                >
                  <span
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all shadow-sm ${
                      isCompleted
                        ? 'bg-emerald-600 text-white'
                        : isCurrent
                        ? 'bg-paypal-blue text-white ring-4 ring-paypal-light dark:ring-blue-900/40'
                        : 'bg-slate-200 dark:bg-slate-800 text-slate-500 dark:text-slate-400'
                    }`}
                  >
                    {isCompleted ? <Check className="w-4 h-4 stroke-[3]" /> : step.id}
                  </span>
                  <div className="flex flex-col">
                    <span
                      className={`text-xs font-bold leading-tight ${
                        isCurrent
                          ? 'text-paypal-blue dark:text-blue-400'
                          : isCompleted
                          ? 'text-slate-900 dark:text-white'
                          : 'text-slate-400 dark:text-slate-500'
                      }`}
                    >
                      {step.title}
                    </span>
                    <span className="text-[10px] text-slate-400 dark:text-slate-500">
                      {isCompleted ? 'Completed' : isCurrent ? 'Active' : 'Pending'}
                    </span>
                  </div>
                </button>

                {/* Connecting Bar */}
                {idx < STEPS.length - 1 && (
                  <div className="flex-1 mx-3 hidden md:block">
                    <div
                      className={`h-0.5 w-full rounded transition-colors ${
                        step.id < currentStep
                          ? 'bg-emerald-500'
                          : 'bg-slate-200 dark:bg-slate-800'
                      }`}
                    />
                  </div>
                )}
              </li>
            );
          })}
        </ol>
      </nav>
    </div>
  );
};
