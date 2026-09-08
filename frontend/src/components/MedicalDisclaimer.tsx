import React from 'react';
import { AlertTriangle, X } from 'lucide-react';

interface MedicalDisclaimerProps {
  variant?: 'banner' | 'inline' | 'modal';
  onDismiss?: () => void;
}

/**
 * Medical Disclaimer Component
 * Displays a clearly visible disclaimer that the app does not provide medical advice.
 */
const MedicalDisclaimer: React.FC<MedicalDisclaimerProps> = ({
  variant = 'banner',
  onDismiss,
}) => {
  const disclaimerText =
    'Smarty AI provides fitness and nutrition guidance ' +
    'for informational purposes only. It is not a substitute for professional ' +
    'medical advice, diagnosis, or treatment. Always consult a qualified ' +
    'healthcare provider before starting any exercise program or making ' +
    'dietary changes, especially if you are pregnant, nursing, have a ' +
    'medical condition, or are taking medication.';

  if (variant === 'inline') {
    return (
      <p className="text-xs text-amber-400/90 italic my-2 leading-relaxed flex items-start gap-1.5">
        <AlertTriangle size={14} className="shrink-0 mt-0.5" />
        <span>{disclaimerText}</span>
      </p>
    );
  }

  if (variant === 'modal') {
    return (
      <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 z-[65] animate-in fade-in">
        <div className="glass-panel p-8 rounded-[2.5rem] max-w-md w-full border border-rose-500/20 shadow-2xl space-y-4 card-3d">
          <div className="card-3d-shine" />
          <div className="flex items-center space-x-3 text-rose-400">
            <AlertTriangle size={22} />
            <h3 className="text-lg font-black italic uppercase tracking-tight text-white">Important Health Notice</h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">{disclaimerText}</p>
          <button
            onClick={onDismiss}
            className="w-full py-3.5 bg-rose-500 hover:bg-rose-400 text-slate-950 rounded-2xl font-black text-xs uppercase tracking-widest transition shadow-lg shadow-rose-500/20 active:scale-95"
          >
            I Understand
          </button>
        </div>
      </div>
    );
  }

  // Default: banner
  return (
    <div className="bg-rose-500/10 border-b border-rose-500/20 px-4 py-2.5 text-center text-xs text-slate-300 relative flex items-center justify-center gap-2">
      <AlertTriangle size={14} className="text-rose-400 shrink-0" />
      <span>
        Informational guidance only — not medical advice.{' '}
        <a href="/privacy-policy.html" className="text-cyan-400 underline hover:text-cyan-300">
          Privacy Policy
        </a>
      </span>
      {onDismiss && (
        <button
          onClick={onDismiss}
          aria-label="Dismiss disclaimer"
          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/10"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
};

export default MedicalDisclaimer;
