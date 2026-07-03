import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Eye, EyeOff, Mail, Lock, User, Sparkles, ChevronRight, Activity, Brain, Target, Shield } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface LoginForm { name: string; email: string; password: string; }

const LoginPage: React.FC = () => {
    const navigate = useNavigate();
    const { login, register, googleLogin, appleLogin, loading: authLoading } = useAuth();
    const [isRegister, setIsRegister] = useState(false);
    const [showPass, setShowPass] = useState(false);
    const [form, setForm] = useState<LoginForm>({ name: '', email: '', password: '' });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleLoginSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            await login(form.email, form.password);
            const profile = localStorage.getItem('smarty_profile');
            navigate(profile ? '/dashboard' : '/onboarding');
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
            const profile = localStorage.getItem('smarty_profile');
            navigate(profile ? '/dashboard' : '/onboarding');
        } catch (err: any) {
            setError(err?.message || 'Registration failed');
        } finally {
            setLoading(false);
        }
    };

    const handleGuest = () => {
        localStorage.setItem('smarty_user', JSON.stringify({ name: 'Guest Operator', email: 'guest@smarty.ai', loggedIn: true }));
        const profile = localStorage.getItem('smarty_profile');
        navigate(profile ? '/dashboard' : '/onboarding');
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
                                    navigate(localStorage.getItem('smarty_profile') ? '/dashboard' : '/onboarding');
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
                navigate(localStorage.getItem('smarty_profile') ? '/dashboard' : '/onboarding');
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
            const appleClientId = import.meta.env.VITE_APPLE_CLIENT_ID;
            if (appleClientId) {
                const data = (window as any).AppleID?.auth?.signIn ? await (window as any).AppleID.auth.signIn() : null;
                if (data?.authorization?.id_token) {
                    await appleLogin(data.authorization.id_token, data.user?.name?.firstName ? `${data.user.name.firstName} ${data.user.name.lastName}` : undefined, data.user?.email);
                    navigate(localStorage.getItem('smarty_profile') ? '/dashboard' : '/onboarding');
                } else {
                    const mockToken = btoa(JSON.stringify({ sub: `apple_${Date.now()}`, email: 'user@icloud.com', name: 'Apple User' }));
                    await appleLogin(mockToken);
                    navigate(localStorage.getItem('smarty_profile') ? '/dashboard' : '/onboarding');
                }
            } else {
                const mockToken = btoa(JSON.stringify({ sub: `apple_${Date.now()}`, email: 'user@icloud.com', name: 'Apple User' }));
                await appleLogin(mockToken);
                navigate(localStorage.getItem('smarty_profile') ? '/dashboard' : '/onboarding');
            }
        } catch (err: any) {
            setError(err?.message || 'Apple sign-in failed');
            setLoading(false);
        }
    };

    const features = [
        { icon: Brain, title: 'AI Food Scanner', desc: 'Camera detects food, calories & macros instantly', color: 'text-blue-500 bg-blue-50' },
        { icon: Activity, title: 'Personalized Plans', desc: 'Workouts & diet tailored to your exact goal', color: 'text-emerald-500 bg-emerald-50' },
        { icon: Target, title: 'Progress Tracking', desc: 'Charts, streaks, and goal progress in real time', color: 'text-amber-500 bg-amber-50' },
        { icon: Shield, title: 'Live AI Coach', desc: 'Voice-powered fitness coaching, always on', color: 'text-rose-500 bg-rose-50' },
    ];

    return (
        <div className="min-h-screen bg-[#f8fafc] text-slate-800 flex overflow-hidden relative font-sans">
            {/* Dynamic CSS for Free-Flowing Google Fitness Shapes */}
            <style dangerouslySetInnerHTML={{__html: `
                @keyframes float-shape-1 {
                    0% { transform: translate(0px, 0px) scale(1); }
                    33% { transform: translate(40px, -60px) scale(1.1); }
                    66% { transform: translate(-30px, 30px) scale(0.95); }
                    100% { transform: translate(0px, 0px) scale(1); }
                }
                @keyframes float-shape-2 {
                    0% { transform: translate(0px, 0px) scale(1.05); }
                    50% { transform: translate(-50px, 50px) scale(0.9); }
                    100% { transform: translate(0px, 0px) scale(1.05); }
                }
                @keyframes float-shape-3 {
                    0% { transform: translate(0px, 0px) scale(0.9); }
                    40% { transform: translate(60px, 40px) scale(1.1); }
                    80% { transform: translate(-20px, -30px) scale(1); }
                    100% { transform: translate(0px, 0px) scale(0.9); }
                }
                .animate-blob-1 {
                    animation: float-shape-1 25s infinite ease-in-out;
                }
                .animate-blob-2 {
                    animation: float-shape-2 30s infinite ease-in-out;
                }
                .animate-blob-3 {
                    animation: float-shape-3 22s infinite ease-in-out;
                }
            `}} />

            {/* Free-Flowing Moving Shapes (Google Primary Colors at very low, clean opacity) */}
            <div className="absolute top-1/4 left-1/10 w-96 h-96 bg-blue-500/8 rounded-full blur-3xl animate-blob-1 pointer-events-none" />
            <div className="absolute top-2/3 right-1/4 w-80 h-80 bg-emerald-500/8 rounded-full blur-3xl animate-blob-2 pointer-events-none" />
            <div className="absolute bottom-1/10 left-1/3 w-108 h-108 bg-amber-500/6 rounded-full blur-3xl animate-blob-3 pointer-events-none" />
            <div className="absolute top-1/10 right-1/10 w-72 h-72 bg-rose-500/6 rounded-full blur-3xl animate-blob-1 pointer-events-none" />

            {/* Top-Right Toggle Button */}
            <div className="absolute top-8 right-8 z-20">
                <button 
                    onClick={() => { setIsRegister(!isRegister); setError(''); }}
                    className="px-5 py-2 rounded-full border border-slate-200 bg-white/80 text-slate-600 font-semibold text-xs uppercase tracking-wider hover:bg-slate-50 hover:text-slate-800 transition-all duration-300 shadow-sm backdrop-blur-sm"
                >
                    {isRegister ? 'Sign In' : 'Register'}
                </button>
            </div>

            <div className="hidden lg:flex flex-col justify-between w-1/2 p-16 relative overflow-hidden border-r border-slate-100 bg-white/40 backdrop-blur-sm">
                <div className="relative z-10">
                    <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-md">
                            <Zap size={22} className="text-white fill-white" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold tracking-tight text-slate-800">Smarty <span className="text-blue-600 font-extrabold">AI</span></h1>
                            <p className="text-[8px] font-bold uppercase tracking-widest text-slate-400">Fitness Intelligence Platform</p>
                        </div>
                    </div>
                </div>
                
                <div className="relative z-10 space-y-8 my-auto">
                    <div className="space-y-4">
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-600 border border-blue-100">
                            Fit OS v5
                        </span>
                        <h2 className="text-5xl font-extrabold tracking-tight text-slate-900 leading-tight">
                            Train with clarity.<br />Eat with confidence.<br /><span className="text-blue-600">Live with vitality.</span>
                        </h2>
                        <p className="text-slate-500 text-sm leading-relaxed max-w-md">
                            The world's most accessible fitness system. Snap meals for dynamic tracking, access custom training metrics, and explore personalized health goals inside a clean workspace.
                        </p>
                    </div>
                    <div className="grid grid-cols-2 gap-4 mt-8">
                        {features.map((f) => (
                            <div key={f.title} className="p-4 bg-white border border-slate-100 rounded-2xl hover:shadow-md hover:border-slate-200 transition-all group duration-300">
                                <div className={`w-8 h-8 rounded-lg flex items-center justify-center mb-3 ${f.color}`}>
                                    <f.icon size={16} />
                                </div>
                                <p className="text-xs font-bold text-slate-800">{f.title}</p>
                                <p className="text-[10px] text-slate-400 mt-1 leading-normal">{f.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
                
                <div className="relative z-10 flex items-center space-x-4 text-slate-400 text-[10px] font-semibold tracking-wider">
                    <span>© 2026 Smarty AI</span>
                    <span>•</span>
                    <span>Built by Aaditya Uniyal</span>
                </div>
            </div>

            <div className="flex-1 flex items-center justify-center p-8 relative">
                <div className="relative z-10 w-full max-w-sm space-y-6">
                    <div className="lg:hidden flex items-center space-x-3 mb-8">
                        <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center">
                            <Zap size={18} className="text-white fill-white" />
                        </div>
                        <h1 className="text-lg font-bold text-slate-800">Smarty <span className="text-blue-600">AI</span></h1>
                    </div>
                    <div>
                        <h2 className="text-3xl font-extrabold tracking-tight text-slate-900">
                            {isRegister ? 'Get Started' : 'Welcome back'}
                        </h2>
                        <p className="text-slate-400 text-xs mt-1">
                            {isRegister ? 'Create your account to unlock your dashboard.' : 'Sign in to access your workout and meal schedules.'}
                        </p>
                    </div>

                    <div className="relative w-full h-[280px]">
                        {/* Sign In Form */}
                        <form 
                            onSubmit={handleLoginSubmit} 
                            className={`absolute w-full space-y-3 transition-all duration-500 ease-in-out ${
                                isRegister ? '-translate-x-full opacity-0 pointer-events-none' : 'translate-x-0 opacity-100'
                            }`}
                        >
                            <div className="relative">
                                <Mail size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                                <input type="email" placeholder="Email address" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} required
                                    className="w-full bg-white border border-slate-200 rounded-xl py-3 pl-11 pr-4 text-xs text-slate-700 focus:outline-none focus:border-blue-500/60 focus:ring-4 focus:ring-blue-500/5 transition-all placeholder:text-slate-400" />
                            </div>
                            <div className="relative">
                                <Lock size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                                <input type={showPass ? 'text' : 'password'} placeholder="Password" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} required
                                    className="w-full bg-white border border-slate-200 rounded-xl py-3 pl-11 pr-11 text-xs text-slate-700 focus:outline-none focus:border-blue-500/60 focus:ring-4 focus:ring-blue-500/5 transition-all placeholder:text-slate-400" />
                                <button type="button" onClick={() => setShowPass(!showPass)} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition">
                                    {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
                                </button>
                            </div>
                            {error && !isRegister && <p className="text-rose-500 text-[10px] font-semibold">{error}</p>}
                            <button type="submit" disabled={loading || authLoading}
                                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-100 disabled:text-slate-400 text-white font-bold py-3.5 rounded-xl transition-all flex items-center justify-center space-x-2 shadow-md shadow-blue-600/10 active:scale-[0.98]">
                                {loading ? (
                                    <span className="text-xs uppercase tracking-wider animate-pulse">Signing in...</span>
                                ) : (
                                    <><Sparkles size={15} /><span className="text-xs uppercase tracking-wider">Login</span><ChevronRight size={15} /></>
                                )}
                            </button>
                        </form>

                        {/* Register Form */}
                        <form 
                            onSubmit={handleRegisterSubmit} 
                            className={`absolute w-full space-y-3 transition-all duration-500 ease-in-out ${
                                isRegister ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0 pointer-events-none'
                            }`}
                        >
                            <div className="relative">
                                <User size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                                <input type="text" placeholder="Your Name" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required={isRegister}
                                    className="w-full bg-white border border-slate-200 rounded-xl py-3 pl-11 pr-4 text-xs text-slate-700 focus:outline-none focus:border-blue-500/60 focus:ring-4 focus:ring-blue-500/5 transition-all placeholder:text-slate-400" />
                            </div>
                            <div className="relative">
                                <Mail size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                                <input type="email" placeholder="Email address" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} required
                                    className="w-full bg-white border border-slate-200 rounded-xl py-3 pl-11 pr-4 text-xs text-slate-700 focus:outline-none focus:border-blue-500/60 focus:ring-4 focus:ring-blue-500/5 transition-all placeholder:text-slate-400" />
                            </div>
                            <div className="relative">
                                <Lock size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                                <input type={showPass ? 'text' : 'password'} placeholder="Password" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} required
                                    className="w-full bg-white border border-slate-200 rounded-xl py-3 pl-11 pr-11 text-xs text-slate-700 focus:outline-none focus:border-blue-500/60 focus:ring-4 focus:ring-blue-500/5 transition-all placeholder:text-slate-400" />
                                <button type="button" onClick={() => setShowPass(!showPass)} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition">
                                    {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
                                </button>
                            </div>
                            {error && isRegister && <p className="text-rose-500 text-[10px] font-semibold">{error}</p>}
                            <button type="submit" disabled={loading || authLoading}
                                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-100 disabled:text-slate-400 text-white font-bold py-3.5 rounded-xl transition-all flex items-center justify-center space-x-2 shadow-md shadow-blue-600/10 active:scale-[0.98]">
                                {loading ? (
                                    <span className="text-xs uppercase tracking-wider animate-pulse">Initializing...</span>
                                ) : (
                                    <><Sparkles size={15} /><span className="text-xs uppercase tracking-wider">Create Account</span><ChevronRight size={15} /></>
                                )}
                            </button>
                        </form>
                    </div>

                    <div className="relative flex items-center gap-3 pt-2">
                        <div className="flex-1 h-px bg-slate-100" /><span className="text-slate-400 text-[9px] uppercase tracking-widest font-bold">or</span><div className="flex-1 h-px bg-slate-100" />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <button onClick={handleGoogleOAuth}
                            className="flex items-center justify-center space-x-2 px-3 py-2.5 rounded-xl border border-slate-100 bg-white hover:bg-slate-50 text-slate-500 font-bold text-[9px] uppercase tracking-wider transition-all shadow-sm">
                            <svg viewBox="0 0 24 24" className="w-3.5 h-3.5 shrink-0"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
                            <span>Google</span>
                        </button>
                        <button onClick={handleAppleOAuth}
                            className="flex items-center justify-center space-x-2 px-3 py-2.5 rounded-xl border border-slate-100 bg-white hover:bg-slate-50 text-slate-500 font-bold text-[9px] uppercase tracking-wider transition-all shadow-sm">
                            <svg viewBox="0 0 24 24" className="w-3.5 h-3.5 shrink-0"><path fill="currentColor" d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/></svg>
                            <span>Apple</span>
                        </button>
                    </div>

                    <button onClick={handleGuest}
                        className="w-full bg-white hover:bg-slate-50 border border-slate-200 text-slate-600 font-bold py-3 rounded-xl transition-all text-xs uppercase tracking-wider shadow-sm">
                        Continue as Guest
                    </button>
                    
                    <p className="text-center text-slate-400 text-xs">
                        {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
                        <button onClick={() => { setIsRegister(!isRegister); setError(''); }} className="text-blue-600 hover:text-blue-700 font-bold transition">
                            {isRegister ? 'Sign In' : 'Register'}
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
