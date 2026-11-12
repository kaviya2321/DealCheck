import React, { useState } from 'react';
import { HighlightedPhrase } from '../types';
import { AlertCircle, HelpCircle, X } from 'lucide-react';

interface ChatHighlighterProps {
  chatText: string;
  highlights: HighlightedPhrase[];
}

export const ChatHighlighter: React.FC<ChatHighlighterProps> = ({
  chatText,
  highlights,
}) => {
  const [activeHighlight, setActiveHighlight] = useState<HighlightedPhrase | null>(null);

  if (!chatText) {
    return <div className="text-slate-400 italic text-sm">No conversation transcript provided.</div>;
  }

  // If no highlights detected
  if (!highlights || highlights.length === 0) {
    return (
      <div className="bg-slate-50 dark:bg-slate-900/60 p-4 rounded-xl border border-slate-200 dark:border-slate-800 text-sm whitespace-pre-wrap font-sans text-slate-800 dark:text-slate-200">
        {chatText}
      </div>
    );
  }

  // Sort highlights by character offset start
  const sorted = [...highlights].sort((a, b) => a.start - b.start);

  const segments: React.ReactNode[] = [];
  let lastIdx = 0;

  sorted.forEach((hl, i) => {
    // Plain text before highlight
    if (hl.start > lastIdx) {
      segments.push(
        <span key={`plain-${i}`}>{chatText.substring(lastIdx, hl.start)}</span>
      );
    }

    // Highlighted phrase span
    const isSelected = activeHighlight?.start === hl.start;
    segments.push(
      <mark
        key={`hl-${i}`}
        onClick={() => setActiveHighlight(isSelected ? null : hl)}
        className={`highlight-pill ${
          isSelected
            ? 'bg-red-300 dark:bg-red-800 ring-2 ring-red-500 text-red-950 dark:text-white font-bold'
            : 'highlight-pill-risk'
        }`}
        title={`Click for risk explanation: ${hl.reason}`}
      >
        {chatText.substring(hl.start, hl.end)}
        <span className="ml-1 text-[10px] font-mono opacity-80">▲{hl.weight}</span>
      </mark>
    );

    lastIdx = hl.end;
  });

  // Remainder plain text
  if (lastIdx < chatText.length) {
    segments.push(
      <span key="plain-end">{chatText.substring(lastIdx)}</span>
    );
  }

  return (
    <div className="relative">
      {/* Transcript Box */}
      <div className="bg-slate-50 dark:bg-slate-900/70 p-4 rounded-xl border border-slate-200 dark:border-slate-800 text-sm leading-relaxed whitespace-pre-wrap font-sans text-slate-800 dark:text-slate-200 shadow-inner max-h-[360px] overflow-y-auto">
        {segments}
      </div>

      {/* Explanatory Tooltip / Card for active selected phrase */}
      {activeHighlight && (
        <div className="mt-3 p-3.5 bg-red-50 dark:bg-red-950/80 border border-red-200 dark:border-red-900 rounded-xl shadow-md transition-all">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-2 text-red-800 dark:text-red-300 font-bold text-xs">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>Risky Phrase Detected: &ldquo;{activeHighlight.phrase}&rdquo;</span>
            </div>
            <button
              onClick={() => setActiveHighlight(null)}
              className="text-red-500 hover:text-red-700 dark:hover:text-red-200 p-0.5"
              aria-label="Close explanation"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-red-900 dark:text-red-200 mt-1 font-medium">
            {activeHighlight.reason}
          </p>
          <div className="mt-2 flex items-center justify-between text-[11px] text-red-700 dark:text-red-400 border-t border-red-200/60 dark:border-red-900/60 pt-1.5">
            <span>Model Log-Odds Contribution: <strong>+{activeHighlight.weight}</strong></span>
            <span className="text-[10px] text-slate-500">Tap anywhere on chat to deselect</span>
          </div>
        </div>
      )}

      {/* Helper cue */}
      {!activeHighlight && (
        <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-2 flex items-center space-x-1">
          <HelpCircle className="w-3.5 h-3.5" />
          <span>Tap or click on any highlighted phrase above to view the model&apos;s risk rationale.</span>
        </p>
      )}
    </div>
  );
};
