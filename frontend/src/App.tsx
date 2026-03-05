
import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Dumbbell, Utensils, Mic, MessageCircle,
  Menu, X, LogOut, Zap, Fingerprint, Camera, TrendingUp,
  Phone, User, ChevronRight
} from 'lucide-react';

// Pages
import LoginPage from './pages/LoginPage';
import OnboardingPage from './pages/OnboardingPage';
import ContactPage from './pages/ContactPage';

// Feature Components
import Dashboard from './Dashboard';
import WorkoutAssistant from './WorkoutAssistant';
import NutritionHub from './NutritionHub';
import LiveCoach from './LiveCoach';
import SmartyChat from './SmartyChat';
import BioLink from './BioLink';
import MealScanner from './MealScanner';
import ProgressTracking from './ProgressTracking';

// -- Auth Guard
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const user = localStorage.getItem('smarty_user');
  if (!user) return <Navigate to="/" replace />;
  return <>{children}</>;
};

// -- Dashboard shell with sidebar
const DashboardShell: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const user = JSON.parse(localStorage.getItem('smarty_user') || '{}');
  const profile = JSON.parse(localStorage.getItem('smarty_profile') || '{}');

  const navItems = [
    { path: '/dashboard', label: 'Mission Control', icon: LayoutDashboard, exact: true },
    { path: '/dashboard/food-scanner', label: 'Food Scanner', icon: Camera },
    { path: '/dashboard/workout', label: 'Workout Planner', icon: Dumbbell },
    { path: '/dashboard/nutrition', label: 'Nutrition Hub', icon: Utensils },
    { path: '/dashboard/progress', label: 'Progress', icon: TrendingUp },
    { path: '/dashboard/bio', label: 'Bio Profile', icon: Fingerprint },
    { path: '/dashboard/coach', label: 'Live Coach', icon: Mic },
    { path: '/contact', label: 'Contact', icon: Phone },
  ];

  const isActive = (item: typeof navItems[0]) => {
    if (item.exact) return location.pathname === item.path;
    return location.pathname.startsWith(item.path);
  };

  const handleSignOut = () => {
    localStorage.removeItem('smarty_user');
    navigate('/');
  };

  const goalLabel = profile.goal ? {
    weight_loss: '🔥 Weight Loss', muscle_gain: '💪 Muscle Gain',
    athletic: '⚡ Athletic', maintenance: '🎯 Maintenance'
  }[profile.goal as string] || profile.goal : null;

  return (
    <div className="flex h-screen bg-[#020617] overflow-hidden text-slate-200 selection:bg-emerald-500/30">
      {/* Sidebar */}
      <aside className="w-72 border-r border-white/5 flex-col hidden lg:flex bg-slate-950/20 backdrop-blur-2xl relative shrink-0">
        <div className="absolute top-0 right-0 w-[1px] h-full bg-gradient-to-b from-transparent via-emerald-500/20 to-transparent" />

        <div className="p-8">
          <div className="flex items-center space-x-4 group cursor-pointer" onClick={() => navigate('/dashboard')}>
            <div className="w-11 h-11 bg-emerald-500 rounded-2xl flex items-center justify-center text-slate-950 shadow-[0_0_20px_rgba(16,185,129,0.4)] transition-all group-hover:scale-110 rotate-3">
              <Zap size={22} className="fill-slate-950" />
            </div>
            <div>
              <h1 className="text-xl font-black italic tracking-tighter text-white">SMARTY <span className="text-emerald-400">AI</span></h1>
              <p className="text-[7px] font-black uppercase tracking-[0.4em] text-slate-500">Neural Fitness v4.0</p>
            </div>
          </div>

          {/* User pill */}
          {user.name && (
            <div className="mt-6 p-4 bg-white/5 border border-white/10 rounded-2xl">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 bg-emerald-500/20 rounded-xl flex items-center justify-center">
                  <User size={16} className="text-emerald-400" />
                </div>
                <div>
                  <p className="text-xs font-black text-white">{profile.name || user.name}</p>
                  {goalLabel && <p className="text-[9px] text-slate-500 mt-0.5">{goalLabel}</p>}
                </div>
              </div>
            </div>
          )}
        </div>

        <nav className="flex-1 px-5 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const active = isActive(item);
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center space-x-3 px-5 py-3.5 rounded-2xl transition-all relative group ${active
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-inner'
                  : 'text-slate-500 hover:text-slate-200 hover:bg-white/5 border border-transparent'}`}
              >
                <item.icon size={18} className={active ? 'text-emerald-400' : 'group-hover:text-emerald-400 transition-colors'} />
                <span className="font-black uppercase tracking-[0.12em] text-[10px]">{item.label}</span>
                {active && <div className="absolute right-4 w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]" />}
              </button>
            );
          })}
        </nav>

        <div className="p-5 border-t border-white/5">
          <button
            onClick={handleSignOut}
            className="w-full flex items-center space-x-3 px-5 py-3.5 text-rose-500/60 hover:text-rose-400 hover:bg-rose-500/5 rounded-2xl transition-colors"
          >
            <LogOut size={16} />
            <span className="font-black uppercase tracking-widest text-[9px]">Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {/* Topbar */}
        <header className="h-20 border-b border-white/5 flex items-center justify-between px-6 md:px-10 bg-[#020617]/40 backdrop-blur-3xl sticky top-0 z-40 shrink-0">
          <div className="flex items-center space-x-4">
            <button className="lg:hidden p-2.5 text-slate-400 bg-white/5 rounded-xl" onClick={() => setIsMobileMenuOpen(true)}>
              <Menu size={20} />
            </button>
            <div className="hidden sm:block">
              <p className="text-[9px] font-black uppercase tracking-widest text-slate-600">Current Module</p>
              <p className="text-sm font-black text-emerald-400 uppercase tracking-widest">
                {navItems.find(n => isActive(n))?.label || 'Dashboard'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            {goalLabel && (
              <div className="hidden md:flex items-center space-x-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
                <span className="text-[9px] font-black uppercase tracking-widest text-emerald-400">Goal: {goalLabel}</span>
              </div>
            )}
            <div className="w-11 h-11 rounded-2xl border border-white/20 bg-slate-900 flex items-center justify-center">
              <User size={18} className="text-emerald-400" />
            </div>
          </div>
        </header>

        {/* Content area */}
        <div className="flex-1 overflow-y-auto p-6 md:p-10 relative">
          <div className="absolute inset-0 opacity-[0.015] pointer-events-none" style={{ backgroundImage: 'linear-gradient(rgba(16,185,129,0.2) 1px, transparent 1px), linear-gradient(90deg, rgba(16,185,129,0.2) 1px, transparent 1px)', backgroundSize: '80px 80px' }} />
          <div className="relative z-10">
            <Routes>
              <Route index element={<Dashboard />} />
              <Route path="food-scanner" element={<MealScanner />} />
              <Route path="workout" element={<WorkoutAssistant />} />
              <Route path="nutrition" element={<NutritionHub />} />
              <Route path="progress" element={<ProgressTracking />} />
              <Route path="bio" element={<BioLink />} />
              <Route path="coach" element={<LiveCoach />} />
            </Routes>
          </div>
        </div>
      </main>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-slate-950/90 backdrop-blur-md" onClick={() => setIsMobileMenuOpen(false)} />
          <aside className="absolute top-0 left-0 bottom-0 w-72 bg-[#020617] border-r border-white/10 p-6 flex flex-col">
            <div className="flex items-center justify-between mb-8">
              <span className="text-xl font-black italic text-white">SMARTY <span className="text-emerald-400">AI</span></span>
              <button onClick={() => setIsMobileMenuOpen(false)} className="p-2 text-slate-500"><X size={20} /></button>
            </div>
            {user.name && (
              <div className="mb-6 p-4 bg-white/5 border border-white/10 rounded-2xl">
                <p className="text-sm font-black text-white">{profile.name || user.name}</p>
                {goalLabel && <p className="text-[10px] text-slate-500">{goalLabel}</p>}
              </div>
            )}
            <nav className="flex-1 space-y-2 overflow-y-auto">
              {navItems.map((item) => (
                <button key={item.path} onClick={() => { navigate(item.path); setIsMobileMenuOpen(false); }}
                  className={`w-full flex items-center space-x-3 p-4 rounded-2xl ${isActive(item) ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'text-slate-500'}`}>
                  <item.icon size={18} />
                  <span className="font-black text-[10px] uppercase tracking-widest">{item.label}</span>
                </button>
              ))}
            </nav>
            <button onClick={handleSignOut} className="flex items-center space-x-3 p-4 text-rose-400 mt-4">
              <LogOut size={16} />
              <span className="font-black text-[10px] uppercase tracking-widest">Sign Out</span>
            </button>
          </aside>
        </div>
      )}
    </div>
  );
};

// Root App with router
const App: React.FC = () => (
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<LoginPage />} />
      <Route path="/onboarding" element={<ProtectedRoute><OnboardingPage /></ProtectedRoute>} />
      <Route path="/contact" element={<ContactPage />} />
      <Route path="/dashboard/*" element={<ProtectedRoute><DashboardShell /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  </BrowserRouter>
);

export default App;
