import React from 'react';
import { CheckCircle2, AlertTriangle, Info, XCircle, X } from 'lucide-react';
import type { Toast } from '../hooks/useToast';

interface ToastContainerProps {
  toasts: Toast[];
  onDismiss: (id: string) => void;
}

const ICONS = {
  success: <CheckCircle2 size={18} className="text-emerald-400 shrink-0" />,
  error: <XCircle size={18} className="text-rose-400 shrink-0" />,
  warning: <AlertTriangle size={18} className="text-amber-400 shrink-0" />,
  info: <Info size={18} className="text-cyan-400 shrink-0" />,
};

const COLORS = {
  success: 'border-emerald-500/30 bg-slate-950/90 text-emerald-300',
  error: 'border-rose-500/30 bg-slate-950/90 text-rose-300',
  warning: 'border-amber-500/30 bg-slate-950/90 text-amber-300',
  info: 'border-cyan-500/30 bg-slate-950/90 text-cyan-300',
};

const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onDismiss }) => {
  if (toasts.length === 0) return null;
  return (
    <div 
      className="fixed bottom-6 right-6 z-[70] flex flex-col gap-3 pointer-events-none"
      role="status"
      aria-live="polite"
    >
      {toasts.map(toast => (
        <div
          key={toast.id}
          className={`flex items-center gap-3 px-5 py-4 rounded-2xl border backdrop-blur-2xl shadow-2xl pointer-events-auto max-w-sm animate-in slide-in-from-right-4 duration-300 card-3d ${COLORS[toast.type]}`}
        >
          <div className="card-3d-shine" />
          {ICONS[toast.type]}
          <p className="text-xs font-bold text-white flex-1 leading-snug">{toast.message}</p>
          <button
            onClick={() => onDismiss(toast.id)}
            className="text-slate-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-white/10"
            aria-label="Dismiss notification"
          >
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
};

export default ToastContainer;
