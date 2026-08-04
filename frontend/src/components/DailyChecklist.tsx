import React, { useState, useEffect, useCallback } from 'react';
import { Check, Plus, Loader2, ListTodo, Dumbbell, Apple, Droplets, Moon, Sparkles, Heart, X } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const CATEGORY_META: Record<string, { icon: React.ReactNode; label: string; color: string }> = {
  nutrition: { icon: <Apple size={14} />, label: 'Nutrition', color: 'bg-green-500/10 text-green-400 border-green-500/30' },
  exercise: { icon: <Dumbbell size={14} />, label: 'Exercise', color: 'bg-orange-500/10 text-orange-400 border-orange-500/30' },
  hydration: { icon: <Droplets size={14} />, label: 'Hydration', color: 'bg-blue-500/10 text-blue-400 border-blue-500/30' },
  sleep: { icon: <Moon size={14} />, label: 'Sleep', color: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30' },
  mindful: { icon: <Sparkles size={14} />, label: 'Mindful', color: 'bg-purple-500/10 text-purple-400 border-purple-500/30' },
  femme: { icon: <Heart size={14} />, label: 'Femme', color: 'bg-pink-500/10 text-pink-400 border-pink-500/30' },
  general: { icon: <ListTodo size={14} />, label: 'General', color: 'bg-gray-500/10 text-gray-400 border-gray-500/30' },
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
      if (r.ok) { const d = await r.json(); setTasks(d); }
    } catch {} finally { setLoading(false); }
  }, [userId]);

  useEffect(() => { fetchTasks(); }, [fetchTasks]);

  const toggleTask = async (id: number) => {
    // 1. Optimistic UI: Immediately toggle task status in local state
    setTasks(prev => prev.map(t => t.id === id ? { ...t, is_completed: !t.is_completed } : t));
    
    try {
      const r = await fetch(`${API}/api/tasks/${id}/toggle`, { method: 'PUT' });
      if (!r.ok) {
        throw new Error("Failed to toggle task on server");
      }
      onComplete?.(id);
    } catch (err) {
      console.warn("[Optimistic UI] Failed to sync task toggle. Rolling back...");
      // 2. Rollback state if network failed
      setTasks(prev => prev.map(t => t.id === id ? { ...t, is_completed: !t.is_completed } : t));
    }
  };


  const addTask = async () => {
    if (!newTitle.trim()) return;
    try {
      const r = await fetch(`${API}/api/tasks/${userId}?title=${encodeURIComponent(newTitle)}&category=${newCat}`, { method: 'POST' });
      if (r.ok) { setNewTitle(''); await fetchTasks(); }
    } catch {}
  };

  const deleteTask = async (id: number) => {
    try {
      const r = await fetch(`${API}/api/tasks/${id}`, { method: 'DELETE' });
      if (r.ok) setTasks(prev => prev.filter(t => t.id !== id));
    } catch {}
  };

  const autoGenerate = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/tasks/auto-generate/${userId}`, { method: 'POST' });
      if (r.ok) await fetchTasks();
    } catch {}
    setLoading(false);
  };

  const pct = tasks.length ? Math.round((tasks.filter(t => t.is_completed).length / tasks.length) * 100) : 0;

  if (compact) {
    const pending = tasks.filter(t => !t.is_completed);
    return (
      <div className="bg-gray-900/80 border border-gray-700/50 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <ListTodo size={18} className="text-indigo-400" />
          <span className="text-sm font-semibold text-white">Today's Progress</span>
          <span className="text-xs text-gray-400 ml-auto">{tasks.filter(t => t.is_completed).length}/{tasks.length}</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-1.5 mb-3">
          <div className="bg-gradient-to-r from-indigo-500 to-purple-500 h-1.5 rounded-full transition-all" style={{ width: `${pct}%` }} />
        </div>
        {pending.length > 0 && (
          <div className="text-xs text-gray-400 truncate">
            Next: <span className="text-indigo-300">{pending[0].title}</span>
          </div>
        )}
        {pending.length === 0 && tasks.length > 0 && (
          <div className="text-xs text-green-400">All done! Great job!</div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-gray-900/80 border border-gray-700/50 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <ListTodo size={20} className="text-indigo-400" />
          <h2 className="text-lg font-bold text-white">Daily Checklist</h2>
        </div>
        <button onClick={autoGenerate} disabled={loading} className="text-xs bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 px-3 py-1.5 rounded-lg transition flex items-center gap-1">
          {loading ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
          Auto-fill
        </button>
      </div>

      <div className="w-full bg-gray-700 rounded-full h-2 mb-4">
        <div className="bg-gradient-to-r from-indigo-500 to-purple-500 h-2 rounded-full transition-all" style={{ width: `${pct}%` }} />
      </div>
      <div className="text-xs text-gray-400 mb-4 text-center">{pct}% complete ({tasks.filter(t => t.is_completed).length}/{tasks.length})</div>

      <div className="space-y-2 max-h-80 overflow-y-auto custom-scrollbar">
        {tasks.map(task => {
          const meta = CATEGORY_META[task.category] || CATEGORY_META.general;
          return (
            <div key={task.id} className={`flex items-start gap-3 p-3 rounded-lg border transition cursor-pointer ${task.is_completed ? 'bg-gray-800/40 border-gray-700/30 opacity-60' : 'bg-gray-800/60 border-gray-700/50 hover:bg-gray-700/60'}`}
              onClick={() => toggleTask(task.id)}>
              <div className={`mt-0.5 w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition ${task.is_completed ? 'bg-green-500 border-green-500' : 'border-gray-500 hover:border-indigo-400'}`}>
                {task.is_completed && <Check size={12} className="text-white" />}
              </div>
              <div className="flex-1 min-w-0">
                <div className={`text-sm font-medium truncate ${task.is_completed ? 'text-gray-500 line-through' : 'text-gray-200'}`}>{task.title}</div>
                {task.description && <div className="text-xs text-gray-500 mt-0.5 truncate">{task.description}</div>}
              </div>
              <div className={`flex items-center gap-1.5 text-[10px] px-2 py-0.5 rounded-full border ${meta.color} flex-shrink-0`}>
                {meta.icon} <span>{meta.label}</span>
              </div>
              <button onClick={(e) => { e.stopPropagation(); deleteTask(task.id); }} className="text-gray-600 hover:text-red-400 transition flex-shrink-0">
                <X size={14} />
              </button>
            </div>
          );
        })}
        {!loading && tasks.length === 0 && (
          <div className="text-center py-8 text-gray-500 text-sm">
            <ListTodo size={32} className="mx-auto mb-2 opacity-40" />
            No tasks yet. Click <span className="text-indigo-400">Auto-fill</span> to generate!
          </div>
        )}
      </div>

      <div className="flex gap-2 mt-4">
        <input value={newTitle} onChange={e => setNewTitle(e.target.value)} placeholder="Add a custom task..." className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          onKeyDown={e => e.key === 'Enter' && addTask()} />
        <button onClick={addTask} disabled={!newTitle.trim()} className="bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 px-3 py-2 rounded-lg transition disabled:opacity-40">
          <Plus size={16} />
        </button>
      </div>
    </div>
  );
}
