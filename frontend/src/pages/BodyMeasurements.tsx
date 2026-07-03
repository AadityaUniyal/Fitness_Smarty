import React, { useState, useEffect } from 'react';
import { Ruler, Plus, TrendingUp, Trash2, Check, Activity } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from 'recharts';

const STORAGE_KEY = 'smarty_body_measurements';

const MEASUREMENT_FIELDS = [
  { key: 'weight', label: 'Weight (kg)', color: '#10b981' },
  { key: 'waist', label: 'Waist (cm)', color: '#f59e0b' },
  { key: 'hips', label: 'Hips (cm)', color: '#8b5cf6' },
  { key: 'chest', label: 'Chest (cm)', color: '#06b6d4' },
  { key: 'leftArm', label: 'Left Arm (cm)', color: '#f97316' },
  { key: 'rightArm', label: 'Right Arm (cm)', color: '#ef4444' },
  { key: 'leftThigh', label: 'Left Thigh (cm)', color: '#6366f1' },
  { key: 'rightThigh', label: 'Right Thigh (cm)', color: '#ec4899' },
];

interface MeasurementEntry {
  date: string;
  weight?: number;
  waist?: number;
  hips?: number;
  chest?: number;
  leftArm?: number;
  rightArm?: number;
  leftThigh?: number;
  rightThigh?: number;
}

const loadData = (): MeasurementEntry[] => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) return JSON.parse(saved);
  } catch {}
  const profile = JSON.parse(localStorage.getItem('smarty_profile') || '{}');
  if (profile.weight) {
    const today = new Date().toISOString().split('T')[0];
    return [{ date: today, weight: profile.weight }];
  }
  return [];
};

