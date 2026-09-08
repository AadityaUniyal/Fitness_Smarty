import React, { useState, useEffect } from 'react';
import { Moon, Sun, Activity, Droplets, Brain, Heart, Sparkles, ChevronRight, Apple, Dumbbell } from 'lucide-react';
import SmartNextMove from '../components/SmartNextMove';
import DailyChecklist from '../components/DailyChecklist';
import { useCurrentUserId } from '../hooks/useCurrentUserId';
import { use3DTilt } from '../hooks/use3DTilt';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const MOODS = ['Amazing', 'Good', 'Neutral', 'Tired', 'Crampy'];
const FLOWS = ['Light', 'Medium', 'Heavy'];
const PHASES = [
  { value: 'menstrual', label: 'Menstrual', icon: <Droplets size={16} />, color: 'text-rose-400', bg: 'bg-rose-500/10 border-rose-500/20' },
  { value: 'follicular', label: 'Follicular', icon: <Sun size={16} />, color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/20' },
  { value: 'ovulatory', label: 'Ovulatory', icon: <Sparkles size={16} />, color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/20' },
  { value: 'luteal', label: 'Luteal', icon: <Moon size={16} />, color: 'text-cyan-400', bg: 'bg-cyan-500/10 border-cyan-500/20' },
];

export default function FemaleDashboard() {
  const userId = useCurrentUserId();
  const [phaseData, setPhaseData] = useState<any>(null);
  const [showLogForm, setShowLogForm] = useState(false);
  const [logPhase, setLogPhase] = useState('follicular');
  const [logEnergy, setLogEnergy] = useState(3);
  const [logMood, setLogMood] = useState('Neutral');
  const [logFlow, setLogFlow] = useState('Light');

  const mainCardTilt = use3DTilt<HTMLDivElement>({ maxTilt: 6 });

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${API}/api/female/cycle-phase/${userId}`);
        if (r.ok) setPhaseData(await r.json());
      } catch {}
    })();
  }, [userId]);

  const handleLogSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await fetch(`${API}/api/female/log-cycle-entry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: Number(userId),
          phase: logPhase,
          energy_level: logEnergy,
          mood: logMood,
          flow_intensity: logFlow,
        }),
      });
      setShowLogForm(false);
      const r = await fetch(`${API}/api/female/cycle-phase/${userId}`);
      if (r.ok) setPhaseData(await r.json());
    } catch {}
  };

  const phase = phaseData?.phase || 'follicular';
  const phaseInfo = PHASES.find(p => p.value === phase) || PHASES[1];

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header Banner */}
      <div 
        ref={mainCardTilt.ref as any}
        style={mainCardTilt.style}
        onMouseMove={mainCardTilt.onMouseMove as any}
        onMouseLeave={mainCardTilt.onMouseLeave as any}
        className="glass-panel p-8 rounded-[2.5rem] border border-pink-500/20 bg-gradient-to-r from-pink-950/20 via-slate-950 to-purple-950/20 relative overflow-hidden card-3d"
      >
        <div className="card-3d-shine" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-pink-500/10 border border-pink-500/20 rounded-full text-[10px] font-black uppercase tracking-widest text-pink-400">
              <Heart size={12} /> FemmeCare Health Hub
            </div>
            <h1 className="text-3xl md:text-5xl font-black italic tracking-tighter text-white uppercase">
              Cycle <span className="text-pink-400">Phase Sync</span>
            </h1>
            <p className="text-sm text-slate-300 max-w-xl">
              Hormone-aligned workout and nutritional recommendations tuned to your current cycle day.
            </p>
          </div>
          <button
            onClick={() => setShowLogForm(!showLogForm)}
            className="px-6 py-3.5 bg-pink-500 hover:bg-pink-400 text-slate-950 rounded-2xl font-black text-xs uppercase tracking-widest transition shadow-lg shadow-pink-500/20 active:scale-95 shrink-0"
          >
            {showLogForm ? 'Close Form' : 'Log Daily Entry'}
          </button>
        </div>

        {/* Phase Card */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8 pt-6 border-t border-white/5">
          <div className="bg-slate-900/80 border border-white/10 rounded-2xl p-4">
            <span className="text-[9px] font-black uppercase tracking-widest text-slate-400 block">Current Phase</span>
            <div className="flex items-center gap-2 mt-1">
              {phaseInfo.icon}
              <span className={`text-base font-black capitalize ${phaseInfo.color}`}>{phaseInfo.label}</span>
            </div>
          </div>
          <div className="bg-slate-900/80 border border-white/10 rounded-2xl p-4">
            <span className="text-[9px] font-black uppercase tracking-widest text-slate-400 block">Cycle Day</span>
            <span className="text-base font-black text-white italic mt-1 block">Day {phaseData?.cycle_day || 14}</span>
          </div>
          <div className="bg-slate-900/80 border border-white/10 rounded-2xl p-4">
            <span className="text-[9px] font-black uppercase tracking-widest text-slate-400 block">Hormonal Focus</span>
            <span className="text-base font-black text-pink-300 italic mt-1 block">{phaseData?.energy_tip || 'Balanced Recovery'}</span>
          </div>
        </div>
      </div>

      {/* Log Entry Form */}
      {showLogForm && (
        <form onSubmit={handleLogSubmit} className="glass-panel p-8 rounded-[2.5rem] border border-pink-500/20 space-y-6">
          <h3 className="text-xl font-black italic uppercase text-white">Log Cycle Status</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 block">Phase</label>
              <select value={logPhase} onChange={e => setLogPhase(e.target.value)} className="w-full bg-slate-900 border border-white/10 rounded-xl p-3 text-xs font-bold text-white">
                {PHASES.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
              </select>
            </div>
            <div>
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 block">Energy (1-5)</label>
              <input type="number" min="1" max="5" value={logEnergy} onChange={e => setLogEnergy(Number(e.target.value))} className="w-full bg-slate-900 border border-white/10 rounded-xl p-3 text-xs font-bold text-white" />
            </div>
            <div>
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 block">Mood</label>
              <select value={logMood} onChange={e => setLogMood(e.target.value)} className="w-full bg-slate-900 border border-white/10 rounded-xl p-3 text-xs font-bold text-white">
                {MOODS.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
            <div>
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 block">Flow</label>
              <select value={logFlow} onChange={e => setLogFlow(e.target.value)} className="w-full bg-slate-900 border border-white/10 rounded-xl p-3 text-xs font-bold text-white">
                {FLOWS.map(f => <option key={f} value={f}>{f}</option>)}
              </select>
            </div>
          </div>
          <button type="submit" className="px-8 py-3 bg-pink-500 hover:bg-pink-400 text-slate-950 rounded-xl font-black text-xs uppercase tracking-widest transition">
            Save Log Entry
          </button>
        </form>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          <SmartNextMove userId={Number(userId)} genderMode="femmecare" />
          <DailyChecklist userId={Number(userId)} />

          {/* Synced Exercises */}
          <div className="glass-panel p-6 rounded-[2.5rem] border border-purple-500/20">
            <div className="flex items-center gap-2 mb-4">
              <Dumbbell size={18} className="text-purple-400" />
              <h3 className="text-sm font-black italic uppercase text-white">Cycle-Synced Exercises</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {(phaseData?.exercises || []).slice(0, 4).map((ex: any, i: number) => (
                <div key={i} className="bg-slate-900/80 border border-white/10 rounded-2xl p-4">
                  <div className="text-sm font-bold text-slate-100">{ex.name}</div>
                  <div className="text-xs text-slate-400 mt-0.5">{ex.targeted_muscle}</div>
                  <div className="flex items-center gap-2 mt-2 text-[10px] text-slate-400">
                    <span className={`px-2 py-0.5 rounded ${ex.difficulty === 'Beginner' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>{ex.difficulty}</span>
                    <span>{ex.equipment}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="space-y-6">
          <div className="glass-panel p-6 rounded-[2.5rem] border border-pink-500/20">
            <h3 className="text-sm font-black uppercase text-pink-300 flex items-center gap-2 mb-3">
              <Activity size={14} /> Today's Recommendation
            </h3>
            <div className="bg-slate-900/80 rounded-2xl p-4 mb-4 border border-white/5">
              <div className="text-xs font-bold text-slate-200">{phaseData?.recommended_workout || 'General full-body workout'}</div>
            </div>
            <h4 className="text-xs font-black uppercase tracking-wider text-slate-400 mb-2">Recommended Foods</h4>
            <div className="space-y-2">
              {(phaseData?.recommended_foods || []).map((food: string, i: number) => (
                <div key={i} className="flex items-center gap-2 text-xs text-slate-300 bg-white/5 p-2 rounded-xl border border-white/5">
                  <Apple size={14} className="text-pink-400 flex-shrink-0" /> {food}
                </div>
              ))}
            </div>
          </div>

          <div className="glass-panel p-6 rounded-[2.5rem] border border-white/10">
            <h3 className="text-sm font-black uppercase text-slate-300 flex items-center gap-2 mb-3">
              <Sun size={14} className="text-amber-400" /> Cycle Phases
            </h3>
            <div className="space-y-2">
              {PHASES.map(p => (
                <div key={p.value} className={`flex items-center gap-2 p-3 rounded-xl text-xs font-bold ${p.value === phase ? p.bg : 'bg-slate-900/50'}`}>
                  {p.icon}
                  <span className={`${p.value === phase ? p.color : 'text-slate-400'} capitalize`}>{p.label}</span>
                  {p.value === phase && <span className="text-[9px] font-black uppercase tracking-widest text-slate-400 ml-auto">Current</span>}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
