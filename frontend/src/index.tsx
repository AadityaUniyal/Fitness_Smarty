import React from 'react';
import ReactDOM from 'react-dom/client';
import { ClerkProvider } from '@clerk/clerk-react';
import App from './App';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

const PUBLISHABLE_KEY = process.env.CLERK_PUBLISHABLE_KEY;
const root = ReactDOM.createRoot(rootElement);

if (!PUBLISHABLE_KEY) {
  // Render a professional "Key Missing" HUD instead of crashing or using a broken fallback
  root.render(
    <div className="min-h-screen bg-[#020617] flex items-center justify-center p-8 text-center">
      <div className="glass-panel p-12 rounded-[3.5rem] border border-rose-500/20 max-w-md space-y-8 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-rose-500/20 to-transparent"></div>
        <div className="w-20 h-20 bg-rose-500/10 rounded-3xl flex items-center justify-center text-rose-500 mx-auto animate-pulse border border-rose-500/20">
          <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
        </div>
        <div className="space-y-2">
          <h1 className="text-3xl font-black italic tracking-tighter text-white uppercase">Neural Identity Lock</h1>
          <p className="text-[10px] font-black uppercase tracking-[0.3em] text-rose-500/60">Authentication Failure</p>
        </div>
        <p className="text-sm text-slate-400 font-medium leading-relaxed">
          The <span className="text-rose-400 font-bold">CLERK_PUBLISHABLE_KEY</span> environment variable is missing or invalid. Authentication protocol cannot be initialized.
        </p>
        <div className="p-4 bg-slate-950 rounded-2xl border border-white/5 text-[10px] font-mono text-emerald-500/80 overflow-x-auto text-left">
          // Action required:<br/>
          Add CLERK_PUBLISHABLE_KEY to environment variables.
        </div>
      </div>
    </div>
  );
} else {
  root.render(
    <React.StrictMode>
      <ClerkProvider publishableKey={PUBLISHABLE_KEY} afterSignOutUrl="/">
        <App />
      </ClerkProvider>
    </React.StrictMode>
  );
}