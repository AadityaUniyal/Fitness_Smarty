
import React, { useState } from 'react';
import { SignIn, SignUp } from '@clerk/clerk-react';
import { Dumbbell, Zap, ShieldCheck } from 'lucide-react';

const Auth: React.FC = () => {
  const [showSignIn, setShowSignIn] = useState(true);

  const clerkAppearance = {
    variables: {
      colorPrimary: '#10b981',
      colorBackground: 'transparent',
      colorText: '#f8fafc',
      colorTextSecondary: '#94a3b8',
      colorInputBackground: '#020617',
      colorInputText: '#10b981',
      borderRadius: '1.5rem',
      fontFamily: 'Inter, sans-serif'
    },
    elements: {
      card: "shadow-none border-none p-0",
      headerTitle: "hidden",
      headerSubtitle: "hidden",
      socialButtonsBlockButton: "bg-slate-950 border border-white/5 hover:bg-white/5 transition-all text-slate-300",
      formButtonPrimary: "bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black uppercase tracking-[0.2em] shadow-[0_10px_30px_rgba(16,185,129,0.3)] py-4",
      formFieldInput: "bg-slate-950/50 border-white/10 focus:border-emerald-500/50 text-emerald-400 font-bold",
      footerActionLink: "text-emerald-400 hover:text-emerald-300",
      dividerLine: "bg-white/5",
      dividerText: "text-slate-600 font-black uppercase text-[8px] tracking-[0.3em]",
      identityPreviewText: "text-emerald-400",
      formFieldLabel: "text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2",
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center relative overflow-hidden bg-[#020617]">
      {/* Dynamic Background Elements */}
      <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-emerald-500/10 rounded-full blur-[160px] animate-pulse"></div>
      <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] bg-cyan-500/10 rounded-full blur-[160px] animate-pulse transition-all duration-1000"></div>
      
      {/* Grid Pattern Overlay */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none" 
           style={{ backgroundImage: 'radial-gradient(#10b981 1px, transparent 0)', backgroundSize: '40px 40px' }}></div>

      <div className="relative z-10 w-full max-w-[480px] px-6 py-12">
        <div className="text-center mb-10 space-y-4">
          <div className="relative inline-flex mb-4 group">
             <div className="absolute -inset-4 bg-emerald-500/20 rounded-full blur-xl group-hover:bg-emerald-500/40 transition-all"></div>
             <div className="relative w-20 h-20 bg-emerald-500 rounded-3xl flex items-center justify-center text-slate-950 rotate-6 group-hover:rotate-12 transition-transform shadow-[0_0_30px_rgba(16,185,129,0.5)]">
                <Dumbbell size={40} />
             </div>
             <div className="absolute -top-1 -right-1 bg-cyan-400 w-6 h-6 rounded-full flex items-center justify-center animate-bounce">
                <Zap size={12} className="text-slate-950 fill-slate-950" />
             </div>
          </div>
          
          <h1 className="text-5xl font-black italic tracking-tighter text-white glow-text">
            SMARTY <span className="text-emerald-400">AI</span>
          </h1>
          <p className="text-slate-400 text-sm font-bold uppercase tracking-[0.3em]">Neural Fitness Protocol</p>
        </div>

        <div className="glass-panel p-1 rounded-[3rem] border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.5)] relative overflow-hidden">
          <div className="scanline absolute top-0 left-0"></div>
          
          <div className="p-8">
            <div className="flex bg-slate-950/80 p-1.5 rounded-2xl border border-white/5 mb-8">
              <button 
                onClick={() => setShowSignIn(true)}
                className={`flex-1 py-3 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all ${
                  showSignIn ? 'bg-emerald-500 text-slate-950 shadow-[0_0_15px_rgba(16,185,129,0.4)]' : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                Identification
              </button>
              <button 
                onClick={() => setShowSignIn(false)}
                className={`flex-1 py-3 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all ${
                  !showSignIn ? 'bg-emerald-500 text-slate-950 shadow-[0_0_15px_rgba(16,185,129,0.4)]' : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                Initialize
              </button>
            </div>

            {showSignIn ? (
              <SignIn appearance={clerkAppearance} routing="hash" />
            ) : (
              <SignUp appearance={clerkAppearance} routing="hash" />
            )}
          </div>
        </div>

        <div className="mt-12 flex flex-col items-center space-y-4">
           <div className="flex items-center space-x-3 text-slate-600">
              <ShieldCheck size={14} className="text-emerald-500" />
              <span className="text-[10px] font-bold uppercase tracking-widest">End-to-End Encrypted Sync</span>
           </div>
           <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">
              Smarty AI v4.0.0-Uplink • <span className="text-emerald-500 text-xs italic tracking-normal lowercase ml-1">clerk enabled</span>
           </p>
        </div>
      </div>
    </div>
  );
};

export default Auth;
