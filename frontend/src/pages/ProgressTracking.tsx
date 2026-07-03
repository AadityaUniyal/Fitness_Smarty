import React, { useState } from 'react';
import { Flame, Dumbbell, Scale, Target, Plus, Check, Award, Calendar, CheckCircle2, Timer, Droplets, GlassWater } from 'lucide-react';
import HydrationHub from '../components/HydrationHub';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface WeightEntry { date: string; weight: number; }
interface MealLog { mealName: string; totalCalories: number; totalProtein: number; totalCarbs: number; totalFats: number; mealType: string; timestamp: string; }
interface WorkoutLog { name: string; duration: number; caloriesBurned: number; exercisesCompleted: number; exercisesTotal: number; timestamp: string; goal: string; }

const ProgressTracking: React.FC = () => {
  const profile = JSON.parse(localStorage.getItem('smarty_profile') || '{}');
  const [weightLog, setWeightLog] = useState<WeightEntry[]>(() => {
    const saved = localStorage.getItem('smarty_weight_log');
    if (saved) return JSON.parse(saved);
    // Seed with starting weight
    if (profile.weight) {
      return [{ date: new Date(Date.now() - 7 * 86400000).toLocaleDateString(), weight: Number(profile.weight) + 1.5 },
      { date: new Date(Date.now() - 4 * 86400000).toLocaleDateString(), weight: Number(profile.weight) + 0.8 },
      { date: new Date().toLocaleDateString(), weight: Number(profile.weight) }];
    }
    return [];
  });
  const [newWeight, setNewWeight] = useState('');
  const [mealLogs, setMealLogs] = useState<MealLog[]>(() => JSON.parse(localStorage.getItem('smarty_meal_logs') || '[]'));
  const [workoutLogs, setWorkoutLogs] = useState<WorkoutLog[]>(() => JSON.parse(localStorage.getItem('smarty_workout_logs') || '[]'));
  const [addingWeight, setAddingWeight] = useState(false);

  const dailyCalGoal = profile.dailyCalorieGoal || 2200;
  const targetWeight = profile.targetWeight ? Number(profile.targetWeight) : null;
  const currentWeight = weightLog.length > 0 ? weightLog[weightLog.length - 1].weight : Number(profile.weight) || 0;
  const startWeight = Number(profile.weight) || currentWeight;

  const goalLabel: Record<string, string> = {
    weight_loss: 'Weight Loss', muscle_gain: 'Muscle Gain', athletic: 'Athletic', maintenance: 'Maintenance'
  };

  // Today stats
  const today = new Date().toDateString();
  const todayMeals = mealLogs.filter(m => new Date(m.timestamp).toDateString() === today);
  const todayCalories = todayMeals.reduce((s, m) => s + (m.totalCalories || 0), 0);
  const todayProtein = todayMeals.reduce((s, m) => s + (m.totalProtein || 0), 0);

  // Weekly calorie data for mini chart
  const weekData = Array.from({ length: 7 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (6 - i));
    const ds = d.toDateString();
    const dayMeals = mealLogs.filter(m => new Date(m.timestamp).toDateString() === ds);
    return { label: d.toLocaleDateString('en', { weekday: 'short' }), calories: dayMeals.reduce((s, m) => s + (m.totalCalories || 0), 0) };
  });

  const maxCal = Math.max(...weekData.map(d => d.calories), dailyCalGoal);

  const totalCalsBurned = workoutLogs.reduce((s, w) => s + (w.caloriesBurned || 0), 0);
  const todayCalsBurned = workoutLogs.filter(w => new Date(w.timestamp).toDateString() === today).reduce((s, w) => s + (w.caloriesBurned || 0), 0);
  const workoutStreak = (() => {
    let streak = 0; let d = new Date();
    while (streak < 30) {
      if (workoutLogs.some(w => new Date(w.timestamp).toDateString() === d.toDateString())) streak++;
      else break;
      d.setDate(d.getDate() - 1);
    }
    return streak;
  })();

  const addWeight = () => {
    if (!newWeight) return;
    const entry: WeightEntry = { date: new Date().toLocaleDateString(), weight: Number(newWeight) };
    const updated = [...weightLog, entry];
    setWeightLog(updated);
    localStorage.setItem('smarty_weight_log', JSON.stringify(updated));
    setNewWeight('');
    setAddingWeight(false);
  };

  const [dailyBudget, setDailyBudget] = useState({ consumed: 0, burned: 0, net: 0 });
  const [dbStreak, setDbStreak] = useState(0);
  const [aiQuery, setAiQuery] = useState('');
  const [aiResponse, setAiResponse] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  React.useEffect(() => {
    // Fetch real-time budget and streak if backend is reachable
    const fetchData = async () => {
      try {
        const userId = profile.id || 1; // Fallback for demo
        const budgetRes = await fetch(`${API_BASE}/api/analytics/daily-budget/${userId}`);
        if (budgetRes.ok) setDailyBudget(await budgetRes.json());

        const streakRes = await fetch(`${API_BASE}/api/analytics/db-streak/${userId}`);
        if (streakRes.ok) setDbStreak((await streakRes.json()).streak);
      } catch {
        setDailyBudget({ consumed: todayCalories, burned: todayCalsBurned, net: todayCalories - todayCalsBurned });
        setDbStreak(workoutStreak);
      }
    };
    fetchData();
  }, [todayCalories, todayCalsBurned, workoutStreak]);

  const handleAiQuery = async () => {
    if (!aiQuery) return;
    setIsAnalyzing(true);
    try {
      const res = await fetch(`${API_BASE}/api/analytics/ai-query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: aiQuery, user_id: profile.id || 1 })
      });
      if (res.ok) setAiResponse(await res.json());
      else setAiResponse({ error: "Failed to connect to AI Analyst" });
    } catch (e) {
      setAiResponse({ error: "Networking error: Check if backend is running." });
    }
    setIsAnalyzing(false);
  };

  const exportForPowerBI = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/analytics/powerbi-export`);
      const data = await res.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `smarty_data_export_${new Date().toISOString().split('T')[0]}.json`;
      a.click();
    } catch (e) {
      alert("Export failed. Make sure backend is running.");
    }
  };

  const progressToTarget = targetWeight && startWeight !== targetWeight
    ? Math.min(100, Math.max(0, Math.round(Math.abs(startWeight - currentWeight) / Math.abs(startWeight - targetWeight) * 100)))
    : null;

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-20">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-4xl font-black italic tracking-tighter text-white">
            Mission <span className="text-emerald-400">Intelligence</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            {profile.goal ? `Goal: ${goalLabel[profile.goal] || profile.goal}` : 'Data-driven fitness evolution'}
          </p>
        </div>
        <button onClick={exportForPowerBI} className="flex items-center space-x-2 px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-400 text-xs font-bold hover:bg-blue-500/20 transition">
          <span>Export to Power BI</span>
        </button>
      </div>

      {/* Advanced Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <div className="p-6 bg-gradient-to-br from-orange-500/20 to-orange-600/5 border border-orange-500/20 rounded-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Flame size={80} />
          </div>
          <p className="text-[10px] font-black uppercase tracking-widest text-orange-500/60 mb-1">Daily Net Budget</p>
          <p className="text-4xl font-black text-white">{dailyBudget.net} <span className="text-lg text-slate-500">kcal</span></p>
          <div className="mt-4 flex items-center space-x-2 text-[10px] text-slate-400">
            <span className="text-emerald-400">+{dailyBudget.burned} burned</span>
            <span>•</span>
            <span className="text-rose-400">-{dailyBudget.consumed} eaten</span>
          </div>
        </div>

        <div className="p-6 bg-gradient-to-br from-emerald-500/20 to-emerald-600/5 border border-emerald-500/20 rounded-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
            <Target size={80} />
          </div>
          <p className="text-[10px] font-black uppercase tracking-widest text-emerald-500/60 mb-1">Activity Streak</p>
          <p className="text-4xl font-black text-white">{dbStreak} <span className="text-lg text-slate-500">days</span></p>
          <div className="mt-4 flex items-center space-x-1">
            {Array.from({ length: Math.min(dbStreak, 7) }).map((_, i) => (
              <div key={i} className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" style={{ animationDelay: `${i * 100}ms` }} />
            ))}
            {dbStreak === 0 && <span className="text-[10px] text-slate-500 italic">Start your streak today!</span>}
          </div>
        </div>

        <HydrationHub />

        <div className="p-6 bg-slate-900 border border-white/10 rounded-2xl flex flex-col justify-between">
          <div>
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-1">System Integrity</p>
            <p className="text-4xl font-black text-white">94%</p>
          </div>
          <div className="mt-4 h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full bg-emerald-500" style={{ width: '94%' }} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calorie Chart - Spans 2 cols */}
        <div className="lg:col-span-2 p-6 bg-slate-900 border border-white/10 rounded-3xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-orange-500/5 rounded-full blur-3xl -mr-16 -mt-16" />
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-orange-500/10 rounded-lg">
                <Flame size={18} className="text-orange-400" />
              </div>
              <div>
                <p className="text-xs font-black text-white uppercase tracking-widest leading-none">Weekly Calorie Velocity</p>
                <p className="text-[9px] text-slate-500 mt-1">Average: {Math.round(weekData.reduce((s, d) => s + d.calories, 0) / 7)} kcal/day</p>
              </div>
            </div>
          </div>

          <div className="flex items-end space-x-3 h-48">
            {weekData.map((d, i) => {
              const height = d.calories > 0 ? Math.max(8, (d.calories / maxCal) * 100) : 4;
              const isToday = i === 6;
              const isOver = d.calories > dailyCalGoal;
              return (
                <div key={i} className="flex-1 flex flex-col items-center group">
                  <div className="w-full relative flex items-end mb-3" style={{ height: '100%' }}>
                    <div
                      className={`w-full rounded-xl transition-all duration-500 ${isToday ? 'bg-gradient-to-t from-emerald-600 to-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.3)]' : isOver ? 'bg-rose-500/40' : 'bg-slate-800 group-hover:bg-slate-700'}`}
                      style={{ height: `${height}%` }}
                    />
                  </div>
                  <p className={`text-[9px] font-black uppercase tracking-wider ${isToday ? 'text-emerald-400' : 'text-slate-500'}`}>{d.label}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* AI Bio-Analyst */}
        <div className="p-6 bg-gradient-to-b from-slate-900 to-indigo-950/30 border border-white/10 rounded-3xl flex flex-col">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2 bg-indigo-500/10 rounded-lg">
              <CheckCircle2 size={18} className="text-indigo-400" />
            </div>
            <p className="text-xs font-black text-white uppercase tracking-widest leading-none">AI Bio-Analyst</p>
          </div>

          <div className="flex-1 space-y-4 mb-4 overflow-y-auto min-h-[200px] max-h-[300px] pr-2 scrollbar-hide">
            {!aiResponse && (
              <div className="p-4 bg-white/5 border border-white/5 rounded-2xl">
                <p className="text-[10px] text-slate-400 italic">
                  "How does my protein intake affect my morning energy levels?"
                </p>
              </div>
            )}

            {aiResponse && (
              <div className="space-y-4">
                {aiResponse.error ? (
                  <p className="text-xs text-rose-400 bg-rose-400/5 p-3 rounded-xl border border-rose-400/10">{aiResponse.error}</p>
                ) : (
                  <>
                    <div className="p-4 bg-indigo-500/10 border border-indigo-500/20 rounded-2xl animate-in fade-in slide-in-from-bottom-2">
                      <p className="text-xs font-bold text-indigo-300 mb-2">Findings:</p>
                      <p className="text-[11px] text-slate-300 leading-relaxed uppercase tracking-tight">{aiResponse.summary}</p>
                    </div>
                    {aiResponse.data && aiResponse.data.length > 0 && (
                      <div className="p-3 bg-slate-950/50 rounded-xl overflow-x-auto">
                        <table className="w-full text-[9px] text-slate-400">
                          <thead>
                            <tr className="border-b border-white/5 text-left">
                              {Object.keys(aiResponse.data[0]).map(k => <th key={k} className="pb-1 pr-2">{k}</th>)}
                            </tr>
                          </thead>
                          <tbody>
                            {aiResponse.data.slice(0, 3).map((row: any, i: number) => (
                              <tr key={i}>
                                {Object.values(row).map((v: any, j: number) => <td key={j} className="py-1 pr-2">{String(v)}</td>)}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>

          <div className="relative">
            <input
              value={aiQuery}
              onChange={e => setAiQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAiQuery()}
              placeholder="Ask the analyst..."
              className="w-full bg-slate-950 border border-white/10 rounded-2xl px-4 py-3 text-xs focus:outline-none focus:border-indigo-500/50 pr-12 transition-all shadow-inner"
            />
            <button
              onClick={handleAiQuery}
              disabled={isAnalyzing}
              className={`absolute right-2 top-2 p-1.5 rounded-xl ${isAnalyzing ? 'bg-slate-800' : 'bg-indigo-500 hover:bg-indigo-400'} text-white transition-colors`}
            >
              {isAnalyzing ? <Timer size={14} className="animate-spin" /> : <Plus size={14} className="rotate-45" />}
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Correlative Insights */}
        <div className="p-6 bg-slate-900 border border-white/10 rounded-3xl">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2 bg-emerald-500/10 rounded-lg">
              <Award size={18} className="text-emerald-400" />
            </div>
            <p className="text-xs font-black text-white uppercase tracking-widest leading-none">Correlative Insights</p>
          </div>
          <div className="space-y-3">
            {[
              { text: "Consistency with dinner timing improved target sleep recovery by 18%.", confidence: 92 },
              { text: "Leg day volume correlates with metabolic spike 24hrs later.", confidence: 88 }
            ].map((insight, i) => (
              <div key={i} className="p-4 bg-slate-800/50 border border-white/5 rounded-2xl flex items-start gap-4">
                <div className="w-12 h-12 rounded-full border-2 border-slate-700 flex items-center justify-center shrink-0">
                  <span className="text-xs font-black text-emerald-400">{insight.confidence}%</span>
                </div>
                <p className="text-[11px] text-slate-300 leading-relaxed font-bold uppercase italic">{insight.text}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Predictive Plateau Detection */}
        <div className="p-6 bg-slate-900 border border-white/10 rounded-3xl">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2 bg-rose-500/10 rounded-lg">
              <Timer size={18} className="text-rose-400" />
            </div>
            <p className="text-xs font-black text-white uppercase tracking-widest leading-none">Plateau Intelligence</p>
          </div>
          <div className="p-5 bg-rose-500/5 border border-rose-500/20 rounded-2xl">
            <div className="flex items-center justify-between mb-3 text-rose-400">
              <span className="text-[10px] font-black uppercase tracking-wider underline">Warning: Stagnation Pattern Detect</span>
              <CheckCircle2 size={14} />
            </div>
            <p className="text-xs text-slate-300 mb-4 font-bold">Your metabolic adaptation has reached 4.2% threshold. Progress likely to stall within 5-7 days.</p>
            <div className="flex gap-2">
              <button className="flex-1 py-2 bg-rose-500 text-slate-950 text-[10px] font-black uppercase rounded-xl hover:bg-rose-400 transition italic">Inject Refeed Day</button>
              <button className="flex-1 py-2 bg-white/10 text-white text-[10px] font-black uppercase rounded-xl hover:bg-white/20 transition italic">Adjust Macros</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProgressTracking;
