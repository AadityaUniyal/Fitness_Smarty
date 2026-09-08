import React, { useState, useEffect, useCallback } from 'react';
import { Check, Plus, Loader2, ListTodo, Dumbbell, Apple, Droplets, Moon, Sparkles, Heart, X } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const CATEGORY_META: Record<string, { icon: React.ReactNode; label: string; color: string }> = {
  nutrition: { icon: <Apple size={14} />, label: 'Nutrition', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' },
  exercise: { icon: <Dumbbell size={14} />, label: 'Exercise', color: 'bg-orange-500/10 text-orange-400 border-orange-500/30' },
  hydration: { icon: <Droplets size={14} />, label: 'Hydration', color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' },
  sleep: { icon: <Moon size={14} />, label: 'Sleep', color: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30' },
  mindful: { icon: <Sparkles size={14} />, label: 'Mindful', color: 'bg-purple-500/10 text-purple-400 border-purple-500/30' },
  femme: { icon: <Heart size={14} />, label: 'Femme', color: 'bg-pink-500/10 text-pink-400 border-pink-500/30' },
  general: { icon: <ListTodo size={14} />, label: 'General', color: 'bg-slate-500/10 text-slate-400 border-slate-500/30' },
};

interface Task {
  id: number; title: string; category: string; is_completed: boolean;
  priority: number; description?: string; is_auto?: boolean; source?: string;
}

interface Props {
  userId: number;
  onComplete?: (taskId: number) => void;
  compact?: boolean;
}

export default function DailyChecklist({ userId, onComplete, compact }: Props) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [newTitle, setNewTitle] = useState('');
  const [newCat, setNewCat] = useState('general');

  const fetchTasks = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/tasks/${userId}`);
      if (r.ok) { const d = await r.json(); setTasks(Array.isArray(d) ? d : (d.tasks || [])); }
    } catch {} finally { setLoading(false); }
  }, [userId]);

  useEffect(() => { fetchTasks(); }, [fetchTasks]);

  const toggleTask = async (id: number) => {
    const taskList = Array.isArray(tasks) ? tasks : [];
    const orig = [...taskList];
    setTasks(ts => (Array.isArray(ts) ? ts : []).map(t => t.id === id ? { ...t, is_completed: !t.is_completed } : t));
    try {
      const r = await fetch(`${API}/api/tasks/${id}/complete`, { method: 'POST' });
      if (r.ok && onComplete) onComplete(id);
      if (!r.ok) setTasks(orig);
    } catch { setTasks(orig); }
  };

  const addTask = async () => {
    if (!newTitle.trim()) return;
    try {
      const r = await fetch(`${API}/api/tasks/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, title: newTitle, category: newCat, priority: 2 }),
      });
      if (r.ok) { setNewTitle(''); fetchTasks(); }
    } catch {}
  };

  const deleteTask = async (id: number) => {
    setTasks(ts => (Array.isArray(ts) ? ts : []).filter(t => t.id !== id));
    try { await fetch(`${API}/api/tasks/${id}`, { method: 'DELETE' }); } catch {}
  };

  const autoGenerate = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/tasks/generate/${userId}`, { method: 'POST' });
      if (r.ok) { const d = await r.json(); setTasks(Array.isArray(d) ? d : (d.tasks || [])); }
    } catch {}
    setLoading(false);
  };

  const taskList = Array.isArray(tasks) ? tasks : [];
  const pct = taskList.length ? Math.round((taskList.filter(t => t.is_completed).length / taskList.length) * 100) : 0;

  if (compact) {
    const pending = taskList.filter(t => !t.is_completed);
    return (
      <div className="glass-panel p-5 rounded-[2rem] border border-white/10 card-3d">
        <div className="flex items-center gap-2 mb-3">
          <ListTodo size={18} className="text-indigo-400" />
          <span className="text-sm font-black italic uppercase tracking-tight text-white">Today's Progress</span>
          <span className="text-xs font-bold text-slate-400 ml-auto">{taskList.filter(t => t.is_completed).length}/{taskList.length}</span>
        </div>
        <div className="w-full bg-slate-900 rounded-full h-2 mb-3 border border-white/5 overflow-hidden">
          <div className="bg-gradient-to-r from-indigo-500 to-purple-500 h-2 rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
        </div>
        {pending.length > 0 && (
          <div className="text-xs text-slate-400 truncate">
            Next Target: <span className="text-indigo-300 font-bold">{pending[0].title}</span>
          </div>
        )}
        {pending.length === 0 && taskList.length > 0 && (
          <div className="text-xs font-bold text-emerald-400">All targets completed!</div>
        )}
      </div>
    );
  }

  return (
    <div className="glass-panel p-6 rounded-[2.5rem] border border-white/10 space-y-4 card-3d">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <ListTodo size={20} className="text-indigo-400" />
          <h2 className="text-lg font-black italic uppercase text-white tracking-tight">Daily Protocol</h2>
        </div>
        <button onClick={autoGenerate} disabled={loading} className="text-xs font-bold bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 px-3.5 py-2 rounded-xl transition flex items-center gap-1.5 border border-indigo-500/30">
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
          Auto-fill Tasks
        </button>
      </div>

      <div className="w-full bg-slate-900 rounded-full h-2 border border-white/5 overflow-hidden">
        <div className="bg-gradient-to-r from-indigo-500 to-purple-500 h-2 rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
      </div>
      <div className="text-[10px] font-black uppercase tracking-widest text-slate-400 text-center">{pct}% Complete ({taskList.filter(t => t.is_completed).length}/{taskList.length})</div>

      <div className="space-y-2.5 max-h-80 overflow-y-auto custom-scrollbar">
        {taskList.map(task => {
          const meta = CATEGORY_META[task.category] || CATEGORY_META.general;
          return (
            <div key={task.id} className={`flex items-start gap-3 p-3.5 rounded-2xl border transition cursor-pointer ${task.is_completed ? 'bg-slate-950/40 border-white/5 opacity-60' : 'bg-slate-900/80 border-white/10 hover:border-indigo-500/30'}`}
              onClick={() => toggleTask(task.id)}>
              <div className={`mt-0.5 w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition ${task.is_completed ? 'bg-emerald-500 border-emerald-500' : 'border-slate-500 hover:border-indigo-400'}`}>
                {task.is_completed && <Check size={12} className="text-slate-950 font-bold" />}
              </div>
              <div className="flex-1 min-w-0">
                <div className={`text-xs font-bold truncate ${task.is_completed ? 'text-slate-500 line-through' : 'text-slate-100'}`}>{task.title}</div>
                {task.description && <div className="text-[10px] text-slate-400 mt-0.5 truncate">{task.description}</div>}
              </div>
              <div className={`flex items-center gap-1.5 text-[9px] font-bold px-2.5 py-1 rounded-full border ${meta.color} flex-shrink-0 uppercase tracking-wider`}>
                {meta.icon} <span>{meta.label}</span>
              </div>
              <button onClick={(e) => { e.stopPropagation(); deleteTask(task.id); }} className="text-slate-500 hover:text-rose-400 transition flex-shrink-0 p-1">
                <X size={14} />
              </button>
            </div>
          );
        })}
        {!loading && tasks.length === 0 && (
          <div className="text-center py-8 text-slate-400 text-xs font-bold">
            <ListTodo size={32} className="mx-auto mb-2 opacity-40" />
            No tasks yet. Click <span className="text-indigo-400">Auto-fill</span> to generate!
          </div>
        )}
      </div>

      <div className="flex gap-2 pt-2">
        <input value={newTitle} onChange={e => setNewTitle(e.target.value)} placeholder="Add a custom task..." className="flex-1 bg-slate-900 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
          onKeyDown={e => e.key === 'Enter' && addTask()} />
        <button onClick={addTask} className="px-4 py-2.5 bg-indigo-500 hover:bg-indigo-400 text-slate-950 font-black text-xs uppercase tracking-widest rounded-xl transition">
          <Plus size={16} />
        </button>
      </div>
    </div>
  );
}
