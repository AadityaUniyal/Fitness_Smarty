import React, { useState, useEffect } from 'react';
import { Moon, Plus, Trash2, Check, Clock, TrendingUp, Star } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from 'recharts';

const STORAGE_KEY = 'smarty_sleep_logs';

interface SleepEntry {
  date: string;
  hours: number;
  quality: number;
  notes: string;
  timestamp: string;
}

const QUALITY_LABELS = ['Awful', 'Poor', 'Fair', 'Good', 'Great'];

const SleepTracker: React.FC = () => {
  const [entries, setEntries] = useState<SleepEntry[]>(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); } catch { return []; }
  });
  const [hours, setHours] = useState(7);
  const [quality, setQuality] = useState(3);
  const [notes, setNotes] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  }, [entries]);

  const handleLog = () => {
    const entry: SleepEntry = {
      date: new Date().toISOString().split('T')[0],
      hours, quality, notes,
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

  const chartData = entries.slice().reverse().slice(-14).map(e => ({
    date: new Date(e.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    hours: e.hours,
    quality: e.quality * 2,
  }));

  const avgHours = entries.length > 0 ? entries.reduce((s, e) => s + e.hours, 0) / entries.length : 0;
  const avgQuality = entries.length > 0 ? entries.reduce((s, e) => s + e.quality, 0) / entries.length : 0;
  const bestHours = entries.length > 0 ? Math.max(...entries.map(e => e.hours)) : 0;
  const worstHours = entries.length > 0 ? Math.min(...entries.map(e => e.hours)) : 0;

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <div className="w-16 h-16 bg-indigo-500/10 border border-indigo-500/20 rounded-3xl flex items-center justify-center text-indigo-400">
            <Moon size={32} />
          </div>
          <div>
            <h2 className="text-4xl font-black italic tracking-tighter text-white uppercase">Sleep Tracker</h2>
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Log hours & quality to optimize recovery</p>
          </div>
        </div>
        <button onClick={() => setShowForm(!showForm)}
          className="flex items-center space-x-2 px-6 py-3 bg-indigo-500 hover:bg-indigo-400 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest transition">
          <Plus size={16} />
          <span>Log Tonight</span>
        </button>
      </div>

      {showForm && (
        <div className="glass-panel p-8 rounded-[2.5rem] border border-white/5 space-y-6">
          <div>
            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4">
              Hours Slept: <span className="text-indigo-400">{hours}h</span>
            </p>
            <input type="range" min={0} max={12} step={0.5} value={hours} onChange={e => setHours(parseFloat(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-full appearance-none cursor-pointer accent-indigo-500" />
            <div className="flex justify-between text-[8px] text-slate-600 font-black uppercase tracking-widest mt-1">
              <span>0h</span><span>4h</span><span>8h</span><span>12h</span>
            </div>
          </div>
          <div>
            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4">Sleep Quality</p>
            <div className="flex space-x-2">
              {QUALITY_LABELS.map((label, i) => (
                <button key={i} onClick={() => setQuality(i + 1)}
                  className={`flex-1 flex flex-col items-center py-3 rounded-xl text-[9px] font-black uppercase tracking-widest border transition-all ${quality === i + 1
                    ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400'
                    : 'bg-slate-900 border-slate-800 text-slate-600 hover:text-slate-400'}`}>
                  <Star size={14} className={quality >= i + 1 ? 'fill-indigo-400 text-indigo-400' : 'fill-none'} />
                  <span className="mt-1">{label}</span>
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Notes</label>
            <input value={notes} onChange={e => setNotes(e.target.value)} placeholder="How did you sleep?"
              className="w-full mt-2 bg-slate-950 border border-white/10 rounded-xl px-5 py-3 text-xs text-white placeholder:text-slate-600" />
          </div>
          <button onClick={handleLog}
            className="w-full py-4 bg-indigo-500 hover:bg-indigo-400 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest transition">
            Save Entry
          </button>
        </div>
      )}

      {entries.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass-panel p-5 rounded-2xl border border-white/5">
            <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Avg Hours</p>
            <p className="text-2xl font-black text-indigo-400 mt-1">{avgHours.toFixed(1)}<span className="text-xs text-slate-600">h</span></p>
          </div>
          <div className="glass-panel p-5 rounded-2xl border border-white/5">
            <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Avg Quality</p>
            <p className="text-2xl font-black text-emerald-400 mt-1">{avgQuality.toFixed(1)}<span className="text-xs text-slate-600">/5</span></p>
          </div>
          <div className="glass-panel p-5 rounded-2xl border border-white/5">
            <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Best Night</p>
            <p className="text-2xl font-black text-amber-400 mt-1">{bestHours}<span className="text-xs text-slate-600">h</span></p>
          </div>
          <div className="glass-panel p-5 rounded-2xl border border-white/5">
            <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Total Logs</p>
            <p className="text-2xl font-black text-cyan-400 mt-1">{entries.length}<span className="text-xs text-slate-600"> nights</span></p>
          </div>
        </div>
      )}

      {chartData.length > 1 && (
        <div className="glass-panel p-8 rounded-[2.5rem] border border-white/5">
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-6">14-Day Sleep Trends</p>
          <div className="h-64">
            <ResponsiveContainer>
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748b' }} tickLine={false} axisLine={false} />
                <YAxis domain={[0, 12]} tick={{ fontSize: 9, fill: '#64748b' }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', fontSize: '10px', color: '#e2e8f0' }} />
                <Area type="monotone" dataKey="hours" stroke="#818cf8" fill="url(#sleepGradient)" strokeWidth={2} />
                <Area type="monotone" dataKey="quality" stroke="#34d399" fill="url(#qualityGradient)" strokeWidth={1.5} strokeDasharray="4 4" />
                <defs>
                  <linearGradient id="sleepGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#818cf8" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#818cf8" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="qualityGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#34d399" stopOpacity={0.2} />
                    <stop offset="100%" stopColor="#34d399" stopOpacity={0} />
                  </linearGradient>
                </defs>
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-center space-x-6 mt-4">
            <div className="flex items-center space-x-2"><div className="w-3 h-0.5 rounded bg-indigo-400" /><span className="text-[9px] text-slate-500 font-black uppercase tracking-widest">Hours</span></div>
            <div className="flex items-center space-x-2"><div className="w-3 h-0.5 rounded bg-emerald-400" /><span className="text-[9px] text-slate-500 font-black uppercase tracking-widest">Quality (×2)</span></div>
          </div>
        </div>
      )}

      {entries.length > 0 && (
        <div className="glass-panel rounded-[2.5rem] border border-white/5 overflow-hidden">
          <div className="p-6 border-b border-white/5">
            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Sleep History</p>
          </div>
          <div className="divide-y divide-white/5">
            {entries.map((e, i) => (
              <div key={`${e.date}-${i}`} className="flex items-center justify-between p-5 hover:bg-white/[0.02] transition-colors">
                <div className="flex items-center space-x-5">
                  <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-400">
                    <Moon size={18} />
                  </div>
                  <div>
                    <p className="text-sm font-black text-white">{new Date(e.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</p>
                    <div className="flex items-center space-x-3 mt-0.5">
                      <span className="text-[10px] text-indigo-400 font-black">{e.hours}h</span>
                      <div className="flex space-x-0.5">
                        {Array.from({ length: 5 }).map((_, si) => (
                          <Star key={si} size={10} className={si < e.quality ? 'fill-amber-400 text-amber-400' : 'text-slate-700'} />
                        ))}
                      </div>
                      {e.notes && <span className="text-[9px] text-slate-600 italic">— {e.notes}</span>}
                    </div>
                  </div>
                </div>
                <button onClick={() => handleDelete(i)}
                  className="p-2.5 rounded-xl hover:bg-rose-500/10 text-rose-400/60 hover:text-rose-400 transition">
                  {deleteConfirm === i ? <Check size={14} /> : <Trash2 size={14} />}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {entries.length === 0 && !showForm && (
        <div className="glass-panel rounded-[2.5rem] p-16 border border-white/5 text-center">
          <Moon size={48} className="mx-auto text-slate-600 mb-4" />
          <p className="text-lg font-black text-slate-500 uppercase tracking-wider">No sleep data yet</p>
          <p className="text-[10px] font-black text-slate-600 mt-2 uppercase tracking-widest">Start logging your sleep to see recovery trends</p>
        </div>
      )}
    </div>
  );
};

export default SleepTracker;
