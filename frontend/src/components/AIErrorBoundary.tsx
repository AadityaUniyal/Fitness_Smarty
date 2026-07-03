import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class AIErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[Smarty AI] Localized AI Component Error:', error, info);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="p-8 bg-rose-500/5 border border-rose-500/20 rounded-[2rem] text-center max-w-lg mx-auto my-6 backdrop-blur-xl relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-full h-[2px] bg-rose-500/30"></div>
          <div className="w-14 h-14 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <AlertTriangle size={24} className="text-rose-400" />
          </div>
          <h4 className="text-lg font-black italic text-white uppercase tracking-tight mb-1">AI Sub-Processor Error</h4>
          <p className="text-xs text-slate-400 mb-4 leading-relaxed">
            The neural analyzer failed to process this request. This can be caused by model timeout or invalid inputs.
          </p>
          {this.state.error && (
            <p className="font-mono text-[10px] text-rose-400 bg-slate-950 p-3 rounded-xl border border-white/5 mb-4 max-h-24 overflow-y-auto break-all">
              {this.state.error.message}
            </p>
          )}
          <button
            onClick={this.handleRetry}
            className="inline-flex items-center space-x-2 px-5 py-3 bg-rose-500 hover:bg-rose-400 text-slate-950 font-black text-[10px] uppercase tracking-widest rounded-2xl transition-all shadow-[0_4px_15px_rgba(239,68,68,0.2)] active:scale-[0.98]"
          >
            <RefreshCw size={12} />
            <span>Retry Operation</span>
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
export default AIErrorBoundary;
