
import React, { useState, useEffect } from 'react';
import {
  Activity,
  Flame,
  Clock,
  TrendingUp,
  Zap,
  Target,
  BrainCircuit,
  ShieldCheck,
  Cpu,
  CheckCircle2,
  Circle,
  Fingerprint,
  Dumbbell,
  Trophy
} from 'lucide-react';
import {
  AreaChart, Area, ResponsiveContainer
} from 'recharts';
import { fetchRecoveryScore, fetchNeuralIntegrity, fetchMissionBriefing } from './api';
import { generateDailyTasks } from './geminiService';
import { DailyTask } from './types';

interface WorkoutLog { name: string; duration: number; caloriesBurned: number; exercisesCompleted: number; exercisesTotal: number; timestamp: string; goal: string; }
interface MealLog { mealName: string; totalCalories: number; totalProtein: number; totalCarbs: number; totalFats: number; mealType: string; timestamp: string; }

const Dashboard: React.FC = () => {
  const [tasks, setTasks] = useState<DailyTask[]>([]);
  const [recovery, setRecovery] = useState<any>(null);
  const [integrity, setIntegrity] = useState<any>(null);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [briefing, setBriefing] = useState<any>(null);
  const [typedBriefing, setTypedBriefing] = useState('');
  const [briefingIndex, setBriefingIndex] = useState(0);

  // Real data from localStorage
  const workoutLogs: WorkoutLog[] = JSON.parse(localStorage.getItem('smarty_workout_logs') || '[]');
  const mealLogs: MealLog[] = JSON.parse(localStorage.getItem('smarty_meal_logs') || '[]');
  const today = new Date().toDateString();
  const todayWorkouts = workoutLogs.filter(w => new Date(w.timestamp).toDateString() === today);
  const todayMeals = mealLogs.filter(m => new Date(m.timestamp).toDateString() === today);
  const todayCalsBurned = todayWorkouts.reduce((s, w) => s + (w.caloriesBurned || 0), 0);
  const todayCalEaten = todayMeals.reduce((s, m) => s + (m.totalCalories || 0), 0);
  const todayProtein = todayMeals.reduce((s, m) => s + (m.totalProtein || 0), 0);
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

  useEffect(() => {
    fetchRecoveryScore().then(setRecovery);
    fetchNeuralIntegrity().then(setIntegrity);
    fetchMissionBriefing().then(setBriefing);

    // Fetch AI Recommendations
    setLoadingRecs(true);
    fetch('http://localhost:8000/api/users/user-1/recommendations')
      .then(res => res.json())
      .then(data => setRecommendations(data.recommendations || []))
      .catch(err => console.error('Failed to fetch recommendations:', err))
      .finally(() => setLoadingRecs(false));

    const savedProfile = localStorage.getItem('bio_profile');
    if (savedProfile) {
      setLoadingTasks(true);
      generateDailyTasks(JSON.parse(savedProfile))
        .then(setTasks)
        .finally(() => setLoadingTasks(false));
    }
  }, []);

  // Typewriter effect for briefing
  useEffect(() => {
    if (briefing?.directive && briefingIndex < briefing.directive.length) {
      const timeout = setTimeout(() => {
        setTypedBriefing(prev => prev + briefing.directive[briefingIndex]);
        setBriefingIndex(prev => prev + 1);
      }, 30);
      return () => clearTimeout(timeout);
    }
  }, [briefing, briefingIndex]);

  const toggleTask = (id: string) => {
    setTasks(prev => prev.map(t => t.id === id ? { ...t, completed: !t.completed } : t));
  };

  return (
    <div className="space-y-10 animate-in fade-in duration-700">
      {/* Bio-Sync Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center space-x-6">
          <div className="w-16 h-16 rounded-2xl border-2 border-emerald-500/30 bg-slate-900 flex items-center justify-center text-emerald-500">
            <Cpu size={32} />
          </div>
          <div>
            <h2 className="text-4xl font-black text-white italic tracking-tighter uppercase">Mission Status: Operational</h2>
            <div className="flex items-center space-x-3 mt-1">
              <span className="text-[10px] font-black uppercase tracking-widest text-emerald-400 px-2 py-1 bg-emerald-500/10 rounded flex items-center">
                <ShieldCheck size={12} className="mr-1" /> Core Synced
              </span>
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 italic">User-Node: 0xALEX</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: AI Daily Protocol */}
        <div className="lg:col-span-8 space-y-8">
          <div className="glass-panel p-10 rounded-[3rem] border border-white/5 relative overflow-hidden group">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-emerald-500/20 to-transparent"></div>

            <div className="flex items-center justify-between mb-8">
              <div>
                <h3 className="text-2xl font-black text-white italic tracking-tighter">NEURAL CHECKLIST</h3>
                <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em]">Computed for Current Biological State</p>
              </div>
              <div className="px-4 py-2 bg-slate-950 border border-white/10 rounded-xl text-[9px] font-black text-slate-500 uppercase tracking-widest">
                AI Refresh: 24h
              </div>
            </div>

            <div className="space-y-4">
              {loadingTasks ? (
                <div className="py-12 flex flex-col items-center justify-center space-y-4">
                  <BrainCircuit className="animate-spin text-emerald-500" size={40} />
                  <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Generating Strategy...</p>
                </div>
              ) : tasks.length > 0 ? (
                tasks.map((task) => (
                  <div
                    key={task.id}
                    onClick={() => toggleTask(task.id)}
                    className={`flex items-center justify-between p-6 rounded-2xl border transition-all cursor-pointer group ${task.completed ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-slate-950 border-white/5 hover:border-white/10'
                      }`}
                  >
                    <div className="flex items-center space-x-6">
                      {task.completed ? <CheckCircle2 className="text-emerald-500" /> : <Circle className="text-slate-800" />}
                      <div>
                        <p className={`text-sm font-black italic uppercase tracking-tight ${task.completed ? 'text-emerald-400/50 line-through' : 'text-white'}`}>
                          {task.label}
                        </p>
                        <p className="text-[9px] font-black text-slate-600 uppercase tracking-widest mt-1">Scheduled: {task.time}</p>
                      </div>
                    </div>
                    <span className={`text-[8px] font-black uppercase px-2 py-1 rounded border ${task.priority === 'High' ? 'border-rose-500/30 text-rose-500' : 'border-slate-800 text-slate-600'
                      }`}>
                      {task.priority} Priority
                    </span>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-slate-600 uppercase text-[10px] font-black tracking-widest">
                  Initialize Bio-Link to generate daily protocol.
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Kcal Burned Today', value: todayCalsBurned, unit: 'kcal', color: 'orange', icon: Flame, sub: `${todayWorkouts.length} workout${todayWorkouts.length !== 1 ? 's' : ''}` },
              { label: 'Kcal Eaten Today', value: todayCalEaten, unit: 'kcal', color: 'amber', icon: Activity, sub: `${todayMeals.length} meals logged` },
              { label: 'Protein Today', value: `${todayProtein.toFixed(0)}g`, unit: '', color: 'blue', icon: Zap, sub: 'consumed' },
              { label: 'Workout Streak', value: workoutStreak, unit: 'days', color: 'emerald', icon: Trophy, sub: workoutStreak > 0 ? 'Keep it up!' : 'Start today!' },
            ].map(s => (
              <div key={s.label} className={`p-6 bg-${s.color}-500/10 border border-${s.color}-500/20 rounded-3xl`}>
                <s.icon size={18} className={`text-${s.color}-400 mb-3`} />
                <p className={`text-2xl font-black text-${s.color}-400 italic`}>{s.value}{s.unit && <span className="text-sm ml-1">{s.unit}</span>}</p>
                <p className="text-[9px] font-black uppercase tracking-widest text-slate-500 mt-1">{s.label}</p>
                <p className="text-[9px] text-slate-600 mt-0.5">{s.sub}</p>
              </div>
            ))}
          </div>

          {/* NEW: Neural Integrity Engine Widget */}
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
                <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em]">Neural Bio-Analytical Core v5.0</p>
              </div>
            </div>

            {/* Mission Briefing Terminal */}
            <div className="mb-10 p-6 bg-slate-950 border border-emerald-500/20 rounded-2xl relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-[2px] bg-emerald-500/30 animate-pulse"></div>
              <div className="flex items-center space-x-2 mb-3">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
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
                {/* Readiness Orb Visualization */}
                <div className="relative w-48 h-48 flex items-center justify-center mb-6">
                  {/* Outer Glow Orb */}
                  <div className={`absolute inset-0 rounded-full blur-3xl opacity-20 animate-pulse bg-${recovery?.status === 'EMERALD' ? 'emerald' : recovery?.status === 'AMBER' ? 'amber' : 'rose'}-500`}></div>

                  {/* SVG Progress Orb */}
                  <svg className="absolute inset-0 w-full h-full -rotate-90">
                    <defs>
                      <linearGradient id="orbGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor={recovery?.status === 'EMERALD' ? '#10b981' : recovery?.status === 'AMBER' ? '#f59e0b' : '#f43f5e'} />
                        <stop offset="100%" stopColor="#020617" />
                      </linearGradient>
                    </defs>
                    <circle cx="96" cy="96" r="84" stroke="rgba(255,255,255,0.05)" strokeWidth="12" fill="none" />
                    <circle cx="96" cy="96" r="84" stroke="url(#orbGradient)" strokeWidth="12" fill="none"
                      strokeDasharray="527.7"
                      strokeDashoffset={527.7 - (527.7 * (recovery?.score || 85) / 100)}
                      strokeLinecap="round"
                      className="transition-all duration-1000 ease-out"
                    />
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
                  ].map(stat => (
                    <div key={stat.l} className="text-center">
                      <p className={`text-xs font-black text-${stat.c}-400 mb-0.5`}>{stat.v}%</p>
                      <p className="text-[7px] font-black text-slate-600 uppercase tracking-widest">{stat.l}</p>
                    </div>
                  ))}
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
                      <span className={`text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded ${integrity?.precision_index === 'HIGH' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                        {integrity?.precision_index || 'HIGH'} PRECISION
                      </span>
                    </div>
                    <div className="relative p-6 bg-slate-950/50 rounded-2xl border border-white/5 group hover:border-emerald-500/30 transition-all">
                      <div className="absolute top-4 right-4 text-emerald-500/10">
                        <ShieldCheck size={40} />
                      </div>
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
                        <div className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all duration-1000" style={{ width: `${integrity?.integrity_score || 98}%` }}></div>
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

          {/* Right Column: Real Activity */}
          <div className="lg:col-span-4 space-y-8">
            <div className="glass-panel p-8 rounded-[3rem] border border-white/5 relative h-full">
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
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {workoutLogs.slice(0, 6).map((w, i) => (
                    <div key={i} className="p-4 bg-slate-950/50 rounded-2xl border border-white/5 flex items-center justify-between">
                      <div>
                        <p className="text-xs font-black text-white italic">{w.name}</p>
                        <p className="text-[9px] text-slate-500">{w.exercisesCompleted}/{w.exercisesTotal} exercises • {w.duration}min</p>
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
                {todayCalsBurned > 0 && (
                  <p className="text-[9px] font-black text-orange-400 mt-2 text-right">Today: {todayCalsBurned} kcal burned</p>
                )}
              </div>
            </div>

            {/* NEW: Neural Insights Panel */}
            <div className="glass-panel p-8 rounded-[3rem] border border-white/5 relative bg-slate-900/50">
              <h3 className="text-lg font-black text-white italic tracking-tighter mb-6 flex items-center">
                <BrainCircuit className="mr-3 text-cyan-400" size={20} /> Neural Insights
              </h3>

              {loadingRecs ? (
                <div className="space-y-4">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="h-20 bg-slate-950/50 rounded-2xl animate-pulse border border-white/5" />
                  ))}
                </div>
              ) : recommendations.length > 0 ? (
                <div className="space-y-4">
                  {recommendations.slice(0, 3).map((rec, i) => (
                    <div key={i} className="p-5 bg-slate-950/80 rounded-2xl border border-white/10 group hover:border-cyan-500/30 transition-all">
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
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
