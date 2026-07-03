import React, { useState, useMemo } from 'react';
import { Dumbbell, Flame, Clock, Calendar, Filter, Trash2, Check, BarChart3, ChevronDown, ChevronUp, Trophy } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid, AreaChart, Area } from 'recharts';

interface WorkoutLog {
  name: string;
  duration: number;
  caloriesBurned: number;
  exercisesCompleted: number;
  exercisesTotal: number;
  timestamp: string;
  goal: string;
}

const WorkoutHistory: React.FC = () => {
  const [logs, setLogs] = useState<WorkoutLog[]>(() => {
    try { return JSON.parse(localStorage.getItem('smarty_workout_logs') || '[]'); } catch { return []; }
  });
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [filterDays, setFilterDays] = useState(0);

  const filtered = useMemo(() => {
    if (filterDays === 0) return logs;
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - filterDays);
    return logs.filter(l => new Date(l.timestamp) >= cutoff);
  }, [logs, filterDays]);

  const totals = useMemo(() => ({
    workouts: filtered.length,
    totalMinutes: filtered.reduce((s, l) => s + (l.duration || 0), 0),
    totalCalories: filtered.reduce((s, l) => s + (l.caloriesBurned || 0), 0),
    avgDuration: filtered.length > 0 ? filtered.reduce((s, l) => s + (l.duration || 0), 0) / filtered.length : 0,
    avgCalories: filtered.length > 0 ? filtered.reduce((s, l) => s + (l.caloriesBurned || 0), 0) / filtered.length : 0,
  }), [filtered]);

  const streakDays = useMemo(() => {
    if (logs.length === 0) return 0;
    const dates = [...new Set(logs.map(l => new Date(l.timestamp).toDateString()))].sort().reverse();
    let streak = 1;
    for (let i = 1; i < dates.length; i++) {
      const prev = new Date(dates[i - 1]);
      const curr = new Date(dates[i]);
      const diff = (prev.getTime() - curr.getTime()) / 86400000;
      if (Math.round(diff) === 1) streak++;
      else break;
    }
    return streak;
  }, [logs]);

  const chartData = useMemo(() => {
    const map = new Map<string, { date: string; duration: number; calories: number; count: number }>();
    filtered.forEach(l => {
      const key = new Date(l.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      const existing = map.get(key) || { date: key, duration: 0, calories: 0, count: 0 };
      existing.duration += l.duration || 0;
      existing.calories += l.caloriesBurned || 0;
      existing.count += 1;
      map.set(key, existing);
    });
    return Array.from(map.values());
  }, [filtered]);

  const handleDelete = (idx: number) => {
    const realIdx = logs.findIndex(l => l === filtered[idx]);
    if (deleteConfirm === idx) {
      setLogs(prev => prev.filter((_, i) => i !== realIdx));
      setDeleteConfirm(null);
    } else {
      setDeleteConfirm(idx);
      setTimeout(() => setDeleteConfirm(null), 3000);
    }
  };

  const bestWorkout = useMemo(() => {
    if (filtered.length === 0) return null;
    return filtered.reduce((best, l) => (l.caloriesBurned || 0) > (best.caloriesBurned || 0) ? l : best, filtered[0]);
  }, [filtered]);

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <div className="w-16 h-16 bg-orange-500/10 border border-orange-500/20 rounded-3xl flex items-center justify-center text-orange-400">
            <Dumbbell size={32} />
          </div>
          <div>
            <h2 className="text-4xl font-black italic tracking-tighter text-white uppercase">Workout History</h2>
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Every rep, every set, every session</p>
          </div>
        </div>
        <div className="flex bg-slate-900 border border-white/10 rounded-2xl p-1">
          {[
            { label: 'All', value: 0 },
            { label: '7D', value: 7 },
            { label: '30D', value: 30 },
            { label: '90D', value: 90 },
          ].map(f => (
            <button key={f.value} onClick={() => setFilterDays(f.value)}
              className={`px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all ${filterDays === f.value ? 'bg-orange-500 text-slate-950' : 'text-slate-500 hover:text-orange-400'}`}>
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {filtered.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass-panel p-5 rounded-2xl border border-white/5">
            <Dumbbell size={16} className="text-orange-400 mb-2" />
            <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Workouts</p>
            <p className="text-2xl font-black text-white mt-1">{totals.workouts}</p>
          </div>
          <div className="glass-panel p-5 rounded-2xl border border-white/5">
            <Clock size={16} className="text-indigo-400 mb-2" />
            <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Total Time</p>
            <p className="text-2xl font-black text-indigo-400 mt-1">{totals.totalMinutes}<span className="text-xs text-slate-600"> min</span></p>
          </div>
          <div className="glass-panel p-5 rounded-2xl border border-white/5">
            <Flame size={16} className="text-rose-400 mb-2" />
            <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Calories Burned</p>
            <p className="text-2xl font-black text-rose-400 mt-1">{totals.totalCalories.toLocaleString()}</p>
          </div>
          <div className="glass-panel p-5 rounded-2xl border border-white/5">
            <Calendar size={16} className="text-emerald-400 mb-2" />
            <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Streak</p>
            <p className="text-2xl font-black text-emerald-400 mt-1">{streakDays}<span className="text-xs text-slate-600"> days</span></p>
          </div>
        </div>
      )}

      {chartData.length > 1 && (
        <div className="glass-panel p-8 rounded-[2.5rem] border border-white/5">
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-6">Trends</p>
          <div className="h-56">
            <ResponsiveContainer>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748b' }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 9, fill: '#64748b' }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', fontSize: '10px', color: '#e2e8f0' }} />
                <Bar dataKey="calories" fill="#f97316" radius={[4, 4, 0, 0]} opacity={0.8} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {filtered.length > 0 && (
        <>
          {bestWorkout && (
            <div className="glass-panel p-6 rounded-[2.5rem] border border-amber-500/10 bg-amber-500/[0.02]">
              <div className="flex items-center space-x-3 mb-3">
                <Trophy size={16} className="text-amber-400" />
                <span className="text-[9px] font-black text-amber-400 uppercase tracking-widest">Best Session</span>
              </div>
              <p className="text-lg font-black text-white">{bestWorkout.name}</p>
              <div className="flex items-center space-x-4 mt-2">
                <span className="text-[10px] text-slate-400"><Flame size={12} className="inline mr-1 text-rose-400" />{bestWorkout.caloriesBurned} cal</span>
                <span className="text-[10px] text-slate-400"><Clock size={12} className="inline mr-1 text-indigo-400" />{bestWorkout.duration} min</span>
              </div>
            </div>
          )}

          <div className="glass-panel rounded-[2.5rem] border border-white/5 overflow-hidden">
            <div className="p-6 border-b border-white/5 flex items-center justify-between">
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{filtered.length} Sessions</p>
              <Filter size={14} className="text-slate-600" />
            </div>
            <div className="divide-y divide-white/5">
              {filtered.map((log, i) => (
                <div key={`${log.timestamp}-${i}`}>
                  <div className="flex items-center justify-between p-5 hover:bg-white/[0.02] transition-colors">
                    <div className="flex items-center space-x-5 flex-1 min-w-0" onClick={() => setExpanded(expanded === i ? null : i)}>
                      <div className="w-10 h-10 rounded-xl bg-orange-500/10 flex items-center justify-center text-orange-400 shrink-0">
                        <Dumbbell size={18} />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center space-x-3">
                          <p className="text-sm font-black text-white truncate">{log.name}</p>
                          {expanded === i ? <ChevronUp size={14} className="text-slate-600 shrink-0" /> : <ChevronDown size={14} className="text-slate-600 shrink-0" />}
                        </div>
                        <div className="flex items-center space-x-4 mt-0.5 flex-wrap">
                          <span className="text-[10px] text-orange-400 font-black">{log.duration} min</span>
                          <span className="text-[10px] text-rose-400 font-black">{log.caloriesBurned || 0} cal</span>
                          <span className="text-[9px] text-slate-600">{new Date(log.timestamp).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric' })}</span>
                        </div>
                      </div>
                    </div>
                    <button onClick={() => handleDelete(i)}
                      className="ml-3 p-2.5 rounded-xl hover:bg-rose-500/10 text-rose-400/60 hover:text-rose-400 transition shrink-0">
                      {deleteConfirm === i ? <Check size={14} /> : <Trash2 size={14} />}
                    </button>
                  </div>
                  {expanded === i && (
                    <div className="px-5 pb-5 pt-0 ml-16 space-y-2">
                      <div className="grid grid-cols-3 gap-3">
                        <div className="bg-slate-900 rounded-xl p-3">
                          <p className="text-[8px] text-slate-500 font-black uppercase tracking-widest">Exercises</p>
                          <p className="text-base font-black text-white">{log.exercisesCompleted || '—'} <span className="text-[9px] text-slate-600">/ {log.exercisesTotal || '—'}</span></p>
                        </div>
                        <div className="bg-slate-900 rounded-xl p-3">
                          <p className="text-[8px] text-slate-500 font-black uppercase tracking-widest">Pace</p>
                          <p className="text-base font-black text-emerald-400">{log.duration > 0 ? (log.caloriesBurned / log.duration).toFixed(1) : '—'} <span className="text-[9px] text-slate-600">cal/min</span></p>
                        </div>
                        <div className="bg-slate-900 rounded-xl p-3">
                          <p className="text-[8px] text-slate-500 font-black uppercase tracking-widest">Goal</p>
                          <p className="text-base font-black text-amber-400 uppercase">{log.goal?.replace('_', ' ') || 'General'}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {filtered.length === 0 && (
        <div className="glass-panel rounded-[2.5rem] p-16 border border-white/5 text-center">
          <Dumbbell size={48} className="mx-auto text-slate-600 mb-4" />
          <p className="text-lg font-black text-slate-500 uppercase tracking-wider">No workouts logged yet</p>
          <p className="text-[10px] font-black text-slate-600 mt-2 uppercase tracking-widest">Complete a session to see it here</p>
        </div>
      )}
    </div>
  );
};

export default WorkoutHistory;
