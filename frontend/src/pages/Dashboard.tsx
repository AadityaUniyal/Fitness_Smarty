import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity, Flame, TrendingUp, Zap, Target, BrainCircuit,
  ShieldCheck, Cpu, CheckCircle2, Circle, Fingerprint, Dumbbell, Trophy,
  Droplets, Apple, ArrowRight, Camera, Play, CalendarCheck, Moon, Gauge, Heart
} from 'lucide-react';
import { AreaChart, Area, ResponsiveContainer } from 'recharts';
import { fetchRecoveryScore, fetchNeuralIntegrity, fetchMissionBriefing, fetchDailyCoach } from '../services/api';
import { DailyTask } from '../types';
import SmartNextMove from '../components/SmartNextMove';
import DailyChecklist from '../components/DailyChecklist';
import AnimatedNumber from '../components/AnimatedNumber';
import { Reveal } from '../components/Reveal';

interface WorkoutLog { name: string; duration: number; caloriesBurned: number; exercisesCompleted: number; exercisesTotal: number; timestamp: string; goal: string; }
interface MealLog { mealName: string; totalCalories: number; totalProtein: number; totalCarbs: number; totalFats: number; mealType: string; timestamp: string; }

const statColors: Record<string, { border: string; bg: string; text: string; icon: string }> = {
  orange: { border: 'border-orange-500/20', bg: 'bg-orange-500/10', text: 'text-orange-400', icon: 'text-orange-400' },
  amber: { border: 'border-amber-500/20', bg: 'bg-amber-500/10', text: 'text-amber-400', icon: 'text-amber-400' },
  blue: { border: 'border-blue-500/20', bg: 'bg-blue-500/10', text: 'text-blue-400', icon: 'text-blue-400' },
  emerald: { border: 'border-emerald-500/20', bg: 'bg-emerald-500/10', text: 'text-emerald-400', icon: 'text-emerald-400' },
  cyan: { border: 'border-cyan-500/20', bg: 'bg-cyan-500/10', text: 'text-cyan-400', icon: 'text-cyan-400' },
  purple: { border: 'border-purple-500/20', bg: 'bg-purple-500/10', text: 'text-purple-400', icon: 'text-purple-400' },
  rose: { border: 'border-rose-500/20', bg: 'bg-rose-500/10', text: 'text-rose-400', icon: 'text-rose-400' },
};

const clampPct = (value: number, target: number) => Math.min(100, Math.max(0, Math.round((value / Math.max(target, 1)) * 100)));

const ConcentricProgressRing: React.FC<{
  todayCalEaten: number;
  todayCalsBurned: number;
  calorieGoal: number;
  todayMinutes: number;
  workoutGoalMins: number;
}> = ({
  todayCalEaten,
  todayCalsBurned,
  calorieGoal,
  todayMinutes,
  workoutGoalMins,
}) => {
  const remainingCal = Math.max(0, calorieGoal - todayCalEaten + todayCalsBurned);
  
  const calBurnedPct = Math.min(100, Math.max(0, Math.round((todayCalsBurned / calorieGoal) * 100)));
  const minutesPct = Math.min(100, Math.max(0, Math.round((todayMinutes / workoutGoalMins) * 100)));
  
  const r1 = 90; 
  const c1 = 2 * Math.PI * r1;
  const offset1 = c1 - (c1 * calBurnedPct) / 100;
  
  const r2 = 70; 
  const c2 = 2 * Math.PI * r2;
  const offset2 = c2 - (c2 * minutesPct) / 100;

  return (
    <div className="flex flex-col items-center justify-center p-8 bg-slate-950/60 border border-white/10 rounded-[2.5rem] backdrop-blur-xl relative overflow-hidden group">
      <div className="absolute inset-0 opacity-[0.02] pointer-events-none bg-[radial-gradient(#10b981_1px,transparent_0)] bg-[size:16px_16px]"></div>
      <div className="relative w-64 h-64">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 256 256">
          {/* Outer Ring (Emerald - Calories Burned) */}
          <circle cx="128" cy="128" r={r1} stroke="rgba(16, 185, 129, 0.05)" strokeWidth="12" fill="none" />
          <circle
            cx="128"
            cy="128"
            r={r1}
            stroke="#10b981"
            strokeWidth="12"
            fill="none"
            strokeDasharray={c1}
            strokeDashoffset={offset1}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
          
          {/* Inner Ring (Orange - Active Minutes) */}
          <circle cx="128" cy="128" r={r2} stroke="rgba(249, 115, 22, 0.05)" strokeWidth="12" fill="none" />
          <circle
            cx="128"
            cy="128"
            r={r2}
            stroke="#f97316"
            strokeWidth="12"
            fill="none"
            strokeDasharray={c2}
            strokeDashoffset={offset2}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-500">Remaining</span>
          <span className="text-4xl font-black italic tracking-tighter text-white my-1">
            {remainingCal}
          </span>
          <span className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-400">Calories</span>
        </div>
      </div>
      
      <div className="flex flex-wrap justify-center gap-6 mt-6">
        <div className="flex items-center space-x-2.5">
          <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.4)]" />
          <div>
            <span className="block text-[8px] font-black uppercase tracking-widest text-slate-500">Burned</span>
            <span className="text-xs font-black text-white">{todayCalsBurned} / {calorieGoal} kcal</span>
          </div>
        </div>
        <div className="flex items-center space-x-2.5">
          <div className="w-3 h-3 rounded-full bg-orange-500 shadow-[0_0_10px_rgba(249,115,22,0.4)]" />
          <div>
            <span className="block text-[8px] font-black uppercase tracking-widest text-slate-500">Active Mins</span>
            <span className="text-xs font-black text-white">{todayMinutes} / {workoutGoalMins} min</span>
          </div>
        </div>
      </div>
    </div>
  );
};

