import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Activity,
    Apple,
    ArrowDown,
    ArrowRight,
    Camera,
    CheckCircle2,
    Dumbbell,
    Eye,
    EyeOff,
    HeartPulse,
    Lock,
    Mail,
    Moon,
    Sparkles,
    User,
    Zap,
    TrendingUp,
    Check
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import heroBg from '../assets/hero_background.png';
import brandLogo from '../assets/brand_logo.png';

interface LoginForm { name: string; email: string; password: string; }

const LoginPage: React.FC = () => {
    const navigate = useNavigate();
    const { login, register, googleLogin, appleLogin, loading: authLoading } = useAuth();
    const [isRegister, setIsRegister] = useState(false);
    const [showPass, setShowPass] = useState(false);
    const [form, setForm] = useState<LoginForm>({ name: '', email: '', password: '' });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    
    // Smooth scroll reveals state
    const [scrollY, setScrollY] = useState(0);

    useEffect(() => {
        const handleScroll = () => setScrollY(window.scrollY);
        window.addEventListener('scroll', handleScroll, { passive: true });
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const routeAfterAuth = () => {
        const profile = localStorage.getItem('smarty_profile');
        navigate(profile ? '/dashboard' : '/onboarding');
    };

    const handleLoginSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            await login(form.email, form.password);
            routeAfterAuth();
        } catch (err: any) {
            setError(err?.message || 'Authentication failed');
        } finally {
            setLoading(false);
        }
    };

    const handleRegisterSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            await register(form.email, form.password, form.name || form.email.split('@')[0]);
            routeAfterAuth();
        } catch (err: any) {
            setError(err?.message || 'Registration failed');
        } finally {
            setLoading(false);
        }
    };

    const handleGuest = () => {
        localStorage.setItem('smarty_user', JSON.stringify({ name: 'Guest Operator', email: 'guest@smarty.ai', loggedIn: true }));
        routeAfterAuth();
    };

    const handleGoogleOAuth = async () => {
        setLoading(true);
        setError('');
        try {
            const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
            if (googleClientId) {
                await new Promise<void>((resolve, reject) => {
                    const script = document.createElement('script');
                    script.src = 'https://accounts.google.com/gsi/client';
                    script.onload = () => {
                        (window as any).google.accounts.id.initialize({
                            client_id: googleClientId,
                            callback: async (response: any) => {
                                try {
                                    await googleLogin(response.credential);
                                    routeAfterAuth();
                                    resolve();
                                } catch (err) { reject(err); }
                            },
                        });
                        (window as any).google.accounts.id.prompt();
                    };
                    script.onerror = () => reject(new Error('Failed to load Google Sign-In'));
                    document.head.appendChild(script);
                });
            } else {
                const mockToken = btoa(JSON.stringify({ sub: `google_${Date.now()}`, email: 'user@gmail.com', name: 'Google User' }));
                await googleLogin(mockToken);
                routeAfterAuth();
            }
        } catch (err: any) {
            setError(err?.message || 'Google sign-in failed');
            setLoading(false);
        }
    };

    const handleAppleOAuth = async () => {
        setLoading(true);
        setError('');
        try {
            const mockToken = btoa(JSON.stringify({ sub: `apple_${Date.now()}`, email: 'user@icloud.com', name: 'Apple User' }));
            await appleLogin(mockToken);
            routeAfterAuth();
        } catch (err: any) {
            setError(err?.message || 'Apple sign-in failed');
            setLoading(false);
        }
    };

    const busy = loading || authLoading;

    // Detect if user is returning as female to customize landing page experience
    const profile = JSON.parse(localStorage.getItem('smarty_profile') || '{}');
    const isFemaleDefault = profile.gender === 'Female' || profile.femmecareEnabled;
    const primaryAccent = isFemaleDefault ? 'pink' : 'emerald';
    const accentClass = isFemaleDefault ? 'text-pink-500' : 'text-emerald-400';
    const accentBg = isFemaleDefault ? 'bg-pink-500 hover:bg-pink-600' : 'bg-emerald-500 hover:bg-emerald-600';
    const accentGlow = isFemaleDefault ? 'shadow-pink-500/25' : 'shadow-emerald-500/20';

    return (
        <div className="min-h-screen bg-[#020617] text-white overflow-hidden font-sans selection:bg-emerald-500/30 selection:text-white">
            
            {/* Background Grid Pattern & Orbs */}
            <div className="absolute inset-0 z-0 opacity-20 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,_transparent_1px),_linear-gradient(90deg,_rgba(255,255,255,0.02)_1px,_transparent_1px)] bg-[size:40px_40px]" />
            <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-emerald-500/5 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2 pointer-events-none" />
            <div className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] bg-cyan-500/5 rounded-full blur-3xl translate-x-1/2 translate-y-1/2 pointer-events-none" />

            {/* Header */}
            <header className="sticky top-0 z-50 border-b border-white/5 bg-slate-950/80 backdrop-blur px-6 py-4 sm:px-10 lg:px-16">
                <div className="mx-auto flex max-w-7xl items-center justify-between">
