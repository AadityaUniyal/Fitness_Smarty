import React, { useState, useEffect } from 'react';
import { Calendar, Flame, Dumbbell, Utensils, TrendingUp, Trophy, Target, Activity } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid, AreaChart, Area } from 'recharts';
import { Reveal } from '../components/Reveal';

interface WorkoutLog {
  name: string; duration: number; caloriesBurned: number; exercisesCompleted: number;
  exercisesTotal: number; timestamp: string; goal: string;
}
interface MealLog {
  mealName?: string; totalCalories: number; totalProtein: number; totalCarbs: number;
  totalFats: number; mealType: string; timestamp: string;
}

const WeeklyReview: React.FC = () => {
  const [days, setDays] = useState(7);

  const getLastNDays = (n: number): Date[] => {
    return Array.from({ length: n }, (_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - (n - 1 - i));
      return d;
    });
  };

  const lastNDays = getLastNDays(days);
  const dateStrs = lastNDays.map(d => d.toDateString());
  const shortDates = lastNDays.map(d =>
    d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
  );

  const workoutLogs: WorkoutLog[] = JSON.parse(localStorage.getItem('smarty_workout_logs') || '[]');
  const mealLogs: MealLog[] = JSON.parse(localStorage.getItem('smarty_meal_logs') || '[]');

  const dailyData = dateStrs.map((ds, i) => {
    const dayWorkouts = workoutLogs.filter(w => new Date(w.timestamp).toDateString() === ds);
    const dayMeals = mealLogs.filter(m => new Date(m.timestamp).toDateString() === ds);
    return {
      date: shortDates[i],
      caloriesBurned: dayWorkouts.reduce((s, w) => s + (w.caloriesBurned || 0), 0),
      caloriesEaten: dayMeals.reduce((s, m) => s + (m.totalCalories || 0), 0),
      protein: dayMeals.reduce((s, m) => s + (m.totalProtein || 0), 0),
      workouts: dayWorkouts.length,
      meals: dayMeals.length,
      duration: dayWorkouts.reduce((s, w) => s + (w.duration || 0), 0),
    };
  });

  const totals = dailyData.reduce((s, d) => ({
    workouts: s.workouts + d.workouts,
    meals: s.meals + d.meals,
    caloriesBurned: s.caloriesBurned + d.caloriesBurned,
    caloriesEaten: s.caloriesEaten + d.caloriesEaten,
    protein: s.protein + d.protein,
    duration: s.duration + d.duration,
  }), { workouts: 0, meals: 0, caloriesBurned: 0, caloriesEaten: 0, protein: 0, duration: 0 });

  const dailyAvg = days > 0 ? {
    caloriesBurned: Math.round(totals.caloriesBurned / days),
    caloriesEaten: Math.round(totals.caloriesEaten / days),
    protein: Math.round(totals.protein / days),
  } : null;

  const netCalories = totals.caloriesEaten - totals.caloriesBurned;

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/20 rounded-3xl flex items-center justify-center text-emerald-400">
            <Calendar size={32} />
          </div>
          <div>
            <h2 className="text-4xl font-black italic tracking-tighter text-white uppercase">Weekly Review</h2>
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Your past week summarized</p>
          </div>
        </div>
        <div className="flex bg-slate-900 border border-white/10 rounded-2xl p-1">
          {[7, 14, 30].map(n => (
            <button key={n} onClick={() => setDays(n)}
              className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${days === n ? 'bg-emerald-500 text-slate-950' : 'text-slate-500 hover:text-emerald-400'}`}>
              {n}d
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Workouts', value: totals.workouts, unit: 'sessions', color: 'text-emerald-400', bg: 'bg-emerald-500/10', icon: Dumbbell },
          { label: 'Calories Burned', value: totals.caloriesBurned, unit: 'kcal', color: 'text-orange-400', bg: 'bg-orange-500/10', icon: Flame },
          { label: 'Calories Eaten', value: totals.caloriesEaten, unit: 'kcal', color: 'text-amber-400', bg: 'bg-amber-500/10', icon: Utensils },
          { label: 'Net Calories', value: netCalories, unit: 'kcal', color: netCalories > 0 ? 'text-rose-400' : 'text-emerald-400', bg: netCalories > 0 ? 'bg-rose-500/10' : 'bg-emerald-500/10', icon: Activity },
        ].map((stat, i) => (
          <Reveal key={stat.label} animation="fade-in-up" delay={i * 80}>
            <div className={`${stat.bg} border border-white/5 p-6 rounded-3xl card-hover`}>
              <stat.icon size={18} className={`${stat.color} mb-3`} />
              <p className={`text-2xl font-black italic ${stat.color}`}>{stat.value.toLocaleString()}</p>
              <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mt-1">{stat.label}</p>
              <p className="text-[8px] text-slate-600">{stat.unit}</p>
            </div>
          </Reveal>
        ))}
      </div>

      <Reveal animation="fade-in-up" delay={200}>
        <div className="glass-panel p-8 rounded-[2.5rem] border border-white/5">
          <h3 className="text-lg font-black text-white italic tracking-tighter mb-6 uppercase flex items-center">
            <TrendingUp className="mr-3 text-cyan-400" size={20} /> Daily Calories
          </h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={dailyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 9, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '12px' }} />
              <Bar dataKey="caloriesEaten" name="Eaten" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              <Bar dataKey="caloriesBurned" name="Burned" fill="#f97316" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Reveal>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Reveal animation="slide-in-left" delay={300}>
          <div className="glass-panel p-8 rounded-[2.5rem] border border-white/5">
            <h3 className="text-lg font-black text-white italic tracking-tighter mb-6 uppercase flex items-center">
              <Trophy className="mr-3 text-emerald-400" size={20} /> Workouts
            </h3>
            {totals.workouts > 0 ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-950/50 p-4 rounded-2xl text-center">
                    <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Total Time</p>
                    <p className="text-xl font-black text-white mt-1">{totals.duration} min</p>
                  </div>
                  <div className="bg-slate-950/50 p-4 rounded-2xl text-center">
                    <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Avg/Workout</p>
                    <p className="text-xl font-black text-white mt-1">
                      {totals.workouts > 0 ? Math.round(totals.duration / totals.workouts) : 0} min
                    </p>
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={100}>
                  <AreaChart data={dailyData}>
                    <Area type="monotone" dataKey="duration" stroke="#10b981" fill="#10b981" fillOpacity={0.1} strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="py-8 text-center text-slate-500">
                <Dumbbell size={32} className="mx-auto mb-2 text-slate-700" />
                <p className="text-sm">No workouts logged this period</p>
              </div>
            )}
          </div>
        </Reveal>

        <Reveal animation="slide-in-right" delay={400}>
          <div className="glass-panel p-8 rounded-[2.5rem] border border-white/5">
            <h3 className="text-lg font-black text-white italic tracking-tighter mb-6 uppercase flex items-center">
              <Target className="mr-3 text-amber-400" size={20} /> Nutrition
            </h3>
            {totals.meals > 0 ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-950/50 p-4 rounded-2xl text-center">
                    <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Daily Avg Calories</p>
                    <p className="text-xl font-black text-amber-400 mt-1">{dailyAvg?.caloriesEaten || 0}</p>
                  </div>
                  <div className="bg-slate-950/50 p-4 rounded-2xl text-center">
                    <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Daily Avg Protein</p>
                    <p className="text-xl font-black text-blue-400 mt-1">{dailyAvg?.protein || 0}g</p>
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={100}>
                  <AreaChart data={dailyData}>
                    <Area type="monotone" dataKey="protein" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.1} strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="py-8 text-center text-slate-500">
                <Utensils size={32} className="mx-auto mb-2 text-slate-700" />
                <p className="text-sm">No meals logged this period</p>
              </div>
            )}
          </div>
        </Reveal>
      </div>
    </div>
  );
};

export default WeeklyReview;
