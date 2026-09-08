import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Activity,
    ArrowRight,
    Camera,
    Dumbbell,
    Eye,
    EyeOff,
    HeartPulse,
    Lock,
    Mail,
    User,
    Zap,
    CheckCircle2
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { use3DTilt } from '../hooks/use3DTilt';
import heroBg from '../assets/hero_background.png';

interface LoginForm { name: string; email: string; password: string; }

const LoginPage: React.FC = () => {
    const navigate = useNavigate();
    const { user, login, register, googleLogin, appleLogin, loading: authLoading } = useAuth();
    const [isRegister, setIsRegister] = useState(false);
    const [showPass, setShowPass] = useState(false);
    const [form, setForm] = useState<LoginForm>({ name: '', email: '', password: '' });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [acceptDisclaimer, setAcceptDisclaimer] = useState(false);
    
    // 3D tilt hooks for cards
    const authCardTilt = use3DTilt<HTMLDivElement>({ maxTilt: 6, scale: 1.01 });
    const featureCard1Tilt = use3DTilt<HTMLDivElement>({ maxTilt: 8 });
    const featureCard2Tilt = use3DTilt<HTMLDivElement>({ maxTilt: 8 });
    const featureCard3Tilt = use3DTilt<HTMLDivElement>({ maxTilt: 8 });

    // Smooth scroll reveals state
    const [scrollY, setScrollY] = useState(0);

    useEffect(() => {
        const handleScroll = () => setScrollY(window.scrollY);
        window.addEventListener('scroll', handleScroll, { passive: true });
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const routeAfterAuth = (userObj?: any) => {
        const u = userObj || user;
        if (u?.is_admin) {
            navigate('/admin');
            return;
        }
        navigate('/onboarding');
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
        localStorage.setItem('smarty_user', JSON.stringify({ name: 'Guest Athlete', email: 'guest@smarty.ai', loggedIn: true }));
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
    const accentClass = 'text-emerald-400';
    const accentBg = 'bg-emerald-500 hover:bg-emerald-400';
    const accentGlow = 'shadow-emerald-500/20';

    return (
        <div className="min-h-screen bg-[#020617] text-white overflow-hidden font-sans selection:bg-emerald-500/30 selection:text-white">
            
            {/* Background Ambient Canvas */}
            <div className="fixed inset-0 z-0 opacity-25 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,_transparent_1px),_linear-gradient(90deg,_rgba(255,255,255,0.02)_1px,_transparent_1px)] bg-[size:48px_48px] pointer-events-none" />
            <div className="fixed top-1/4 left-1/4 w-[500px] h-[500px] bg-emerald-500/10 rounded-full blur-[100px] -translate-x-1/2 -translate-y-1/2 pointer-events-none" />
            <div className="fixed bottom-1/4 right-1/4 w-[600px] h-[600px] bg-cyan-500/10 rounded-full blur-[120px] translate-x-1/2 translate-y-1/2 pointer-events-none" />

            {/* Header */}
            <header className="sticky top-0 z-50 border-b border-white/5 bg-slate-950/80 backdrop-blur-xl px-6 py-4 sm:px-10 lg:px-16">
                <div className="mx-auto flex max-w-7xl items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/30 card-3d">
                            <Zap className="h-6 w-auto fill-slate-950" />
                        </div>
                        <div>
                            <h1 className="text-xl font-black italic tracking-tighter uppercase text-white">
                                SMARTY <span className={accentClass}>AI</span>
                            </h1>
                            <p className="text-[8px] font-black uppercase tracking-[0.35em] text-slate-400">
                                TRAIN INTELLIGENTLY
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={() => { setIsRegister(!isRegister); setError(''); }}
                        className={`rounded-full ${accentBg} px-6 py-2.5 text-xs font-black uppercase tracking-widest text-slate-950 transition-all shadow-lg ${accentGlow} active:scale-95`}
                    >
                        {isRegister ? 'Sign In' : 'Create Account'}
                    </button>
                </div>
            </header>

            {/* 1. Cinematic Hero Section */}
            <section className="relative min-h-[88vh] flex items-center z-10 px-6 sm:px-10 lg:px-16 border-b border-white/5" style={{ backgroundImage: `url(${heroBg})`, backgroundSize: 'cover', backgroundPosition: 'center' }}>
                <div className="absolute inset-0 bg-gradient-to-r from-slate-950/90 via-slate-950/70 to-slate-950/80 pointer-events-none" />
                
                <div className="relative z-10 mx-auto max-w-7xl w-full grid lg:grid-cols-[1.2fr_420px] gap-16 py-12 items-center">
                    
                    {/* Hero copy */}
                    <div className="relative">
                        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-black uppercase tracking-widest text-slate-300 mb-6">
                            <Activity size={14} className={accentClass} />
                            Precision Athletic Intelligence
                        </div>
                        <h2 className="text-5xl sm:text-7xl lg:text-8xl font-black italic uppercase tracking-tighter leading-none text-white">
                            YOUR BODY.<br />
                            YOUR DATA.<br />
                            <span className={accentClass}>YOUR RULES.</span>
                        </h2>
                        <p className="mt-6 max-w-xl text-base leading-relaxed text-slate-300 font-medium">
                            An intelligent fitness platform designed for peak performance. Dynamic meal scanning, adaptive workout programming, and FemmeCare cycle alignment — engineered to elevate your potential.
                        </p>

                        {/* Interactive Athlete Dynamic Visualizer */}
                        <div className="mt-8 relative w-full max-w-md h-28 border border-white/10 bg-slate-950/60 rounded-2xl overflow-hidden flex items-center px-6 backdrop-blur-md card-3d">
                            <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-emerald-500/15 to-transparent pointer-events-none" />
                            <div className="flex-1">
                                <p className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-400">Biomechanic Alignment</p>
                                <p className="text-xl font-black italic text-white mt-1">98.4% OPTIMAL EFFICIENCY</p>
                            </div>
                            <svg className="w-24 h-16 text-emerald-400" viewBox="0 0 100 50">
                                <path d="M10 30 L30 15 L50 35 L70 10 L90 25" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
                                <circle cx="90" cy="25" r="4" fill="#34d399" className="animate-ping" />
                                <circle cx="90" cy="25" r="4" fill="white" />
                            </svg>
                        </div>
                    </div>

                    {/* Auth Card with 3D Tilt */}
                    <div 
                        ref={authCardTilt.ref as any}
                        style={authCardTilt.style}
                        onMouseMove={authCardTilt.onMouseMove as any}
                        onMouseLeave={authCardTilt.onMouseLeave as any}
                        className="w-full bg-slate-950/80 border border-white/10 rounded-3xl p-8 backdrop-blur-2xl shadow-2xl relative card-3d"
                    >
                        <div className="card-3d-shine" />
                        <div className="mb-6">
                            <h3 className="text-2xl font-black italic uppercase tracking-tight text-white">
                                {isRegister ? 'Begin Your Training' : 'Sign In to Smarty'}
                            </h3>
                            <p className="mt-1.5 text-xs text-slate-400">
                                Access your personalized training plans and daily nutrition stats.
                            </p>
                        </div>

                        <form onSubmit={isRegister ? handleRegisterSubmit : handleLoginSubmit} className="space-y-4">
                            {isRegister && (
                                <div className="relative">
                                    <User size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                                    <input
                                        type="text"
                                        placeholder="Full Name"
                                        value={form.name}
                                        onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                                        required
                                        className="w-full bg-slate-900/90 border border-white/10 rounded-xl py-3.5 pl-11 pr-4 text-xs font-semibold text-white outline-none focus:border-emerald-500 transition placeholder:text-slate-500"
                                    />
                                </div>
                            )}
                            <div className="relative">
                                <Mail size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                                <input
                                    type="email"
                                    placeholder="Email Address"
                                    value={form.email}
                                    onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                                    required
                                    className="w-full bg-slate-900/90 border border-white/10 rounded-xl py-3.5 pl-11 pr-4 text-xs font-semibold text-white outline-none focus:border-emerald-500 transition placeholder:text-slate-500"
                                />
                            </div>
                            <div className="relative">
                                <Lock size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                                <input
                                    type={showPass ? 'text' : 'password'}
                                    placeholder="Password"
                                    value={form.password}
                                    onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                                    required
                                    className="w-full bg-slate-900/90 border border-white/10 rounded-xl py-3.5 pl-11 pr-11 text-xs font-semibold text-white outline-none focus:border-emerald-500 transition placeholder:text-slate-500"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPass(!showPass)}
                                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                                >
                                    {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                                </button>
                            </div>

                            {isRegister && (
                                <div className="flex items-start gap-2.5 bg-slate-900/60 border border-white/10 p-3 rounded-xl">
                                    <input
                                        type="checkbox"
                                        id="disclaimer"
                                        checked={acceptDisclaimer}
                                        onChange={e => setAcceptDisclaimer(e.target.checked)}
                                        className="mt-0.5 accent-emerald-500 rounded cursor-pointer"
                                        required
                                    />
                                    <label htmlFor="disclaimer" className="text-[10px] text-slate-300 leading-snug cursor-pointer select-none">
                                        I understand that Smarty AI provides fitness and nutritional guidance, which is NOT medical advice.
                                    </label>
                                </div>
                            )}

                            {error && (
                                <p className="bg-rose-500/10 border border-rose-500/20 text-rose-400 px-4 py-2.5 rounded-xl text-xs font-bold text-center">
                                    {error}
                                </p>
                            )}

                            <button
                                type="submit"
                                disabled={busy || (isRegister && !acceptDisclaimer)}
                                className={`flex w-full items-center justify-center gap-2 rounded-xl ${accentBg} py-3.5 text-xs font-black uppercase tracking-widest text-slate-950 shadow-lg transition disabled:bg-slate-800 disabled:text-slate-500`}
                            >
                                {busy ? 'Connecting...' : isRegister ? 'Register Account' : 'Sign In'}
                                <ArrowRight size={16} />
                            </button>
                        </form>

                        <div className="my-5 flex items-center gap-3">
                            <div className="h-px flex-1 bg-white/10" />
                            <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">Quick Sign In</span>
                            <div className="h-px flex-1 bg-white/10" />
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                            <button onClick={handleGoogleOAuth} className="rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 py-3 text-xs font-bold text-slate-200 transition">
                                Google
                            </button>
                            <button onClick={handleAppleOAuth} className="rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 py-3 text-xs font-bold text-slate-200 transition">
                                Apple
                            </button>
                        </div>

                        <button
                            onClick={handleGuest}
                            className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 border border-white/5 hover:bg-slate-800 py-3 text-xs font-black uppercase tracking-widest text-slate-400 transition"
                        >
                            Explore as Guest
                        </button>

                        <div className="mt-4 text-center">
                            <button
                                type="button"
                                onClick={() => { setIsRegister(!isRegister); setError(''); }}
                                className="text-xs font-bold text-slate-400 hover:text-white transition"
                            >
                                {isRegister ? 'Already have an account? Sign In' : "Don't have an account? Create Account"}
                            </button>
                        </div>
                    </div>
                </div>
            </section>

            {/* 2. Feature Cards Section */}
            <section className="relative py-24 px-6 sm:px-10 lg:px-16 bg-slate-950/60">
                <div className="mx-auto max-w-7xl">
                    <div className="text-center mb-16">
                        <p className="text-xs font-black uppercase tracking-[0.35em] text-slate-400">INTELLIGENT ATHLETIC ARCHITECTURE</p>
                        <h2 className="text-3xl sm:text-5xl font-black italic uppercase tracking-tighter text-white mt-2">
                            POWERED BY DYNAMIC DATA
                        </h2>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8">
                        {/* Feature 1 */}
                        <div 
                            ref={featureCard1Tilt.ref as any}
                            style={featureCard1Tilt.style}
                            onMouseMove={featureCard1Tilt.onMouseMove as any}
                            onMouseLeave={featureCard1Tilt.onMouseLeave as any}
                            className={`bg-slate-900/80 border border-white/10 p-8 rounded-3xl transition-all duration-700 card-3d ${scrollY > 150 ? 'translate-y-0 opacity-100' : 'translate-y-12 opacity-0'}`}
                        >
                            <div className="card-3d-shine" />
                            <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-6 text-emerald-400 shadow-md">
                                <Camera size={22} />
                            </div>
                            <h3 className="text-lg font-black uppercase tracking-tight text-white">AI MEAL SCANNER</h3>
                            <p className="text-xs text-slate-400 leading-relaxed mt-2.5">
                                Instantly scan food items with your camera. Get instant protein, macro, and calorie breakdowns logged directly to your daily goal.
                            </p>
                        </div>

                        {/* Feature 2 */}
                        <div 
                            ref={featureCard2Tilt.ref as any}
                            style={featureCard2Tilt.style}
                            onMouseMove={featureCard2Tilt.onMouseMove as any}
                            onMouseLeave={featureCard2Tilt.onMouseLeave as any}
                            className={`bg-slate-900/80 border border-white/10 p-8 rounded-3xl transition-all duration-700 delay-100 card-3d ${scrollY > 150 ? 'translate-y-0 opacity-100' : 'translate-y-12 opacity-0'}`}
                        >
                            <div className="card-3d-shine" />
                            <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mb-6 text-cyan-400 shadow-md">
                                <Dumbbell size={22} />
                            </div>
                            <h3 className="text-lg font-black uppercase tracking-tight text-white">ADAPTIVE WORKOUTS</h3>
                            <p className="text-xs text-slate-400 leading-relaxed mt-2.5">
                                Dynamic workout plans calibrated to your exact targets — weight loss, muscle gain, or athletic performance.
                            </p>
                        </div>

                        {/* Feature 3 */}
                        <div 
                            ref={featureCard3Tilt.ref as any}
                            style={featureCard3Tilt.style}
                            onMouseMove={featureCard3Tilt.onMouseMove as any}
                            onMouseLeave={featureCard3Tilt.onMouseLeave as any}
                            className={`bg-slate-900/80 border border-white/10 p-8 rounded-3xl transition-all duration-700 delay-200 card-3d ${scrollY > 150 ? 'translate-y-0 opacity-100' : 'translate-y-12 opacity-0'}`}
                        >
                            <div className="card-3d-shine" />
                            <div className="w-12 h-12 rounded-2xl bg-pink-500/10 border border-pink-500/20 flex items-center justify-center mb-6 text-pink-400 shadow-md">
                                <HeartPulse size={22} />
                            </div>
                            <h3 className="text-lg font-black uppercase tracking-tight text-white">FEMME CARE SYNC</h3>
                            <p className="text-xs text-slate-400 leading-relaxed mt-2.5">
                                Cycle-aware workout adjustments and specialized nutritional recommendations tailored to your hormonal recovery state.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* 3. Social Proof */}
            <section className="py-16 border-t border-white/5 bg-[#020617] text-center px-6">
                <div className="max-w-4xl mx-auto flex flex-wrap justify-center gap-12 sm:gap-20">
                    <div>
                        <p className="text-4xl sm:text-5xl font-black italic text-white">10K+</p>
                        <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mt-1">ACTIVE ATHLETES</p>
                    </div>
                    <div>
                        <p className="text-4xl sm:text-5xl font-black italic text-white">500+</p>
                        <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mt-1">EXERCISE EXAMPLES</p>
                    </div>
                    <div>
                        <p className="text-4xl sm:text-5xl font-black italic text-white">100%</p>
                        <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mt-1">DATA PRIVACY</p>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-8 border-t border-white/5 text-center text-xs text-slate-500 bg-slate-950/80">
                &copy; 2026 SMARTY AI Inc. All Rights Reserved. Train Intelligently.
            </footer>
        </div>
    );
};

export default LoginPage;