<div className="flex items-center gap-3">
  <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${isFemaleDefault ? 'bg-pink-500' : 'bg-emerald-500'} text-slate-950 shadow-lg`}>
    <img src={brandLogo} alt="Smarty Logo" className="h-7 w-auto" />
  </div>
  <div>
    <h1 className="text-lg font-black italic tracking-tighter uppercase text-white">
      SMARTY <span className={accentClass}>AI</span>
    </h1>
    <p className="text-[7px] font-bold uppercase tracking-[0.4em] text-slate-500">
      {isFemaleDefault ? 'Femme Fitness v4.0' : 'Fit Intelligence'}
    </p>
  </div>
</div>
                    <button
                        onClick={() => { setIsRegister(!isRegister); setError(''); }}
                        className={`rounded-full ${accentBg} px-6 py-2.5 text-xs font-black uppercase tracking-widest text-slate-950 transition shadow-lg ${accentGlow}`}
                    >
                        {isRegister ? 'Sign In' : 'Create Account'}
                    </button>
                </div>
            </header>

            {/* 1. Cinematic Hero Section with Athlete Silhouette */}
            <section className="relative min-h-[90vh] flex items-center z-10 px-6 sm:px-10 lg:px-16 border-b border-white/5" style={{ backgroundImage: `url(${heroBg})`, backgroundSize: 'cover', backgroundPosition: 'center' }}>
                <div className="mx-auto max-w-7xl w-full grid lg:grid-cols-[1.2fr_420px] gap-16 py-12 items-center">
                    
                    {/* Hero copy */}
                    <div className="relative">
                        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-black uppercase tracking-widest text-slate-400 mb-6">
                            <Activity size={12} className={accentClass} />
                            Train Beyond Limits
                        </div>
                        <h2 className="text-5xl sm:text-7xl lg:text-8xl font-black italic uppercase tracking-tighter leading-none text-white">
                            JUST DO <span className={accentClass}>IT.</span><br />
                            INTELLIGENTLY.
                        </h2>
                        <p className="mt-6 max-w-xl text-sm sm:text-base leading-relaxed text-slate-400 font-medium">
                            The ultimate Nike-style fitness recommender platform. Track diet, construct elite personalized routines, sync training load dynamically to FemmeCare, and get updated instantly on the Neon Cloud DB.
                        </p>

                        {/* Interactive Athlete Dynamic SVG Visualizer */}
                        <div className="mt-8 relative w-full max-w-md h-32 border border-white/5 bg-slate-950/40 rounded-2xl overflow-hidden flex items-center px-6">
                            <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-emerald-500/10 to-transparent pointer-events-none" />
                            <div className="flex-1">
                                <p className="text-[10px] font-black uppercase tracking-widest text-slate-500">Biokinetic Alignment</p>
                                <p className="text-xl font-bold italic text-white mt-1">98.4% KINETIC INDEX</p>
                            </div>
                            <svg className="w-24 h-20 text-emerald-400" viewBox="0 0 100 50">
                                <path d="M10 25 L30 10 L50 40 L70 15 L90 35" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
                                <circle cx="90" cy="35" r="4" fill="white" />
                            </svg>
                        </div>
                    </div>

                    {/* Auth Card (Neon Direct Update) */}
                    <div className="w-full bg-slate-950/60 border border-white/10 rounded-3xl p-8 backdrop-blur-xl shadow-2xl relative">
                        <div className="absolute -top-3 -right-3 bg-slate-900 border border-white/10 text-slate-400 px-3 py-1 rounded-full text-[8px] font-black tracking-widest uppercase">
                            Neon Postgres Sync Active
                        </div>
                        <div className="mb-6">
                            <h3 className="text-2xl font-black italic uppercase tracking-tight text-white">
                                {isRegister ? 'Start Your Era' : 'Welcome Back'}
                            </h3>
                            <p className="mt-1.5 text-xs text-slate-500">
                                Connect credentials to pull personalized aims and goals instantly.
                            </p>
                        </div>

                        <form onSubmit={isRegister ? handleRegisterSubmit : handleLoginSubmit} className="space-y-4">
                            {isRegister && (
                                <div className="relative">
                                    <User size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                                    <input
                                        type="text"
                                        placeholder="Full Name"
                                        value={form.name}
                                        onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                                        required
                                        className="w-full bg-slate-900 border border-white/10 rounded-xl py-3.5 pl-11 pr-4 text-xs font-semibold text-white outline-none focus:border-emerald-500 transition placeholder:text-slate-600"
                                    />
                                </div>
                            )}
                            <div className="relative">
                                <Mail size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                                <input
                                    type="email"
                                    placeholder="Email Address"
                                    value={form.email}
                                    onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                                    required
                                    className="w-full bg-slate-900 border border-white/10 rounded-xl py-3.5 pl-11 pr-4 text-xs font-semibold text-white outline-none focus:border-emerald-500 transition placeholder:text-slate-600"
                                />
                            </div>
                            <div className="relative">
                                <Lock size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                                <input
                                    type={showPass ? 'text' : 'password'}
                                    placeholder="Password"
                                    value={form.password}
                                    onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                                    required
                                    className="w-full bg-slate-900 border border-white/10 rounded-xl py-3.5 pl-11 pr-11 text-xs font-semibold text-white outline-none focus:border-emerald-500 transition placeholder:text-slate-600"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPass(!showPass)}
                                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white"
                                >
                                    {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
                                </button>
                            </div>

                            {error && (
                                <p className="bg-rose-500/10 border border-rose-500/20 text-rose-400 px-4 py-2.5 rounded-xl text-xs font-bold text-center">
                                    {error}
                                </p>
                            )}

                            <button
                                type="submit"
                                disabled={busy}
                                className={`flex w-full items-center justify-center gap-2 rounded-xl ${accentBg} py-3.5 text-xs font-black uppercase tracking-widest text-slate-950 shadow-lg transition disabled:bg-slate-800 disabled:text-slate-500`}
                            >
                                {busy ? 'Syncing...' : isRegister ? 'Register' : 'Access Hub'}
                                <ArrowRight size={14} />
                            </button>
                        </form>

                        <div className="my-5 flex items-center gap-3">
                            <div className="h-px flex-1 bg-white/5" />
                            <span className="text-[8px] font-black uppercase tracking-widest text-slate-600">Secure Direct Access</span>
                            <div className="h-px flex-1 bg-white/5" />
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                            <button onClick={handleGoogleOAuth} className="rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 py-3 text-[10px] font-black uppercase tracking-wider text-slate-300 transition">
                                Google
                            </button>
                            <button onClick={handleAppleOAuth} className="rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 py-3 text-[10px] font-black uppercase tracking-wider text-slate-300 transition">
                                Apple
                            </button>
                        </div>

                        <button
                            onClick={handleGuest}
                            className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 border border-white/5 hover:bg-slate-800 py-3 text-[10px] font-black uppercase tracking-widest text-slate-400 transition"
                        >
                            Guest Mode
                        </button>
                    </div>
                </div>
            </section>

            {/* 2. Feature Reveal Section (Scroll-Triggered Reveal Animation) */}
            <section className="relative py-24 px-6 sm:px-10 lg:px-16 bg-slate-950/40">
                <div className="mx-auto max-w-7xl">
                    <div className="text-center mb-20">
                        <p className="text-[10px] font-black uppercase tracking-[0.4em] text-slate-500">Elite Performance Blueprint</p>
                        <h2 className="text-3xl sm:text-5xl font-black italic uppercase tracking-tighter text-white mt-2">
                            UNFOLD CORE INTEGRITY
                        </h2>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8">
                        {/* Feature 1 */}
                        <div className={`bg-slate-900/60 border border-white/10 p-8 rounded-3xl transition-all duration-700 transform ${scrollY > 150 ? 'translate-y-0 opacity-100' : 'translate-y-12 opacity-0'}`}>
                            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-6">
                                <Camera className="text-emerald-400" size={22} />
                            </div>
                            <h3 className="text-lg font-black uppercase tracking-tight text-white">AI FOOD SCANNER</h3>
                            <p className="text-xs text-slate-400 leading-relaxed mt-2.5">
                                Snapshot food items directly. Generates macro estimates with Gemini Vision, updating stats instantly on the cloud DB.
                            </p>
                        </div>

                        {/* Feature 2 */}
                        <div className={`bg-slate-900/60 border border-white/10 p-8 rounded-3xl transition-all duration-700 delay-100 transform ${scrollY > 150 ? 'translate-y-0 opacity-100' : 'translate-y-12 opacity-0'}`}>
                            <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mb-6">
                                <Dumbbell className="text-cyan-400" size={22} />
                            </div>
                            <h3 className="text-lg font-black uppercase tracking-tight text-white">GOAL RECOMMENDER</h3>
                            <p className="text-xs text-slate-400 leading-relaxed mt-2.5">
                                Algorithmic routine engine matching specific fitness aims. Every exercise is synced perfectly.
                            </p>
                        </div>

                        {/* Feature 3 */}
                        <div className={`bg-slate-900/60 border border-white/10 p-8 rounded-3xl transition-all duration-700 delay-200 transform ${scrollY > 150 ? 'translate-y-0 opacity-100' : 'translate-y-12 opacity-0'}`}>
                            <div className="w-12 h-12 rounded-xl bg-pink-500/10 border border-pink-500/20 flex items-center justify-center mb-6">
                                <HeartPulse className="text-pink-400" size={22} />
                            </div>
                            <h3 className="text-lg font-black uppercase tracking-tight text-white">FEMME CARE</h3>
                            <p className="text-xs text-slate-400 leading-relaxed mt-2.5">
                                Personalized cycle syncing with adaptive loading models. Turns entire dashboard interface soft-rose themed.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* 3. Social & Proof Banner */}
            <section className="py-16 border-t border-white/5 bg-[#020617] text-center px-6">
                <div className="max-w-4xl mx-auto flex flex-wrap justify-center gap-12 sm:gap-20">
                    <div>
                        <p className="text-4xl sm:text-5xl font-black italic text-white">10K+</p>
                        <p className="text-[8px] font-black uppercase tracking-widest text-slate-500 mt-1">OPERATORS ONLINE</p>
                    </div>
                    <div>
                        <p className="text-4xl sm:text-5xl font-black italic text-white">500+</p>
                        <p className="text-[8px] font-black uppercase tracking-widest text-slate-500 mt-1">ELITE EXERCISES</p>
                    </div>
                    <div>
                        <p className="text-4xl sm:text-5xl font-black italic text-white">100%</p>
                        <p className="text-[8px] font-black uppercase tracking-widest text-slate-500 mt-1">DATABASE INTEGRITY</p>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-8 border-t border-white/5 text-center text-[10px] text-slate-600 bg-slate-950/80">
                &copy; 2026 Smarty AI Inc. All Rights Reserved. Built for speed.
            </footer>
        </div>
    );
};

export default LoginPage;
