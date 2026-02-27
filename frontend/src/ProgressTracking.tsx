import React, { useState, useEffect } from 'react';
import { TrendingUp, Flame, Dumbbell, Scale, Target, Plus, Check, Trash2, Award, Calendar } from 'lucide-react';

interface WeightEntry { date: string; weight: number; }
interface MealLog { mealName: string; totalCalories: number; totalProtein: number; totalCarbs: number; totalFats: number; mealType: string; timestamp: string; }
interface WorkoutLog { name: string; duration: number; completed: boolean; timestamp: string; }

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

  // Workout streak
  const workoutStreak = (() => {
    let streak = 0;
    let d = new Date();
    while (streak < 30) {
      const ds = d.toDateString();
      if (workoutLogs.some(w => new Date(w.timestamp).toDateString() === ds && w.completed)) streak++;
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

  const weightChange = weightLog.length > 1 ? weightLog[weightLog.length - 1].weight - weightLog[0].weight : 0;
  const progressToTarget = targetWeight && startWeight !== targetWeight
    ? Math.min(100, Math.max(0, Math.round(Math.abs(startWeight - currentWeight) / Math.abs(startWeight - targetWeight) * 100)))
    : null;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-4xl font-black italic tracking-tighter text-white">
          Progress <span className="text-emerald-400">Tracker</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          {profile.goal ? `Goal: ${goalLabel[profile.goal] || profile.goal}` : 'Track your fitness journey'}
          {profile.name ? ` • ${profile.name}` : ''}
        </p>
      </div>

      {/* Today Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          {
            label: "Today's Calories", value: `${todayCalories}`, sub: `/ ${dailyCalGoal} kcal`, color: 'orange', icon: Flame,
            warn: todayCalories > dailyCalGoal
          },
          { label: "Today's Protein", value: `${todayProtein.toFixed(0)}g`, sub: 'consumed', color: 'blue', icon: Dumbbell },
          { label: 'Workout Streak', value: `${workoutStreak}`, sub: 'days', color: 'emerald', icon: Award },
          { label: 'Current Weight', value: `${currentWeight}kg`, sub: weightChange !== 0 ? `${weightChange > 0 ? '+' : ''}${weightChange.toFixed(1)}kg total` : 'no change', color: 'purple', icon: Scale },
        ].map(s => (
          <div key={s.label} className={`p-5 bg-${s.color}-500/10 border border-${s.color}-500/20 rounded-2xl ${s.warn ? 'border-rose-500/40' : ''}`}>
            <s.icon size={18} className={`text-${s.color}-400 mb-3`} />
            <p className={`text-2xl font-black ${s.warn ? 'text-rose-400' : `text-${s.color}-400`}`}>{s.value}</p>
            <p className="text-[9px] font-black uppercase tracking-widest text-slate-500 mt-1">{s.label}</p>
            <p className="text-[9px] text-slate-600 mt-0.5">{s.sub}</p>
          </div>
        ))}
      </div>

      {/* Goal Progress Bar */}
      {progressToTarget !== null && (
        <div className="p-6 bg-slate-900 border border-white/10 rounded-2xl">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <Target size={18} className="text-emerald-400" />
              <div>
                <p className="text-sm font-black text-white">Goal Progress</p>
                <p className="text-[10px] text-slate-500">{startWeight}kg → {targetWeight}kg target</p>
              </div>
            </div>
            <span className="text-2xl font-black text-emerald-400">{progressToTarget}%</span>
          </div>
          <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-emerald-500 to-cyan-400 rounded-full transition-all duration-700 shadow-[0_0_10px_rgba(16,185,129,0.4)]"
              style={{ width: `${progressToTarget}%` }} />
          </div>
          <p className="text-[10px] text-slate-500 mt-2 text-right">{Math.abs(currentWeight - (targetWeight || 0)).toFixed(1)}kg remaining</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Calorie Chart */}
        <div className="p-6 bg-slate-900 border border-white/10 rounded-2xl">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <Flame size={18} className="text-orange-400" />
              <p className="text-sm font-black text-white uppercase tracking-widest">Weekly Calories</p>
            </div>
            <span className="text-[9px] font-black uppercase tracking-widest text-slate-500">Last 7 days</span>
          </div>
          <div className="flex items-end space-x-2 h-36">
            {weekData.map((d, i) => {
              const height = d.calories > 0 ? Math.max(8, (d.calories / maxCal) * 100) : 4;
              const isToday = i === 6;
              const isOver = d.calories > dailyCalGoal;
              return (
                <div key={i} className="flex-1 flex flex-col items-center space-y-2">
                  <div className="w-full relative flex items-end" style={{ height: '120px' }}>
                    <div
                      className={`w-full rounded-t-lg transition-all ${isToday ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.4)]' : isOver ? 'bg-rose-500/60' : 'bg-slate-700'}`}
                      style={{ height: `${height}%` }} />
                    {/* Goal line */}
                    <div className="absolute w-full border-t border-dashed border-emerald-500/30" style={{ bottom: `${(dailyCalGoal / maxCal) * 100}%` }} />
                  </div>
                  <p className="text-[8px] font-black uppercase tracking-wider text-slate-600">{d.label}</p>
                  {d.calories > 0 && <p className="text-[7px] text-slate-600">{d.calories}</p>}
                </div>
              );
            })}
          </div>
          <p className="text-[9px] text-slate-600 mt-3 text-right">— Daily goal: {dailyCalGoal} kcal</p>
        </div>

        {/* Weight Log */}
        <div className="p-6 bg-slate-900 border border-white/10 rounded-2xl">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <Scale size={18} className="text-purple-400" />
              <p className="text-sm font-black text-white uppercase tracking-widest">Weight Log</p>
            </div>
            <button onClick={() => setAddingWeight(!addingWeight)}
              className="flex items-center space-x-1.5 px-3 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400 text-[9px] font-black uppercase tracking-widest hover:bg-emerald-500/20 transition">
              <Plus size={12} />
              <span>Log Weight</span>
            </button>
          </div>

          {addingWeight && (
            <div className="flex space-x-2 mb-4">
              <input type="number" value={newWeight} onChange={e => setNewWeight(e.target.value)} placeholder="e.g. 72.5"
                className="flex-1 bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-emerald-500/50 placeholder:text-slate-600" />
              <span className="flex items-center text-slate-500 text-sm font-black">kg</span>
              <button onClick={addWeight} className="p-2.5 bg-emerald-500 text-slate-950 rounded-xl hover:bg-emerald-400 transition">
                <Check size={16} />
              </button>
            </div>
          )}

          <div className="space-y-2 max-h-52 overflow-y-auto">
            {weightLog.length === 0 ? (
              <p className="text-slate-600 text-sm text-center py-8">No weight entries yet. Log your first one!</p>
            ) : [...weightLog].reverse().map((e, i) => {
              const prev = weightLog.length > 1 - i ? weightLog[weightLog.length - 1 - i - 1] : null;
              const diff = prev ? e.weight - prev.weight : null;
              return (
                <div key={i} className="flex items-center justify-between p-3 bg-slate-800 rounded-xl">
                  <div className="flex items-center space-x-3">
                    <Calendar size={14} className="text-slate-500" />
                    <p className="text-xs text-slate-400">{e.date}</p>
                  </div>
                  <div className="flex items-center space-x-3">
                    {diff !== null && diff !== 0 && (
                      <span className={`text-[9px] font-black ${diff < 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {diff > 0 ? '+' : ''}{diff.toFixed(1)}kg
                      </span>
                    )}
                    <span className="text-sm font-black text-white">{e.weight}kg</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Recent Meal Logs */}
      {mealLogs.length > 0 && (
        <div className="bg-slate-900 border border-white/10 rounded-2xl p-6">
          <div className="flex items-center space-x-3 mb-4">
            <Flame size={18} className="text-orange-400" />
            <p className="text-sm font-black text-white uppercase tracking-widest">Recent Meals</p>
          </div>
          <div className="space-y-2">
            {mealLogs.slice(0, 8).map((m, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-slate-800 rounded-xl">
                <div>
                  <p className="text-sm font-black text-white">{m.mealName}</p>
                  <p className="text-[9px] text-slate-500 capitalize">{m.mealType} • {new Date(m.timestamp).toLocaleDateString()}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-black text-amber-400">{m.totalCalories} kcal</p>
                  <p className="text-[9px] text-slate-500">P{m.totalProtein}g C{m.totalCarbs}g F{m.totalFats}g</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProgressTracking;
