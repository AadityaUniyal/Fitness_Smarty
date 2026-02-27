import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Eye, EyeOff, Mail, Lock, User, Sparkles, ChevronRight, Activity, Brain, Target, Shield } from 'lucide-react';

interface LoginForm { name: string; email: string; password: string; }

const LoginPage: React.FC = () => {
    const navigate = useNavigate();
    const [isRegister, setIsRegister] = useState(false);
    const [showPass, setShowPass] = useState(false);
    const [form, setForm] = useState<LoginForm>({ name: '', email: '', password: '' });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        // Simulate auth - store user info locally
        await new Promise(r => setTimeout(r, 800));
        const userData = { name: form.name || form.email.split('@')[0], email: form.email, loggedIn: true };
        localStorage.setItem('smarty_user', JSON.stringify(userData));
        // Check if onboarding done
        const profile = localStorage.getItem('smarty_profile');
        setLoading(false);
        if (profile) { navigate('/dashboard'); } else { navigate('/onboarding'); }
    };

    const handleGuest = () => {
        const userData = { name: 'Guest Operator', email: 'guest@smarty.ai', loggedIn: true };
        localStorage.setItem('smarty_user', JSON.stringify(userData));
        const profile = localStorage.getItem('smarty_profile');
        if (profile) { navigate('/dashboard'); } else { navigate('/onboarding'); }
    };

    const features = [
        { icon: Brain, title: 'AI Food Scanner', desc: 'Camera detects food, calories & macros instantly' },
        { icon: Activity, title: 'Personalized Plans', desc: 'Workouts & diet tailored to your exact goal' },
        { icon: Target, title: 'Progress Tracking', desc: 'Charts, streaks, and goal progress in real time' },
        { icon: Shield, title: 'Live AI Coach', desc: 'Voice-powered fitness coaching, always on' },
    ];

    return (
        <div className="min-h-screen bg-[#020617] text-white flex overflow-hidden">
            {/* Left — Hero */}
            <div className="hidden lg:flex flex-col justify-between w-1/2 p-16 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-emerald-950/40 via-transparent to-cyan-950/20" />
                <div className="absolute top-1/3 left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl animate-pulse" />
                <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl animate-pulse delay-700" />

                <div className="relative z-10">
                    <div className="flex items-center space-x-4">
                        <div className="w-14 h-14 bg-emerald-500 rounded-3xl flex items-center justify-center shadow-[0_0_30px_rgba(16,185,129,0.5)] rotate-3">
                            <Zap size={30} className="fill-slate-950 text-slate-950" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-black italic tracking-tighter">SMARTY <span className="text-emerald-400">AI</span></h1>
                            <p className="text-[9px] font-black uppercase tracking-[0.4em] text-slate-500">Your Personal Fitness Intelligence</p>
                        </div>
                    </div>
                </div>

                <div className="relative z-10 space-y-6">
                    <div className="space-y-3">
                        <p className="text-[10px] font-black uppercase tracking-[0.4em] text-emerald-400">Neural Fitness System</p>
                        <h2 className="text-6xl font-black italic tracking-tighter leading-none">
                            Train Smarter.<br />
                            <span className="text-emerald-400">Eat Smarter.</span><br />
                            Live Better.
                        </h2>
                        <p className="text-slate-400 text-sm leading-relaxed max-w-md mt-4">
                            The world's most advanced AI fitness companion. Scan food with your camera, get personalised workout plans, track every metric, and stay coached — 24/7.
                        </p>
                    </div>

                    <div className="grid grid-cols-2 gap-4 mt-8">
                        {features.map((f) => (
                            <div key={f.title} className="p-5 bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm hover:bg-white/8 transition-all group">
                                <f.icon size={20} className="text-emerald-400 mb-3 group-hover:scale-110 transition-transform" />
                                <p className="text-sm font-black text-white">{f.title}</p>
                                <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">{f.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="relative z-10 flex items-center space-x-6 text-slate-600 text-[10px] font-black uppercase tracking-widest">
                    <span>© 2025 Smarty AI</span>
                    <span>•</span>
                    <span>Built by Aaditya Uniyal</span>
                </div>
            </div>

            {/* Right — Auth Form */}
            <div className="flex-1 flex items-center justify-center p-8 relative">
                <div className="absolute inset-0 bg-gradient-to-b from-slate-950/50 to-slate-950" />

                <div className="relative z-10 w-full max-w-md space-y-8">
                    {/* Mobile Logo */}
                    <div className="lg:hidden flex items-center space-x-3 mb-8">
                        <div className="w-10 h-10 bg-emerald-500 rounded-2xl flex items-center justify-center">
                            <Zap size={22} className="fill-slate-950 text-slate-950" />
                        </div>
                        <h1 className="text-2xl font-black italic text-white">SMARTY <span className="text-emerald-400">AI</span></h1>
                    </div>

                    <div>
                        <h2 className="text-4xl font-black italic text-white tracking-tighter">
                            {isRegister ? 'Create Account' : 'Welcome Back'}
                        </h2>
                        <p className="text-slate-400 text-sm mt-2">
                            {isRegister ? 'Begin your fitness transformation journey.' : 'Your neural uplink is waiting.'}
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {isRegister && (
                            <div className="relative">
                                <User size={16} className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-500" />
                                <input
                                    type="text"
                                    placeholder="Your Name"
                                    value={form.name}
                                    onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                                    className="w-full bg-slate-900 border border-white/10 rounded-2xl py-4 pl-12 pr-5 text-sm focus:outline-none focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/10 transition-all placeholder:text-slate-600"
                                />
                            </div>
                        )}
                        <div className="relative">
                            <Mail size={16} className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-500" />
                            <input
                                type="email"
                                placeholder="Email address"
                                value={form.email}
                                onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                                required
                                className="w-full bg-slate-900 border border-white/10 rounded-2xl py-4 pl-12 pr-5 text-sm focus:outline-none focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/10 transition-all placeholder:text-slate-600"
                            />
                        </div>
                        <div className="relative">
                            <Lock size={16} className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-500" />
                            <input
                                type={showPass ? 'text' : 'password'}
                                placeholder="Password"
                                value={form.password}
                                onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                                required
                                className="w-full bg-slate-900 border border-white/10 rounded-2xl py-4 pl-12 pr-12 text-sm focus:outline-none focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/10 transition-all placeholder:text-slate-600"
                            />
                            <button type="button" onClick={() => setShowPass(!showPass)} className="absolute right-5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition">
                                {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                            </button>
                        </div>

                        {error && <p className="text-rose-400 text-xs font-medium">{error}</p>}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-800 text-slate-950 font-black py-4 rounded-2xl transition-all flex items-center justify-center space-x-3 shadow-[0_10px_30px_rgba(16,185,129,0.3)] active:scale-[0.98]"
                        >
                            {loading ? (
                                <span className="text-sm uppercase tracking-widest animate-pulse">Connecting...</span>
                            ) : (
                                <>
                                    <Sparkles size={18} />
                                    <span className="text-sm uppercase tracking-widest">{isRegister ? 'Create Account' : 'Login'}</span>
                                    <ChevronRight size={18} />
                                </>
                            )}
                        </button>
                    </form>

                    <div className="relative flex items-center gap-4">
                        <div className="flex-1 h-px bg-white/10" />
                        <span className="text-slate-600 text-[10px] uppercase tracking-widest font-black">or</span>
                        <div className="flex-1 h-px bg-white/10" />
                    </div>

                    <button
                        onClick={handleGuest}
                        className="w-full bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 font-black py-4 rounded-2xl transition-all text-sm uppercase tracking-widest"
                    >
                        Continue as Guest
                    </button>

                    <p className="text-center text-slate-500 text-sm">
                        {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
                        <button onClick={() => setIsRegister(!isRegister)} className="text-emerald-400 hover:text-emerald-300 font-black transition">
                            {isRegister ? 'Sign In' : 'Register'}
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
