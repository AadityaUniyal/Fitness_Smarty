
import React, { useState, Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Dumbbell, Utensils, Mic, MessageCircle,
  Menu, X, LogOut, Zap, Fingerprint, Camera, TrendingUp,
  Phone, User, Heart, Bot, Droplets, Activity, Calendar, Trophy,
  Moon, Image, Clock, Brain, BrainCircuit, CalendarDays, Bell, Download, Footprints, Users, Watch, Move, BookOpen, Sun
} from 'lucide-react';

// Static imports (needed for initial render or auth)
import LoginPage from './pages/LoginPage';
import OnboardingPage from './pages/OnboardingPage';
import ContactPage from './pages/ContactPage';
import NotificationScheduler from './components/NotificationScheduler';
import ErrorBoundary from './components/ErrorBoundary';
import ToastContainer from './components/ToastContainer';
import PageTransition from './components/PageTransition';
import { useToast } from './hooks/useToast';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { i18n } from './i18n';


// Lazy-loaded page components
const Dashboard = lazy(() => import('./pages/Dashboard'));
const ExerciseBrowser = lazy(() => import('./components/ExerciseBrowser'));
const WorkoutAssistant = lazy(() => import('./pages/WorkoutAssistant'));
const NutritionHub = lazy(() => import('./pages/NutritionHub'));
const LiveCoach = lazy(() => import('./pages/LiveCoach'));
const SmartyChat = lazy(() => import('./components/SmartyChat'));
const HydrationHub = lazy(() => import('./components/HydrationHub'));
const BioLink = lazy(() => import('./pages/BioLink'));
const MealScanner = lazy(() => import('./pages/MealScanner'));
const ProgressTracking = lazy(() => import('./pages/ProgressTracking'));
const FemmeCare = lazy(() => import('./pages/FemmeCare'));
const FemaleDashboard = lazy(() => import('./pages/FemaleDashboard'));
const FeedbackPage = lazy(() => import('./pages/FeedbackPage'));
const BodyMeasurements = lazy(() => import('./pages/BodyMeasurements'));
const WeeklyReview = lazy(() => import('./pages/WeeklyReview'));
const Achievements = lazy(() => import('./pages/Achievements'));
const MoodTracker = lazy(() => import('./pages/MoodTracker'));
const QuickWorkout = lazy(() => import('./pages/QuickWorkout'));
const ProgressPhotos = lazy(() => import('./pages/ProgressPhotos'));
const SleepTracker = lazy(() => import('./pages/SleepTracker'));
const WorkoutHistory = lazy(() => import('./pages/WorkoutHistory'));
const TrainingDashboard = lazy(() => import('./pages/TrainingDashboard'));
const MealPlanner = lazy(() => import('./pages/MealPlanner'));
const Reminders = lazy(() => import('./pages/Reminders'));
const ExportPage = lazy(() => import('./pages/ExportPage'));
const ActivityTracker = lazy(() => import('./pages/ActivityTracker'));
const SocialFeed = lazy(() => import('./pages/SocialFeed'));
const WearableIntegrations = lazy(() => import('./pages/WearableIntegrations'));
const FormCorrector = lazy(() => import('./pages/FormCorrector'));
const AiInterpreter = lazy(() => import('./pages/AiInterpreter'));

// -- Auth Guard
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="min-h-screen bg-[#020617] flex items-center justify-center"><div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" /></div>;
  if (!isAuthenticated) {
    const guest = localStorage.getItem('smarty_user');
    if (!guest) return <Navigate to="/" replace />;
  }
  return <>{children}</>;
};

