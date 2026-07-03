import React, { useState, useEffect } from 'react';
import { Smile, Frown, Meh, Angry, Heart, Activity, BarChart3, Plus, Trash2, Check } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid, Area, AreaChart } from 'recharts';

const STORAGE_KEY = 'smarty_mood_logs';

interface MoodEntry {
  date: string;
  mood: number; // 1-5
  energy: number; // 1-5
  notes: string;
  timestamp: string;
}

const MOOD_OPTIONS = [
  { value: 1, label: 'Terrible', icon: <Angry size={20} />, color: 'text-rose-400', bg: 'bg-rose-500/10' },
  { value: 2, label: 'Bad', icon: <Frown size={20} />, color: 'text-orange-400', bg: 'bg-orange-500/10' },
  { value: 3, label: 'Okay', icon: <Meh size={20} />, color: 'text-amber-400', bg: 'bg-amber-500/10' },
  { value: 4, label: 'Good', icon: <Smile size={20} />, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
  { value: 5, label: 'Amazing', icon: <Heart size={20} />, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
];

const ENERGY_OPTIONS = [
  { value: 1, label: 'Exhausted', color: 'text-rose-400' },
  { value: 2, label: 'Low', color: 'text-orange-400' },
  { value: 3, label: 'Moderate', color: 'text-amber-400' },
  { value: 4, label: 'High', color: 'text-emerald-400' },
  { value: 5, label: 'Max', color: 'text-emerald-400' },
];

const MoodTracker: React.FC = () => {
  const [entries, setEntries] = useState<MoodEntry[]>(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); } catch { return []; }
  });
  const [mood, setMood] = useState(3);
  const [energy, setEnergy] = useState(3);
  const [notes, setNotes] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  }, [entries]);

  const handleLog = () => {
    const entry: MoodEntry = {
      date: new Date().toISOString().split('T')[0],
      mood, energy, notes,
      timestamp: new Date().toISOString(),
    };
    setEntries(prev => [entry, ...prev]);
    setShowForm(false);
    setNotes('');
  };

  const handleDelete = (idx: number) => {
    if (deleteConfirm === idx) {
      setEntries(prev => prev.filter((_, i) => i !== idx));
      setDeleteConfirm(null);
    } else {
      setDeleteConfirm(idx);
      setTimeout(() => setDeleteConfirm(null), 3000);
    }
  };

  // Chart data: last 14 days
  const chartData = entries.slice().reverse().slice(-14).map(e => ({
    date: new Date(e.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    mood: e.mood,
    energy: e.energy,
  }));

  const avgMood = entries.length > 0 ? entries.reduce((s, e) => s + e.mood, 0) / entries.length : 0;
  const avgEnergy = entries.length > 0 ? entries.reduce((s, e) => s + e.energy, 0) / entries.length : 0;

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <div className="w-16 h-16 bg-purple-500/10 border border-purple-500/20 rounded-3xl flex items-center justify-center text-purple-400">
            <Activity size={32} />
          </div>
          <div>
            <h2 className="text-4xl font-black italic tracking-tighter text-white uppercase">Mood & Energy</h2>
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Track how you feel before & after workouts</p>
          </div>
        </div>
        <button onClick={() => setShowForm(!showForm)}
          className="flex items-center space-x-2 px-6 py-3 bg-purple-500 hover:bg-purple-400 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest transition">
          <Plus size={16} />
          <span>Log Today</span>
        </button>
      </div>

      {showForm && (
        <div className="glass-panel p-8 rounded-[2.5rem] border border-white/5 space-y-6">
          <div>
            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4">How are you feeling?</p>
            <div className="flex space-x-3">
              {MOOD_OPTIONS.map(opt => (
                <button key={opt.value} onClick={() => setMood(opt.value)}
                  className={`flex-1 flex flex-col items-center space-y-2 p-4 rounded-2xl border transition-all ${mood === opt.value ? `${opt.bg} ${opt.color} border-${opt.color.split('-')[1]}-500/30` : 'bg-slate-900 border-slate-800 text-slate-600 hover:text-slate-400'}`}>
                  {opt.icon}
                  <span className="text-[9px] font-black uppercase tracking-widest">{opt.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4">Energy Level</p>
            <div className="flex space-x-2">
              {ENERGY_OPTIONS.map(opt => (
                <button key={opt.value} onClick={() => setEnergy(opt.value)}
                  className={`flex-1 py-3 rounded-xl text-[9px] font-black uppercase tracking-widest border transition-all ${energy === opt.value ? `${opt.color} bg-${opt.color.split('-')[1]}-500/10 border-${opt.color.split('-')[1]}-500/30` : 'bg-slate-900 border-slate-800 text-slate-600 hover:text-slate-400'}`}>
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2 block">Notes (optional)</label>
            <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={2}
              className="w-full bg-slate-950 border border-white/10 rounded-xl px-4 py-3 text-sm text-white resize-none"
              placeholder="How was your workout? Any pain or fatigue?" />
          </div>

          <div className="flex space-x-3">
            <button onClick={handleLog} className="px-6 py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-xl font-black text-[10px] uppercase tracking-widest transition">
              Log Entry
            </button>
            <button onClick={() => setShowForm(false)} className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded-xl font-black text-[10px] uppercase tracking-widest transition">
              Cancel
            </button>
          </div>
        </div>
      )}

      {entries.length > 0 ? (
        <>
          {/* Averages */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-purple-500/10 border border-purple-500/20 p-6 rounded-3xl text-center">
              <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Avg Mood</p>
              <p className="text-3xl font-black text-purple-400 mt-1">{avgMood.toFixed(1)}</p>
              <p className="text-[8px] text-slate-600">/ 5</p>
            </div>
            <div className="bg-emerald-500/10 border border-emerald-500/20 p-6 rounded-3xl text-center">
              <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Avg Energy</p>
              <p className="text-3xl font-black text-emerald-400 mt-1">{avgEnergy.toFixed(1)}</p>
              <p className="text-[8px] text-slate-600">/ 5</p>
            </div>
            <div className="bg-amber-500/10 border border-amber-500/20 p-6 rounded-3xl text-center">
              <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Total Logs</p>
              <p className="text-3xl font-black text-amber-400 mt-1">{entries.length}</p>
              <p className="text-[8px] text-slate-600">entries</p>
            </div>
            <div className="bg-cyan-500/10 border border-cyan-500/20 p-6 rounded-3xl text-center">
              <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Best Mood</p>
              <p className="text-3xl font-black text-cyan-400 mt-1">{Math.max(...entries.map(e => e.mood))}</p>
              <p className="text-[8px] text-slate-600">/ 5</p>
            </div>
          </div>

          {/* Chart */}
          {chartData.length > 1 && (
            <div className="glass-panel p-8 rounded-[2.5rem] border border-white/5">
              <div className="flex items-center space-x-3 mb-6">
                <BarChart3 size={18} className="text-purple-400" />
                <h3 className="text-lg font-black text-white italic tracking-tighter uppercase">Trend (Last 14)</h3>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 5]} ticks={[1, 2, 3, 4, 5]} tick={{ fontSize: 9, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '12px' }} />
                  <Area type="monotone" dataKey="mood" name="Mood" stroke="#a78bfa" fill="#a78bfa" fillOpacity={0.1} strokeWidth={2.5} dot={{ r: 4 }} />
                  <Area type="monotone" dataKey="energy" name="Energy" stroke="#34d399" fill="#34d399" fillOpacity={0.1} strokeWidth={2.5} dot={{ r: 4 }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* History */}
          <div className="space-y-3">
            <h3 className="text-sm font-black text-slate-500 uppercase tracking-widest">Recent Logs</h3>
            {entries.slice(0, 20).map((entry, i) => (
              <div key={i} className="glass-panel p-5 rounded-2xl border border-white/5 card-hover flex items-start justify-between group">
                <div className="flex items-start space-x-4">
                  <div className={`p-2 rounded-xl ${MOOD_OPTIONS[entry.mood - 1]?.bg || 'bg-slate-800'}`}>
                    {MOOD_OPTIONS[entry.mood - 1]?.icon || <Meh size={16} />}
                  </div>
                  <div>
                    <div className="flex items-center space-x-3">
                      <p className="text-sm font-black text-white">
                        {MOOD_OPTIONS[entry.mood - 1]?.label} • Energy: {ENERGY_OPTIONS[entry.energy - 1]?.label}
                      </p>
                    </div>
                    <p className="text-[10px] text-slate-500 mt-0.5">
                      {new Date(entry.timestamp).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}
                    </p>
                    {entry.notes && <p className="text-xs text-slate-400 mt-2 italic">"{entry.notes}"</p>}
                  </div>
                </div>
                <button onClick={() => handleDelete(i)}
                  className={`p-2 rounded-lg transition ${deleteConfirm === i ? 'bg-rose-500/20 text-rose-400' : 'opacity-0 group-hover:opacity-100 text-slate-500 hover:text-rose-400'}`}>
                  {deleteConfirm === i ? <Check size={14} /> : <Trash2 size={14} />}
                </button>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="glass-panel p-16 rounded-[2.5rem] border border-white/5 text-center">
          <Activity size={48} className="mx-auto mb-4 text-slate-700" />
          <p className="text-slate-500 text-sm">No mood logs yet. Start tracking how you feel!</p>
          <p className="text-[10px] text-slate-600 mt-2">Logging mood helps you identify patterns in your training.</p>
        </div>
      )}
    </div>
  );
};

export default MoodTracker;
