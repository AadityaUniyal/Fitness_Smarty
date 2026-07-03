import React from 'react';
import { AlertTriangle, RefreshCw, Zap } from 'lucide-react';

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends React.Component<React.PropsWithChildren<{}>, State> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[Smarty AI] Uncaught error:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#020617] flex items-center justify-center p-6 text-white">
          <div className="absolute top-1/3 left-1/2 w-96 h-96 bg-rose-500/5 rounded-full blur-3xl -translate-x-1/2 pointer-events-none" />
          <div className="relative z-10 max-w-lg w-full text-center">
            <div className="w-20 h-20 bg-rose-500/10 border border-rose-500/20 rounded-3xl flex items-center justify-center mx-auto mb-6">
              <AlertTriangle size={40} className="text-rose-400" />
            </div>
            <div className="flex items-center justify-center space-x-3 mb-4">
              <div className="w-8 h-8 bg-emerald-500 rounded-xl flex items-center justify-center">
                <Zap size={18} className="fill-slate-950 text-slate-950" />
              </div>
              <h1 className="text-2xl font-black italic text-white">SMARTY <span className="text-emerald-400">AI</span></h1>
            </div>
            <h2 className="text-xl font-black text-white italic tracking-tight mb-2 uppercase">Neural Link Disrupted</h2>
            <p className="text-slate-400 text-sm mb-2">
              An unexpected error occurred in the Smarty AI interface.
            </p>
            {this.state.error && (
              <div className="px-4 py-3 bg-slate-900 border border-rose-500/20 rounded-2xl mb-6 text-left">
                <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Error</p>
                <p className="font-mono text-xs text-rose-400 break-all">{this.state.error.message}</p>
              </div>
            )}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={() => this.setState({ hasError: false, error: undefined })}
                className="flex items-center justify-center space-x-2 px-6 py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-[10px] uppercase tracking-widest rounded-2xl transition-all"
              >
                <RefreshCw size={14} />
                <span>Reboot Interface</span>
              </button>
              <button
                onClick={() => window.location.href = '/'}
                className="flex items-center justify-center space-x-2 px-6 py-3 bg-slate-900 hover:bg-slate-800 border border-white/10 text-slate-400 font-black text-[10px] uppercase tracking-widest rounded-2xl transition-all"
              >
                <span>Return to Base</span>
              </button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