// -- Dashboard shell with sidebar
const DashboardShell: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { toasts, dismissToast } = useToast();
  const user = JSON.parse(localStorage.getItem('smarty_user') || '{}');
  const profile = JSON.parse(localStorage.getItem('smarty_profile') || '{}');
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('smarty_theme');
    return saved || 'dark';
  });

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    localStorage.setItem('smarty_theme', nextTheme);
  };

  React.useEffect(() => {
    if (theme === 'light') {
      document.documentElement.classList.add('light');
    } else {
      document.documentElement.classList.remove('light');
    }
  }, [theme]);

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, exact: true },
    { path: '/dashboard/food-scanner', label: 'Food Scanner', icon: Camera },
    { path: '/dashboard/workout', label: 'Workouts', icon: Dumbbell },
    { path: '/dashboard/exercises', label: 'Exercise Library', icon: BookOpen },
    { path: '/dashboard/quick', label: 'Quick Workout', icon: Zap },
    { path: '/dashboard/activity', label: 'Activity', icon: Footprints },
    { path: '/dashboard/photos', label: 'Progress Photos', icon: Image },
    { path: '/dashboard/sleep', label: 'Sleep', icon: Moon },
    { path: '/dashboard/meal-planner', label: 'Meal Plan', icon: CalendarDays },
    { path: '/dashboard/reminders', label: 'Reminders', icon: Bell },
    { path: '/dashboard/export', label: 'Export', icon: Download },
    { path: '/dashboard/social', label: 'Social', icon: Users },
    { path: '/dashboard/wearables', label: 'Wearables', icon: Watch },
    { path: '/dashboard/form-coach', label: 'Form Coach', icon: Move },
    { path: '/dashboard/history', label: 'History', icon: Clock },
    { path: '/dashboard/nutrition', label: 'Nutrition', icon: Utensils },
    { path: '/dashboard/progress', label: 'Progress', icon: TrendingUp },
    { path: '/dashboard/body', label: 'Measurements', icon: Activity },
    { path: '/dashboard/achievements', label: 'Achievements', icon: Trophy },
    { path: '/dashboard/mood', label: 'Mood & Energy', icon: Heart },
    { path: '/dashboard/weekly', label: 'Weekly Review', icon: Calendar },
    { path: '/dashboard/bio', label: 'Profile', icon: Fingerprint },
    { path: '/dashboard/coach', label: 'Voice Coach', icon: Mic },
    { path: '/dashboard/chat', label: 'Chat', icon: Bot },
    { path: '/dashboard/hydration', label: 'Hydration', icon: Droplets },
    { path: '/dashboard/femmecare', label: 'FemmeCare', icon: Heart },
    { path: '/dashboard/female', label: 'Femme Hub', icon: Heart },
    { path: '/dashboard/training', label: 'Training', icon: Brain },
    { path: '/dashboard/interpreter', label: 'AI Interpreter', icon: BrainCircuit },
    { path: '/dashboard/feedback', label: 'Feedback', icon: MessageCircle },
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
            <button 
              className="lg:hidden p-2.5 text-slate-400 bg-white/5 rounded-xl" 
              onClick={() => setSidebarOpen(true)}
              aria-label="Open mobile navigation menu"
            >
              <Menu size={20} />
            </button>
            <div className="hidden sm:block">
              <p className="text-[9px] font-black uppercase tracking-widest text-slate-600">Current</p>
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
            <button
              onClick={() => {
                const nextLang = i18n.getLanguage() === 'en' ? 'hi' : 'en';
                i18n.setLanguage(nextLang);
                window.location.reload();
              }}
              className="px-3 py-2 text-xs font-black uppercase rounded-2xl border border-white/10 hover:border-white/20 bg-slate-900 text-slate-400 hover:text-emerald-400 transition-colors"
              title="Change Language / भाषा बदलें"
              aria-label="Change translation locale language"
            >
              {i18n.getLanguage() === 'en' ? 'EN' : 'HI'}
            </button>
            <button
              onClick={toggleTheme}
              className="w-11 h-11 rounded-2xl border border-white/10 hover:border-white/20 bg-slate-900 flex items-center justify-center text-slate-400 hover:text-emerald-400 transition-colors"
              title="Toggle Theme"
              aria-label="Toggle light and dark color themes"
            >
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <div className="w-11 h-11 rounded-2xl border border-white/20 bg-slate-900 flex items-center justify-center" aria-label="User avatar profile placeholder">
              <User size={18} className="text-emerald-400" />
            </div>
          </div>


        </header>

        {/* Content area */}
        <NotificationScheduler />
        <div className="flex-1 overflow-y-auto p-6 md:p-10 relative">
          <div className="absolute inset-0 opacity-[0.015] pointer-events-none" style={{ backgroundImage: 'linear-gradient(rgba(16,185,129,0.2) 1px, transparent 1px), linear-gradient(90deg, rgba(16,185,129,0.2) 1px, transparent 1px)', backgroundSize: '80px 80px' }} />
          <div className="relative z-10">
            <Suspense fallback={<div className="flex items-center justify-center min-h-[60vh]"><div className="w-10 h-10 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" /></div>}>
              <PageTransition>
                <Routes>
                  <Route index element={<Dashboard />} />
                  <Route path="food-scanner" element={<MealScanner />} />
                  <Route path="workout" element={<WorkoutAssistant />} />
                  <Route path="quick" element={<QuickWorkout />} />
                  <Route path="activity" element={<ActivityTracker />} />
                  <Route path="photos" element={<ProgressPhotos />} />
                  <Route path="sleep" element={<SleepTracker />} />
                  <Route path="meal-planner" element={<MealPlanner />} />
                  <Route path="reminders" element={<Reminders />} />
                  <Route path="export" element={<ExportPage />} />
                  <Route path="social" element={<SocialFeed />} />
                  <Route path="wearables" element={<WearableIntegrations />} />
                  <Route path="form-coach" element={<FormCorrector />} />
                  <Route path="history" element={<WorkoutHistory />} />
                  <Route path="nutrition" element={<NutritionHub />} />
                  <Route path="exercises" element={<ExerciseBrowser />} />
                  <Route path="progress" element={<ProgressTracking />} />
                  <Route path="body" element={<BodyMeasurements />} />
                  <Route path="weekly" element={<WeeklyReview />} />
                  <Route path="achievements" element={<Achievements />} />
                  <Route path="mood" element={<MoodTracker />} />
                  <Route path="training" element={<TrainingDashboard />} />
                  <Route path="interpreter" element={<AiInterpreter />} />
                  <Route path="bio" element={<BioLink />} />
                  <Route path="coach" element={<LiveCoach />} />
                  <Route path="chat" element={<SmartyChat />} />
                  <Route path="hydration" element={<div className="max-w-2xl mx-auto pt-6"><HydrationHub /></div>} />
                  <Route path="femmecare" element={<FemmeCare />} />
                  <Route path="female" element={<FemaleDashboard />} />
                  <Route path="feedback" element={<FeedbackPage />} />
                </Routes>
              </PageTransition>
            </Suspense>
          </div>
        </div>
      </main>

      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Mobile Menu */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-slate-950/90 backdrop-blur-md" onClick={() => setSidebarOpen(false)} />
          <aside className="absolute top-0 left-0 bottom-0 w-72 bg-[#020617] border-r border-white/10 p-6 flex flex-col">
            <div className="flex items-center justify-between mb-8">
              <span className="text-xl font-black italic text-white">SMARTY <span className="text-emerald-400">AI</span></span>
              <button onClick={() => setSidebarOpen(false)} className="p-2 text-slate-500"><X size={20} /></button>
            </div>
            {user.name && (
              <div className="mb-6 p-4 bg-white/5 border border-white/10 rounded-2xl">
                <p className="text-sm font-black text-white">{profile.name || user.name}</p>
                {goalLabel && <p className="text-[10px] text-slate-500">{goalLabel}</p>}
              </div>
            )}
            <nav className="flex-1 space-y-2 overflow-y-auto">
              {navItems.map((item) => (
                <button key={item.path} onClick={() => { navigate(item.path); setSidebarOpen(false); }}
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
  <ErrorBoundary>
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route path="/onboarding" element={<ProtectedRoute><OnboardingPage /></ProtectedRoute>} />
          <Route path="/contact" element={<ContactPage />} />
          <Route path="/dashboard/*" element={<ProtectedRoute><DashboardShell /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  </ErrorBoundary>
);

export default App;
