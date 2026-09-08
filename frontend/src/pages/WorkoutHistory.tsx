import React, { useState, useMemo, useEffect } from 'react';
import { Dumbbell, Flame, Clock, Calendar, Filter, Trash2, Check, BarChart3, ChevronDown, ChevronUp, Trophy } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from 'recharts';
import { fetchWorkoutHistory } from '../services/apiService';
import { useCurrentUserId } from '../hooks/useCurrentUserId';

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
  const userId = useCurrentUserId();
  const [logs, setLogs] = useState<WorkoutLog[]>(() => {
    try { return JSON.parse(localStorage.getItem('smarty_workout_logs') || '[]'); } catch { return []; }
  });
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [filterDays, setFilterDays] = useState(0);

  useEffect(() => {
    const load = async () => {
      const data = await fetchWorkoutHistory(userId, 200);
      if (data?.workouts && Array.isArray(data.workouts)) {
        setLogs(data.workouts);
        localStorage.setItem('smarty_workout_logs', JSON.stringify(data.workouts));
      }
    };
    load();
  }, [userId]);

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
  }), [filtered]);

  const chartData = useMemo(() => {
    const map = new Map<string, { date: string; calories: number }>();
    filtered.slice().reverse().forEach(l => {
      const key = new Date(l.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      const existing = map.get(key) || { date: key, calories: 0 };
      existing.calories += l.caloriesBurned || 0;
      map.set(key, existing);
    });
    return Array.from(map.values());
  }, [filtered]);

  const handleDelete = (idx: number) => {
    const targetItem = filtered[idx];
    if (deleteConfirm === idx) {
      const updated = logs.filter(l => l !== targetItem);
      setLogs(updated);
      localStorage.setItem('smarty_workout_logs', JSON.stringify(updated));
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
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Every session logged</p>
          </div>
        </div>
      </div>

      {chartData.length > 1 && (
        <div className="glass-panel p-6 rounded-3xl border border-white/5 space-y-4">
          <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest">Activity Trend</h3>
          <div className="h-40 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" fontSize={10} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '11px' }} />
                <Bar dataKey="calories" fill="#f97316" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {filtered.length > 0 && (
        <div className="space-y-4">
          {bestWorkout && (
            <div className="glass-panel p-6 rounded-3xl border border-amber-500/20 bg-amber-500/5 flex items-center space-x-4">
              <Trophy size={24} className="text-amber-400" />
              <div>
                <p className="text-[9px] font-black text-amber-400 uppercase">Best Session</p>
                <p className="text-base font-black text-white">{bestWorkout.name}</p>
                <p className="text-xs text-slate-400">{bestWorkout.caloriesBurned} cal • {bestWorkout.duration} min</p>
              </div>
            </div>
          )}

          <div className="glass-panel rounded-3xl border border-white/5 overflow-hidden">
            <div className="p-4 border-b border-white/5 flex items-center justify-between text-xs text-slate-400 font-bold">
              <span>{filtered.length} Workouts</span>
              <span>{totals.totalCalories} total calories burned</span>
            </div>
            <div className="divide-y divide-white/5">
              {filtered.map((log, i) => (
                <div key={`${log.timestamp}-${i}`} className="p-4 flex items-center justify-between hover:bg-white/5 transition-colors">
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 rounded-xl bg-orange-500/10 flex items-center justify-center text-orange-400">
                      <Dumbbell size={18} />
                    </div>
                    <div>
                      <p className="text-sm font-black text-white">{log.name}</p>
                      <p className="text-xs text-slate-400">{log.duration} min • {log.caloriesBurned} cal • {new Date(log.timestamp).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <button onClick={() => handleDelete(i)} className="p-2 text-rose-400 hover:bg-rose-500/10 rounded-xl transition-all">
                    {deleteConfirm === i ? <Check size={16} /> : <Trash2 size={16} />}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {filtered.length === 0 && (
        <div className="glass-panel rounded-3xl p-12 text-center text-slate-500 space-y-2">
          <Dumbbell size={40} className="mx-auto text-slate-600" />
          <p className="text-sm font-medium">No workouts logged yet</p>
        </div>
      )}
    </div>
  );
};

export default WorkoutHistory;