const BodyMeasurements: React.FC = () => {
  const [entries, setEntries] = useState<MeasurementEntry[]>(loadData);
  const [showForm, setShowForm] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState('weight');
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);
  const [newEntry, setNewEntry] = useState<MeasurementEntry>({
    date: new Date().toISOString().split('T')[0],
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  }, [entries]);

  const handleAdd = () => {
    if (!newEntry.date) return;
    // Check if entry for this date exists, merge or add
    const existingIdx = entries.findIndex(e => e.date === newEntry.date);
    if (existingIdx >= 0) {
      const updated = [...entries];
      updated[existingIdx] = { ...updated[existingIdx], ...newEntry };
      setEntries(updated);
    } else {
      setEntries([...entries, newEntry].sort((a, b) => a.date.localeCompare(b.date)));
    }
    setShowForm(false);
    setNewEntry({ date: new Date().toISOString().split('T')[0] });
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

  const selectedField = MEASUREMENT_FIELDS.find(f => f.key === selectedMetric);
  const chartData = entries.map(e => ({
    date: new Date(e.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    value: (e as any)[selectedMetric],
    fullDate: e.date,
  })).filter(d => d.value != null);

  const latest = entries.length > 0 ? entries[entries.length - 1] : null;
  const first = entries.length > 1 ? entries[0] : null;
  const change = latest && first
    ? ((latest as any)[selectedMetric] ?? 0) - ((first as any)[selectedMetric] ?? 0)
    : null;

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <div className="w-16 h-16 bg-cyan-500/10 border border-cyan-500/20 rounded-3xl flex items-center justify-center text-cyan-400">
            <Ruler size={32} />
          </div>
          <div>
            <h2 className="text-4xl font-black italic tracking-tighter text-white uppercase">Body Measurements</h2>
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Track your physique changes over time</p>
          </div>
        </div>
        <button onClick={() => setShowForm(!showForm)}
          className="flex items-center space-x-2 px-6 py-3 bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest transition">
          <Plus size={16} />
          <span>Log Measurement</span>
        </button>
      </div>

      {showForm && (
        <div className="glass-panel p-8 rounded-[2.5rem] border border-white/5 space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Date</label>
              <input type="date" value={newEntry.date} onChange={e => setNewEntry({ ...newEntry, date: e.target.value })}
                className="w-full bg-slate-950 border border-white/10 rounded-xl px-4 py-3 text-xs text-white" />
            </div>
            {MEASUREMENT_FIELDS.map(field => (
              <div key={field.key} className="space-y-2">
                <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest">{field.label}</label>
                <input type="number" step="0.1" value={(newEntry as any)[field.key] ?? ''}
                  onChange={e => setNewEntry({ ...newEntry, [field.key]: e.target.value ? Number(e.target.value) : undefined })}
                  className="w-full bg-slate-950 border border-white/10 rounded-xl px-4 py-3 text-xs text-white" placeholder="--" />
              </div>
            ))}
          </div>
          <div className="flex space-x-3 pt-2">
            <button onClick={handleAdd}
              className="px-6 py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-xl font-black text-[10px] uppercase tracking-widest transition">
              Save Entry
            </button>
            <button onClick={() => setShowForm(false)}
              className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded-xl font-black text-[10px] uppercase tracking-widest transition">
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {MEASUREMENT_FIELDS.slice(0, 4).map(field => {
          const val = latest ? (latest as any)[field.key] : null;
          return (
            <button key={field.key} onClick={() => setSelectedMetric(field.key)}
              className={`p-5 rounded-2xl border text-left transition-all card-hover ${selectedMetric === field.key ? 'bg-cyan-500/10 border-cyan-500/30' : 'bg-slate-900 border-white/5'}`}>
              <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">{field.label}</p>
              <p className="text-2xl font-black text-white mt-1">{val != null ? val : '--'}</p>
              {change !== null && selectedMetric === field.key && (
                <p className={`text-[10px] font-black mt-1 ${change > 0 ? 'text-rose-400' : change < 0 ? 'text-emerald-400' : 'text-slate-500'}`}>
                  {change > 0 ? '+' : ''}{change.toFixed(1)}
                </p>
              )}
            </button>
          );
        })}
      </div>

      <div className="glass-panel p-8 rounded-[2.5rem] border border-white/5">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <TrendingUp size={18} className="text-cyan-400" />
            <h3 className="text-lg font-black text-white italic tracking-tighter uppercase">{selectedField?.label || 'Trend'}</h3>
          </div>
          <div className="flex space-x-2">
            {MEASUREMENT_FIELDS.slice(4).map(field => (
              <button key={field.key} onClick={() => setSelectedMetric(field.key)}
                className={`px-3 py-1.5 rounded-lg text-[8px] font-black uppercase tracking-widest transition ${selectedMetric === field.key ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'bg-slate-800 text-slate-500 hover:text-slate-300'}`}>
                {field.label.split(' ')[0]}
              </button>
            ))}
          </div>
        </div>
        {chartData.length > 1 ? (
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '12px' }}
                labelStyle={{ color: '#94a3b8', fontSize: '10px' }}
              />
              <Line type="monotone" dataKey="value" stroke={selectedField?.color || '#06b6d4'} strokeWidth={2.5}
                dot={{ fill: selectedField?.color || '#06b6d4', r: 4 }}
                activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="py-12 text-center text-slate-500">
            <Activity size={32} className="mx-auto mb-3 text-slate-700" />
            <p className="text-sm">Log at least 2 measurements to see a trend</p>
          </div>
        )}
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-black text-slate-500 uppercase tracking-widest">History ({entries.length})</h3>
        {entries.slice().reverse().map((entry, i) => {
          const idx = entries.length - 1 - i;
          const hasAny = MEASUREMENT_FIELDS.some(f => (entry as any)[f.key] != null);
          if (!hasAny) return null;
          return (
            <div key={entry.date} className="glass-panel p-5 rounded-2xl border border-white/5 card-hover flex items-center justify-between group">
              <div>
                <p className="text-sm font-black text-white">{new Date(entry.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })}</p>
                <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2">
                  {MEASUREMENT_FIELDS.filter(f => (entry as any)[f.key] != null).map(f => (
                    <span key={f.key} className="text-[10px] text-slate-400">
                      {f.label.split(' ')[0]}: <span className="font-black text-white">{(entry as any)[f.key]}</span>
                    </span>
                  ))}
                </div>
              </div>
              <button onClick={() => handleDelete(idx)}
                className={`p-2 rounded-lg transition ${deleteConfirm === idx ? 'bg-rose-500/20 text-rose-400' : 'opacity-0 group-hover:opacity-100 text-slate-500 hover:text-rose-400'}`}>
                {deleteConfirm === idx ? <Check size={14} /> : <Trash2 size={14} />}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default BodyMeasurements;