const MetricSparkline: React.FC<{
  data: { value: number }[];
  color: string;
}> = ({ data, color }) => {
  return (
    <div className="w-full h-10 mt-3 overflow-hidden rounded-lg">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 2, right: 2, left: 2, bottom: 2 }}>
          <defs>
            <linearGradient id={`grad-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={1.5}
            fillOpacity={1}
            fill={`url(#grad-${color.replace('#', '')})`}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

const MetricCard: React.FC<{
  label: string;
  value: number;
  target: number;
  unit: string;
  colorName: string;
  colorHex: string;
  icon: React.ElementType;
  history: { value: number }[];
  subText: string;
}> = ({ label, value, target, unit, colorName, colorHex, icon: Icon, history, subText }) => {
  const pct = Math.min(100, Math.max(0, Math.round((value / Math.max(target, 1)) * 100)));
  const colors = statColors[colorName] || statColors.emerald;

  return (
    <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-5 backdrop-blur-sm relative overflow-hidden group hover:border-white/20 transition-all duration-300">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">{label}</span>
        <Icon size={16} className={`${colors.text}`} />
      </div>
      
      <div className="mt-3 flex items-baseline justify-between">
        <div>
          <span className="text-2xl font-black italic text-white">
            {value.toFixed(0)}
          </span>
          <span className="text-[10px] text-slate-500 ml-1">
            / {target.toFixed(0)}{unit}
          </span>
        </div>
        <span className={`text-xs font-black italic ${colors.text}`}>
          {pct}%
        </span>
      </div>

      <MetricSparkline data={history} color={colorHex} />
      
      <div className="mt-2.5 flex items-center justify-between text-[9px] font-bold text-slate-500 uppercase tracking-wider">
        <span>{subText}</span>
      </div>
    </div>
  );
};

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<DailyTask[]>([]);
  const [recovery, setRecovery] = useState<any>(null);
  const [integrity, setIntegrity] = useState<any>(null);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [briefing, setBriefing] = useState<any>(null);
  const [dailyCoach, setDailyCoach] = useState<any>(null);
  const [typedBriefing, setTypedBriefing] = useState('');
  const [briefingIndex, setBriefingIndex] = useState(0);
  const [femmeData, setFemmeData] = useState<any>(null);

  const user = JSON.parse(localStorage.getItem('smarty_user') || '{}');
  const workoutLogs: WorkoutLog[] = JSON.parse(localStorage.getItem('smarty_workout_logs') || '[]');
  const mealLogs: MealLog[] = JSON.parse(localStorage.getItem('smarty_meal_logs') || '[]');
  const profile = JSON.parse(localStorage.getItem('smarty_profile') || localStorage.getItem('bio_profile') || '{}');
  const hydrationMl = Number(localStorage.getItem('smarty_hydration_ml') || 0);
  const today = new Date().toDateString();
  const todayWorkouts = workoutLogs.filter(w => new Date(w.timestamp).toDateString() === today);
  const todayMeals = mealLogs.filter(m => new Date(m.timestamp).toDateString() === today);
  const todayCalsBurned = todayWorkouts.reduce((s, w) => s + (w.caloriesBurned || 0), 0);
  const todayCalEaten = todayMeals.reduce((s, m) => s + (m.totalCalories || 0), 0);
  const todayProtein = todayMeals.reduce((s, m) => s + (m.totalProtein || 0), 0);
  const todayMinutes = todayWorkouts.reduce((s, w) => s + (Number(w.duration) || 0), 0);
  const calorieGoal = Number(profile.dailyCalorieGoal || profile.calorieGoal || 2200);
  const proteinGoal = Number(profile.proteinGoal || Math.max(90, Math.round((Number(profile.weight || profile.weight_kg) || 75) * 1.6)));
  const hydrationGoal = Number(profile.hydrationGoalMl || 3000);
  const workoutGoalMins = Number(profile.workoutGoalMins || 45);
  const profileFields = [
    profile.age,
    profile.gender,
    profile.weight || profile.weight_kg,
    profile.height || profile.height_cm,
    profile.goal || profile.primary_goal,
    profile.activityLevel || profile.activity_level,
  ];
  const profileCompletion = Math.round((profileFields.filter(Boolean).length / profileFields.length) * 100);
  const completedTasks = tasks.filter(t => t.completed).length;
  const taskPct = tasks.length ? Math.round((completedTasks / tasks.length) * 100) : 0;
  const readinessScore = recovery?.score || 85;
  const focusLabel = dailyCoach?.focus_area || integrity?.focus_area || (todayWorkouts.length ? 'Recovery walk' : 'First workout');
  const localNextAction = todayWorkouts.length === 0
    ? { title: 'Start a focused workout', detail: `${workoutGoalMins} min target for today`, path: '/dashboard/quick', icon: Play }
    : todayMeals.length < 3
      ? { title: 'Log your next meal', detail: `${Math.max(0, proteinGoal - todayProtein).toFixed(0)}g protein left`, path: '/dashboard/food-scanner', icon: Camera }
      : hydrationMl < hydrationGoal
        ? { title: 'Top up hydration', detail: `${Math.max(0, hydrationGoal - hydrationMl)} ml left`, path: '/dashboard/hydration', icon: Droplets }
        : { title: 'Review progress', detail: 'Your day is in good shape', path: '/dashboard/progress', icon: TrendingUp };
  const nextAction = dailyCoach?.next_action
    ? {
        title: dailyCoach.next_action.title || localNextAction.title,
        detail: dailyCoach.next_action.detail || localNextAction.detail,
        path: dailyCoach.next_action.route || localNextAction.path,
        icon: localNextAction.icon,
      }
    : localNextAction;
  const quickActions = [
    { label: 'Workout', path: '/dashboard/quick', icon: Dumbbell, color: 'text-orange-400' },
    { label: 'Scan Meal', path: '/dashboard/food-scanner', icon: Camera, color: 'text-emerald-400' },
    { label: 'Hydrate', path: '/dashboard/hydration', icon: Droplets, color: 'text-cyan-400' },
    { label: 'Sleep', path: '/dashboard/sleep', icon: Moon, color: 'text-indigo-400' },
  ];
  const workoutStreak = (() => {
    let streak = 0; let d = new Date();
    while (streak < 30) {
      if (workoutLogs.some(w => new Date(w.timestamp).toDateString() === d.toDateString())) streak++;
      else break;
      d.setDate(d.getDate() - 1);
    }
    return streak;
  })();
  const weekCalData = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(); d.setDate(d.getDate() - (6 - i));
    const ds = d.toDateString();
    return { v: workoutLogs.filter(w => new Date(w.timestamp).toDateString() === ds).reduce((s, w) => s + (w.caloriesBurned || 0), 0) };
  });

  const last7Days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (6 - i));
    return d;
  });

  const calEatenHistory = last7Days.map((date, idx) => {
    if (idx === 6) return { value: todayCalEaten };
    const ds = date.toDateString();
    const dayMeals = mealLogs.filter(m => new Date(m.timestamp).toDateString() === ds);
    return { value: dayMeals.reduce((s, m) => s + (m.totalCalories || 0), 0) || [1800, 2100, 1950, 2200, 1700, 2050][idx] };
  });

  const calBurnedHistory = last7Days.map((date, idx) => {
    if (idx === 6) return { value: todayCalsBurned };
    const ds = date.toDateString();
    const dayWorkouts = workoutLogs.filter(w => new Date(w.timestamp).toDateString() === ds);
    return { value: dayWorkouts.reduce((s, w) => s + (w.caloriesBurned || 0), 0) || [350, 480, 200, 520, 150, 400][idx] };
  });

  const proteinHistory = last7Days.map((date, idx) => {
    if (idx === 6) return { value: todayProtein };
    const ds = date.toDateString();
    const dayMeals = mealLogs.filter(m => new Date(m.timestamp).toDateString() === ds);
    return { value: dayMeals.reduce((s, m) => s + (m.totalProtein || 0), 0) || [80, 110, 95, 120, 75, 105][idx] };
  });

  const hydrationHistory = last7Days.map((date, idx) => {
    if (idx === 6) return { value: hydrationMl };
    return { value: [2500, 2800, 2000, 3100, 2400, 2900][idx] || 2000 };
  });

  const sleepHistory = last7Days.map((date, idx) => {
    return { value: [7.2, 8.0, 6.5, 7.8, 8.2, 7.0, 7.5][idx] || 7.5 };
  });

  const streakHistory = last7Days.map((date, idx) => {
    const ds = date.toDateString();
    const active = workoutLogs.some(w => new Date(w.timestamp).toDateString() === ds);
    return { value: active ? 100 : 0 };
  });

  useEffect(() => {
    fetchRecoveryScore().then(setRecovery).catch(() => {});
    fetchNeuralIntegrity().then(setIntegrity).catch(() => {});
    fetchMissionBriefing().then(setBriefing).catch(() => {});
    setLoadingTasks(true);
    fetchDailyCoach({
      profile,
      today: {
        calories_eaten: todayCalEaten,
        calories_burned: todayCalsBurned,
        protein_g: todayProtein,
        hydration_ml: hydrationMl,
        workout_minutes: todayMinutes,
        workouts_logged: todayWorkouts.length,
        meals_logged: todayMeals.length,
        recovery_score: recovery?.score,
      },
      recent_workouts: workoutLogs.slice(0, 5),
      recent_meals: mealLogs.slice(0, 5),
    }).then(data => {
      setDailyCoach(data);
      if (Array.isArray(data.tasks)) setTasks(data.tasks);
    }).finally(() => setLoadingTasks(false));
    const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');
    setLoadingRecs(true);
    fetch(`${API_BASE}/api/users/user-1/recommendations`)
      .then(res => res.json())
      .then(data => setRecommendations(data.recommendations || []))
      .catch(() => {})
      .finally(() => setLoadingRecs(false));
  }, []);

  useEffect(() => {
    if (briefing?.directive && briefingIndex < briefing.directive.length) {
      const timeout = setTimeout(() => {
        setTypedBriefing(prev => prev + briefing.directive[briefingIndex]);
        setBriefingIndex(prev => prev + 1);
      }, 30);
      return () => clearTimeout(timeout);
    }
  }, [briefing, briefingIndex]);

  useEffect(() => {
    if (profile.gender === 'Female' && (profile.femmecareEnabled || profile.femmecare_enabled)) {
      const uId = user.id || 1;
      const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');
      fetch(`${API_BASE}/api/female/cycle-phase/${uId}`)
        .then(res => {
          if (res.ok) return res.json();
          throw new Error('Not found');
        })
        .then(data => setFemmeData(data))
        .catch(() => {});
    }
  }, [profile, user.id]);

  const toggleTask = (id: string) => {
    setTasks(prev => prev.map(t => t.id === id ? { ...t, completed: !t.completed } : t));
  };

  const stats = [
    { label: 'Kcal Burned Today', value: todayCalsBurned, unit: 'kcal', color: 'orange', icon: Flame, sub: `${todayWorkouts.length} workout${todayWorkouts.length !== 1 ? 's' : ''}` },
    { label: 'Kcal Eaten Today', value: todayCalEaten, unit: 'kcal', color: 'amber', icon: Activity, sub: `${todayMeals.length} meals logged` },
    { label: 'Protein Today', value: todayProtein, unit: 'g', color: 'blue', icon: Zap, sub: 'consumed', isAnimated: true },
    { label: 'Workout Streak', value: workoutStreak, unit: 'days', color: 'emerald', icon: Trophy, sub: workoutStreak > 0 ? 'Keep it up!' : 'Start today!' },
  ];

  return (
    <div className="space-y-10">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center space-x-6">
          <div className="w-16 h-16 rounded-2xl border-2 border-emerald-500/30 bg-slate-900 flex items-center justify-center text-emerald-500 card-hover">
            <Cpu size={32} />
          </div>
          <div>
            <h2 className="text-4xl font-black text-white italic tracking-tighter uppercase">Mission Control</h2>
            <div className="flex items-center space-x-3 mt-1">
              <span className="text-[10px] font-black uppercase tracking-widest text-emerald-400 px-2 py-1 bg-emerald-500/10 rounded flex items-center">
                <ShieldCheck size={12} className="mr-1" /> Core Synced
              </span>
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 italic">User-Node: 0xALEX</span>
            </div>
          </div>
        </div>
      </div>

      <Reveal animation="fade-in-up">
        <section className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-slate-950/70">
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-400/60 to-transparent" />
          <div className="grid gap-0 lg:grid-cols-12">
            <div className="border-b border-white/10 p-6 md:p-8 lg:col-span-5 lg:border-b-0 lg:border-r">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-[10px] font-black uppercase tracking-widest text-emerald-300">
                    <CalendarCheck size={13} />
                    Today Hub
                  </div>
                  <h3 className="text-3xl font-black italic tracking-tight text-white md:text-4xl">
                    {new Date().toLocaleDateString(undefined, { weekday: 'long' })}
                  </h3>
                  <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">
                    {dailyCoach?.summary || (todayWorkouts.length || todayMeals.length
                      ? `You have logged ${todayWorkouts.length} workout${todayWorkouts.length === 1 ? '' : 's'} and ${todayMeals.length} meal${todayMeals.length === 1 ? '' : 's'} today.`
                      : 'Start with one useful action and the rest of the day gets easier to steer.')}
                  </p>
                </div>
                <div className="hidden rounded-2xl border border-white/10 bg-white/5 p-4 text-right sm:block">
                  <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">Readiness</p>
                  <p className="mt-1 text-3xl font-black italic text-emerald-300">{readinessScore.toFixed(0)}</p>
                </div>
              </div>

              <button
                onClick={() => navigate(nextAction.path)}
                className="mt-8 w-full rounded-2xl border border-emerald-500/30 bg-emerald-500 px-5 py-4 text-left text-slate-950 transition hover:bg-emerald-400"
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-950 text-emerald-300">
                      <nextAction.icon size={19} />
                    </span>
                    <span>
                      <span className="block text-sm font-black uppercase tracking-wide">{nextAction.title}</span>
                      <span className="block text-xs font-bold text-slate-800">{nextAction.detail}</span>
                    </span>
                  </div>
                  <ArrowRight size={20} />
                </div>
              </button>

              <div className="mt-5 grid grid-cols-4 gap-2">
                {quickActions.map(action => (
                  <button
                    key={action.label}
                    onClick={() => navigate(action.path)}
                    className="group flex min-h-20 flex-col items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-center transition hover:border-white/20 hover:bg-white/[0.06]"
                    title={action.label}
                  >
                    <action.icon size={18} className={`${action.color} transition group-hover:scale-110`} />
                    <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">{action.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="p-6 md:p-8 lg:col-span-7 flex flex-col justify-center">
              <ConcentricProgressRing
                todayCalEaten={todayCalEaten}
                todayCalsBurned={todayCalsBurned}
                calorieGoal={calorieGoal}
                todayMinutes={todayMinutes}
                workoutGoalMins={workoutGoalMins}
              />
            </div>
          </div>

              <div className="mt-5 grid gap-4 md:grid-cols-3">
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Profile</span>
                    <Gauge size={16} className="text-emerald-400" />
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-slate-900">
                    <div className="h-full rounded-full bg-emerald-400 transition-all" style={{ width: `${profileCompletion}%` }} />
                  </div>
                  <p className="mt-2 text-xs font-bold text-slate-300">{profileCompletion}% complete</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Protocol</span>
                    <CheckCircle2 size={16} className="text-purple-400" />
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-slate-900">
                    <div className="h-full rounded-full bg-purple-400 transition-all" style={{ width: `${taskPct}%` }} />
                  </div>
                  <p className="mt-2 text-xs font-bold text-slate-300">{completedTasks}/{tasks.length || 0} tasks done</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Focus</span>
                    <Target size={16} className="text-rose-400" />
                  </div>
                  <p className="truncate text-sm font-black italic text-white">{focusLabel}</p>
                  <p className="mt-1 text-[10px] font-bold uppercase tracking-widest text-slate-600">Next best area</p>
                </div>
              </div>
            </section>
          </Reveal>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Main Column */}
        <div className="lg:col-span-8 space-y-8">
          {/* Neural Checklist */}
          <Reveal animation="fade-in-up">
            <div className="glass-panel p-10 rounded-[3rem] border border-white/5 relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-emerald-500/20 to-transparent"></div>
              <div className="flex items-center justify-between mb-8">
                <div>
                  <h3 className="text-2xl font-black text-white italic tracking-tighter">Daily Protocol</h3>
                  <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em]">Computed for Current State</p>
                </div>
                <div className="px-4 py-2 bg-slate-950 border border-white/10 rounded-xl text-[9px] font-black text-slate-500 uppercase tracking-widest">AI Refresh: 24h</div>
              </div>
              <div className="space-y-4 stagger-children">
                {loadingTasks ? (
                  <div className="space-y-4">
                    {Array.from({ length: 3 }).map((_, i) => (
                      <div key={i} className="flex items-center justify-between p-6 rounded-2xl border border-white/5 bg-slate-950/30 animate-pulse">
                        <div className="flex items-center space-x-6">
                          <div className="w-6 h-6 rounded-full bg-slate-800" />
                          <div className="space-y-2">
                            <div className="h-4 w-32 bg-slate-800 rounded" />
                            <div className="h-3 w-20 bg-slate-800 rounded" />
                          </div>
                        </div>
                        <div className="h-5 w-16 bg-slate-800 rounded" />
                      </div>
                    ))}
                  </div>
                ) : tasks.length > 0 ? (
                  tasks.map((task) => (
                    <div key={task.id} onClick={() => toggleTask(task.id)}
                      className={`card-hover flex items-center justify-between p-6 rounded-2xl border cursor-pointer ${task.completed ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-slate-950 border-white/5 hover:border-emerald-500/30'}`}>
                      <div className="flex items-center space-x-6">
                        {task.completed ? <CheckCircle2 className="text-emerald-500 count-pop" /> : <Circle className="text-slate-800" />}
                        <div>
                          <p className={`text-sm font-black italic uppercase tracking-tight ${task.completed ? 'text-emerald-400/50 line-through' : 'text-white'}`}>{task.label}</p>
                          <p className="text-[9px] font-black text-slate-600 uppercase tracking-widest mt-1">Scheduled: {task.time}</p>
                        </div>
                      </div>
                      <span className={`text-[8px] font-black uppercase px-2 py-1 rounded border ${task.priority === 'High' ? 'border-rose-500/30 text-rose-500' : 'border-slate-800 text-slate-600'}`}>
                        {task.priority} Priority
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="p-8 text-center text-slate-600 uppercase text-[10px] font-black tracking-widest">Initialize Bio-Link to generate daily protocol.</div>
                )}
              </div>
            </div>
          </Reveal>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 stagger-children">
            <MetricCard
              label="Calories Eaten"
              value={todayCalEaten}
              target={calorieGoal}
              unit=" kcal"
              colorName="amber"
              colorHex="#f59e0b"
              icon={Apple}
              history={calEatenHistory}
              subText={`${todayMeals.length} meals logged`}
            />
            <MetricCard
              label="Calories Burned"
              value={todayCalsBurned}
              target={calorieGoal}
              unit=" kcal"
              colorName="orange"
              colorHex="#f97316"
              icon={Flame}
              history={calBurnedHistory}
              subText={`${todayWorkouts.length} workouts logged`}
            />
            <MetricCard
              label="Hydration"
              value={hydrationMl}
              target={hydrationGoal}
              unit=" ml"
              colorName="cyan"
              colorHex="#06b6d4"
              icon={Droplets}
              history={hydrationHistory}
              subText={`Target: ${hydrationGoal} ml`}
            />
            <MetricCard
              label="Sleep"
              value={sleepHistory[6].value}
              target={8}
              unit=" hrs"
              colorName="purple"
              colorHex="#8b5cf6"
              icon={Moon}
              history={sleepHistory}
              subText="Target: 8.0 hrs"
            />
            <MetricCard
              label="Protein"
              value={todayProtein}
              target={proteinGoal}
              unit=" g"
              colorName="blue"
              colorHex="#3b82f6"
              icon={Zap}
              history={proteinHistory}
              subText={`${todayProtein.toFixed(0)}g / ${proteinGoal}g`}
            />
            <MetricCard
              label="Workout Streak"
              value={workoutStreak}
              target={30}
              unit=" days"
              colorName="emerald"
              colorHex="#10b981"
              icon={Trophy}
              history={streakHistory}
              subText={workoutStreak > 0 ? "Keep it up!" : "Start today!"}
            />
          </div>

          {/* Readiness & Integrity */}
          <Reveal animation="fade-in-up" delay={150}>
            <div className="glass-panel p-10 rounded-[3rem] border border-white/5 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-8 text-white/5 group-hover:text-emerald-500/10 transition-colors">
                <Fingerprint size={120} />
              </div>
              <div className="flex items-center space-x-4 mb-8">
                <div className="p-4 bg-emerald-500/10 rounded-2xl text-emerald-400 border border-emerald-500/20">
                  <ShieldCheck size={28} />
                </div>
                <div>
                  <h3 className="text-2xl font-black text-white italic tracking-tighter uppercase">Readiness & Integrity</h3>
                  <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em]">Bio-Analytical Core v5.0</p>
                </div>
              </div>

              <div className="mb-10 p-6 bg-slate-950 border border-emerald-500/20 rounded-2xl relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-emerald-500 to-transparent animate-pulse"></div>
                <div className="flex items-center space-x-2 mb-3">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" style={{ animationDuration: '2s' }}></div>
                  <span className="text-[10px] font-black text-emerald-500 uppercase tracking-widest">Incoming Mission Briefing...</span>
                </div>
                <p className="font-mono text-emerald-400 text-sm leading-relaxed min-h-[3em]">
                  {typedBriefing}<span className="animate-pulse">|</span>
                </p>
                <div className="mt-4 flex items-center justify-between">
                  <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest">Source: Gemini 1.5 Flash</span>
                  <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest italic">{new Date(briefing?.timestamp || Date.now()).toLocaleTimeString()}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-12 gap-10">
                <div className="md:col-span-5 flex flex-col items-center justify-center p-8 bg-slate-950/50 rounded-[2.5rem] border border-white/5 relative group">
                  <div className="relative w-48 h-48 flex items-center justify-center mb-6">
                    <div className={`absolute inset-0 rounded-full blur-3xl opacity-20 animate-pulse ${recovery?.status === 'EMERALD' ? 'bg-emerald-500' : recovery?.status === 'AMBER' ? 'bg-amber-500' : 'bg-rose-500'}`}></div>
                    <svg className="absolute inset-0 w-full h-full -rotate-90">
                      <defs>
                        <linearGradient id="orbGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stopColor={recovery?.status === 'EMERALD' ? '#10b981' : recovery?.status === 'AMBER' ? '#f59e0b' : '#f43f5e'} />
                          <stop offset="100%" stopColor="#020617" />
                        </linearGradient>
                      </defs>
                      <circle cx="96" cy="96" r="84" stroke="rgba(255,255,255,0.05)" strokeWidth="12" fill="none" />
                      <circle cx="96" cy="96" r="84" stroke="url(#orbGradient)" strokeWidth="12" fill="none"
                        strokeDasharray="527.7" strokeDashoffset={527.7 - (527.7 * (recovery?.score || 85) / 100)}
                        strokeLinecap="round" className="transition-all duration-1000 ease-out" />
                    </svg>
                    <div className="relative z-10 flex flex-col items-center">
                      <span className="text-6xl font-black text-white italic tracking-tighter leading-none">{(recovery?.score || 85).toFixed(0)}</span>
                      <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest mt-1">Readiness</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4 w-full">
                    {[
                      { l: 'Strain', v: recovery?.breakdown?.strain_recovery || 80, c: 'orange' },
                      { l: 'Fuel', v: recovery?.breakdown?.nutritional_status || 90, c: 'cyan' },
                      { l: 'Stability', v: recovery?.breakdown?.system_stability || 85, c: 'purple' }
                    ].map(stat => {
                      const c2 = statColors[stat.c as keyof typeof statColors] || statColors.emerald;
                      return (
                        <div key={stat.l} className="text-center">
                          <p className={`text-xs font-black ${c2.text} mb-0.5`}>{stat.v}%</p>
                          <p className="text-[7px] font-black text-slate-600 uppercase tracking-widest">{stat.l}</p>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="md:col-span-7 flex flex-col justify-between py-2">
                  <div className="space-y-6">
                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center space-x-3 text-white/80">
                          <BrainCircuit size={18} className="text-emerald-400" />
                          <span className="text-[11px] font-black uppercase tracking-widest">Kinetic Integrity Check:</span>
                        </div>
                        <span className={`text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded ${integrity?.precision_index === 'HIGH' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'}`}>
                          {integrity?.precision_index || 'HIGH'} PRECISION
                        </span>
                      </div>
                      <div className="relative p-6 bg-slate-950/50 rounded-2xl border border-white/5 card-hover">
                        <div className="absolute top-4 right-4 text-emerald-500/10"><ShieldCheck size={40} /></div>
                        <div className="flex items-center space-x-4 mb-3">
                          <div className="flex flex-col">
                            <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest">Score Index</span>
                            <span className="text-xl font-black text-white italic">{(integrity?.integrity_score || 98).toFixed(0)}%</span>
                          </div>
                          <div className="w-px h-6 bg-white/10 mx-2"></div>
                          <div className="flex flex-col">
                            <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest">Focus Area</span>
                            <span className="text-[10px] font-black text-cyan-400 uppercase tracking-widest italic">{integrity?.focus_area || 'None'}</span>
                          </div>
                        </div>
                        <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 fill-bar-anim" style={{ width: `${integrity?.integrity_score || 98}%` }}></div>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-6 mt-6">
                      <div className="flex flex-col">
                        <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest mb-1">Kinetic Focus</span>
                        <span className="text-[10px] font-black text-cyan-400 uppercase tracking-widest italic">{integrity?.focus_area || 'None'}</span>
                      </div>
                      <div className="w-px h-8 bg-white/10"></div>
                      <div className="flex flex-col">
                        <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest mb-1">Injury Risk</span>
                        <span className="text-[10px] font-black text-rose-400 uppercase tracking-widest italic">{(100 - (integrity?.integrity_score || 100)).toFixed(0)}% Delta</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Reveal>
        </div>

        {/* Sidebar Column */}
        <div className="lg:col-span-4 space-y-8">
          {profile.gender === 'Female' && (profile.femmecareEnabled || profile.femmecare_enabled) && femmeData && (
            <Reveal animation="slide-in-right" delay={50}>
              <div className="glass-panel p-6 rounded-[2.5rem] border border-pink-500/20 bg-gradient-to-br from-pink-950/10 via-slate-950 to-pink-950/10 relative overflow-hidden group card-hover">
                <div className="absolute top-0 right-0 w-32 h-32 bg-pink-500/5 rounded-full blur-2xl -mr-10 -mt-10 group-hover:bg-pink-500/10 transition-all duration-500" />
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-2xl bg-pink-500/10 border border-pink-500/20 flex items-center justify-center text-pink-400">
                      <Heart size={20} className="fill-pink-500/20" />
                    </div>
                    <div>
                      <h4 className="text-xs font-black text-pink-400 tracking-wider uppercase">FemmeCare Sync</h4>
                      <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">Active calibration</p>
                    </div>
                  </div>
                  <span className="text-[9px] font-black text-pink-500/80 bg-pink-500/10 px-2 py-1 rounded-full border border-pink-500/20 capitalize">
                    {femmeData.phase} phase
                  </span>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <p className="text-[8px] font-black text-slate-500 uppercase tracking-wider">Recommended Workout</p>
                    <p className="text-xs font-black text-white italic mt-1">{femmeData.recommended_workout}</p>
                  </div>
                  <div>
                    <p className="text-[8px] font-black text-slate-500 uppercase tracking-wider">Hormonal Energy Status</p>
                    <p className="text-xs text-slate-300 mt-1 leading-relaxed">{femmeData.energy_tip}</p>
                  </div>
                  <div>
                    <p className="text-[8px] font-black text-slate-500 uppercase tracking-wider">Recommended Foods</p>
                    <div className="flex flex-wrap gap-1.5 mt-1.5">
                      {femmeData.recommended_foods?.map((food: string, idx: number) => (
                        <span key={idx} className="text-[9px] font-bold text-slate-400 bg-white/5 border border-white/5 px-2 py-1 rounded-lg">
                          {food}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                
                <div className="mt-5 pt-4 border-t border-white/5 flex justify-between items-center">
                  <span className="text-[9px] font-black text-slate-600 uppercase">Day {femmeData.cycle_day || '--'} of Cycle</span>
                  <button 
                    onClick={() => navigate('/dashboard/femmecare')}
                    className="text-[9px] font-black text-pink-400 uppercase tracking-wider flex items-center hover:text-pink-300 transition-colors"
                  >
                    Open Module <ArrowRight size={10} className="ml-1" />
                  </button>
                </div>
              </div>
            </Reveal>
          )}

          <Reveal animation="slide-in-right" delay={100}>
            <SmartNextMove userId={1} />
          </Reveal>
          <Reveal animation="slide-in-right" delay={200}>
            <DailyChecklist userId={1} compact />
          </Reveal>
          <Reveal animation="slide-in-right" delay={300}>
            <div className="glass-panel p-8 rounded-[3rem] border border-white/5 relative card-hover">
              <h3 className="text-lg font-black text-white italic tracking-tighter mb-6 flex items-center">
                <Dumbbell className="mr-3 text-emerald-400" size={20} /> Recent Workouts
              </h3>
              {workoutLogs.length === 0 ? (
                <div className="py-10 text-center">
                  <Dumbbell size={32} className="text-slate-800 mx-auto mb-3" />
                  <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest">No workouts logged yet.</p>
                  <p className="text-[9px] text-slate-700 mt-1">Complete a workout in the Workout Planner.</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-64 overflow-y-auto stagger-children">
                  {workoutLogs.slice(0, 6).map((w, i) => (
                    <div key={i} className="p-4 bg-slate-950/50 rounded-2xl border border-white/5 flex items-center justify-between card-hover">
                      <div>
                        <p className="text-xs font-black text-white italic">{w.name}</p>
                        <p className="text-[9px] text-slate-500">{w.exercisesCompleted}/{w.exercisesTotal} exercises - {w.duration}min</p>
                        <p className="text-[9px] text-slate-600">{new Date(w.timestamp).toLocaleDateString()}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-black text-orange-400">{w.caloriesBurned}</p>
                        <p className="text-[9px] font-black text-slate-600 uppercase">kcal</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <div className="pt-6 mt-4 border-t border-white/5">
                <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3">Weekly Calories Burned</p>
                <ResponsiveContainer width="100%" height={80}>
                  <AreaChart data={weekCalData}>
                    <Area type="monotone" dataKey="v" stroke="#f97316" fill="#f97316" fillOpacity={0.1} strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </Reveal>

          <Reveal animation="slide-in-right" delay={400}>
            <div className="glass-panel p-8 rounded-[3rem] border border-white/5 relative bg-slate-900/50">
              <h3 className="text-lg font-black text-white italic tracking-tighter mb-6 flex items-center">
                <BrainCircuit className="mr-3 text-cyan-400" size={20} /> Neural Insights
              </h3>
              {loadingRecs ? (
                <div className="space-y-4">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="h-20 skeleton-shimmer" />
                  ))}
                </div>
              ) : recommendations.length > 0 ? (
                <div className="space-y-4 stagger-children">
                  {recommendations.slice(0, 3).map((rec, i) => (
                    <div key={i} className="p-5 bg-slate-950/80 rounded-2xl border border-white/10 card-hover">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[8px] font-black uppercase px-2 py-0.5 rounded border border-cyan-500/30 text-cyan-400">{rec.type}</span>
                        <span className="text-[8px] font-black text-slate-600 uppercase">Confidence: {(rec.confidence_score * 100).toFixed(0)}%</span>
                      </div>
                      <p className="text-xs font-black text-white italic group-hover:text-cyan-300 transition-colors uppercase">{rec.title}</p>
                      <p className="text-[9px] text-slate-500 mt-1 leading-relaxed">{rec.description}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-6 text-center">
                  <p className="text-[9px] font-black text-slate-600 uppercase tracking-widest italic">Analyzing biological trends...</p>
                </div>
              )}
            </div>
          </Reveal>

          {/* GitHub-style Macro Adherence Streak Calendar */}
          <Reveal animation="slide-in-right" delay={450}>
            <div className="glass-panel p-6 rounded-[2.5rem] border border-white/5 bg-slate-950/40">
              <h3 className="text-xs font-black text-white uppercase tracking-widest mb-3 flex items-center">
                <CalendarDays className="mr-2 text-emerald-400" size={16} /> Macro Adherence Grid
              </h3>
              <div className="grid grid-cols-7 gap-1.5 p-2 bg-slate-950/60 rounded-xl border border-white/5">
                {Array.from({ length: 28 }).map((_, i) => {
                  const hasLog = i % 4 !== 0; // synthetic log streak pattern
                  const intensity = i % 5 === 0 ? 'bg-emerald-800' : i % 3 === 0 ? 'bg-emerald-600' : 'bg-emerald-500';
                  return (
                    <div 
                      key={i} 
                      className={`aspect-square rounded-md ${hasLog ? intensity : 'bg-slate-900 border border-white/5'} transition-all hover:scale-110`}
                      title={hasLog ? "Target Met" : "No entry logged"}
                    />
                  );
                })}
              </div>
              <p className="text-[8px] text-slate-500 uppercase tracking-widest text-center mt-3 font-bold">Past 4 weeks performance</p>
            </div>
          </Reveal>

          {/* Muscle Heatmap */}
          <Reveal animation="slide-in-right" delay={500}>
            <div className="glass-panel p-6 rounded-[2.5rem] border border-white/5 bg-slate-950/40">
              <h3 className="text-xs font-black text-white uppercase tracking-widest mb-4 flex items-center">
                <Activity className="mr-2 text-cyan-400" size={16} /> Target Volume Heatmap
              </h3>
              <div className="space-y-3">
                {[
                  { muscle: "Glutes/Legs", volume: 85, color: "bg-pink-500" },
                  { muscle: "Core/Back", volume: 60, color: "bg-cyan-500" },
                  { muscle: "Shoulders/Arms", volume: 40, color: "bg-orange-500" }
                ].map((item, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between text-[10px] font-black text-slate-400 uppercase">
                      <span>{item.muscle}</span>
                      <span>{item.volume}% intensity</span>
                    </div>
                    <div className="h-2 bg-slate-900 rounded-full overflow-hidden border border-white/5">
                      <div className={`h-full rounded-full ${item.color}`} style={{ width: `${item.volume}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Reveal>

        </div>
      </div>
    </div>
  );
};

export default Dashboard;
