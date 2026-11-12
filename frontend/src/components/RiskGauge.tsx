import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';

interface RiskGaugeProps {
  score: number; // 0 to 100
  verdict: 'LOW' | 'MEDIUM' | 'HIGH';
  verdictTitle?: string;
  size?: number;
  initialScore?: number;
}

export const RiskGauge: React.FC<RiskGaugeProps> = ({
  score,
  verdict,
  verdictTitle,
  size = 280,
  initialScore,
}) => {
  const shouldReduceMotion = useReducedMotion();

  // Clamp score
  const safeScore = Math.max(0, Math.min(100, Math.round(score)));

  // Gauge geometry: Semi-circle from -180 deg to 0 deg (or -90 to +90)
  // Let's use an arc from angle -180 deg to 0 deg
  // In needle rotation: 0 score = -90 deg, 100 score = +90 deg
  const needleRotation = -90 + (safeScore / 100) * 180;

  // Determine color theme based on score/verdict
  const getVerdictDetails = () => {
    if (safeScore >= 70 || verdict === 'HIGH') {
      return {
        color: '#dc2626',
        bgPill: 'bg-red-100 text-red-800 dark:bg-red-950/60 dark:text-red-300 border-red-300 dark:border-red-800',
        label: 'HIGH RISK',
        sub: 'Likely Fraud / F&F Coercion',
      };
    }
    if (safeScore >= 40 || verdict === 'MEDIUM') {
      return {
        color: '#d97706',
        bgPill: 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border-amber-300 dark:border-amber-800',
        label: 'MEDIUM RISK',
        sub: 'Caution Advised / Test Seller',
      };
    }
    return {
      color: '#16a34a',
      bgPill: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800',
      label: 'LOW RISK',
      sub: 'Standard Marketplace Deal',
    };
  };

  const details = getVerdictDetails();
  const radius = 100;
  const strokeWidth = 18;
  const center = 130;

  return (
    <div
      role="meter"
      aria-label="DealCheck Transaction Risk Meter"
      aria-valuenow={safeScore}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuetext={`${safeScore} out of 100, ${details.label}`}
      className="flex flex-col items-center justify-center p-4 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-soft w-full"
    >
      <div className="relative w-full max-w-[280px] aspect-[1.7/1] flex items-center justify-center overflow-visible">
        <svg
          viewBox="0 0 260 150"
          className="w-full h-full overflow-visible"
        >
          <defs>
            {/* Smooth linear gradient across the arc */}
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10b981" />   {/* Emerald */}
              <stop offset="35%" stopColor="#84cc16" />  {/* Lime */}
              <stop offset="60%" stopColor="#f59e0b" />  {/* Amber */}
              <stop offset="100%" stopColor="#ef4444" /> {/* Red */}
            </linearGradient>

            <filter id="needleShadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="2" stdDeviation="2" floodOpacity="0.25" />
            </filter>
          </defs>

          {/* Background Track Arc */}
          <path
            d="M 30 130 A 100 100 0 0 1 230 130"
            fill="none"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            className="text-slate-100 dark:text-slate-800"
          />

          {/* Colored Risk Arc */}
          <path
            d="M 30 130 A 100 100 0 0 1 230 130"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray="314.159"
            strokeDashoffset="0"
          />

          {/* Scale Labels */}
          <text x="25" y="146" textAnchor="middle" className="text-[10px] font-bold fill-emerald-600 dark:fill-emerald-400">0</text>
          <text x="130" y="24" textAnchor="middle" className="text-[10px] font-bold fill-amber-500 dark:fill-amber-400">50</text>
          <text x="235" y="146" textAnchor="middle" className="text-[10px] font-bold fill-red-600 dark:fill-red-400">100</text>

          {/* Animated Needle */}
          <motion.g
            animate={{ rotate: needleRotation }}
            transition={shouldReduceMotion ? { duration: 0 } : { type: 'spring', damping: 15, stiffness: 90 }}
            style={{ originX: '130px', originY: '130px' }}
            filter="url(#needleShadow)"
          >
            {/* Needle line */}
            <line
              x1="130"
              y1="130"
              x2="130"
              y2="42"
              stroke="#001C48"
              strokeWidth="3.5"
              strokeLinecap="round"
              className="dark:stroke-white"
            />
            {/* Needle pointer tip */}
            <polygon
              points="126,50 134,50 130,36"
              fill="#001C48"
              className="dark:fill-white"
            />
          </motion.g>

          {/* Center Hub */}
          <circle
            cx="130"
            cy="130"
            r="12"
            fill="#003087"
            className="dark:fill-paypal-blue"
          />
          <circle
            cx="130"
            cy="130"
            r="5"
            fill="#ffffff"
          />
        </svg>
      </div>

      {/* Numerical Score Display */}
      <div className="text-center mt-2">
        <div className="flex items-baseline justify-center space-x-1">
          <motion.span
            key={safeScore}
            initial={shouldReduceMotion ? false : { scale: 0.85, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="text-4xl sm:text-5xl font-extrabold tracking-tight"
            style={{ color: details.color }}
          >
            {safeScore}
          </motion.span>
          <span className="text-sm font-semibold text-slate-400">/100</span>
        </div>

        {/* Verdict Badge */}
        <div className="mt-2 flex flex-col items-center">
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border tracking-wide uppercase ${details.bgPill}`}>
            {verdictTitle || details.label}
          </span>
          <span className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-medium">
            {details.sub}
          </span>
        </div>

        {/* Score Delta Indicator if adjusted by seller litmus test */}
        {initialScore !== undefined && initialScore !== safeScore && (
          <div className="mt-2 text-[11px] font-semibold">
            {safeScore < initialScore ? (
              <span className="text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-800">
                ↓ Risk dropped by {initialScore - safeScore} pts (Seller agreed to G&S)
              </span>
            ) : (
              <span className="text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 px-2 py-0.5 rounded border border-red-200 dark:border-red-800">
                ↑ Risk surged by {safeScore - initialScore} pts (Seller pushed F&F)
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
