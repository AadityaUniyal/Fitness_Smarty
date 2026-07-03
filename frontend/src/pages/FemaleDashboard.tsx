import React, { useState, useEffect } from 'react';
import { Moon, Sun, Activity, Droplets, Brain, Heart, Sparkles, ChevronRight, Apple, Dumbbell } from 'lucide-react';
import SmartNextMove from '../components/SmartNextMove';
import DailyChecklist from '../components/DailyChecklist';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const USER_ID = 1;

const MOODS = ['Amazing', 'Good', 'Neutral', 'Tired', 'Crampy'];
const FLOWS = ['Light', 'Medium', 'Heavy'];
const PHASES = [
  { value: 'menstrual', label: 'Menstrual', icon: <Droplets size={16} />, color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' },
  { value: 'follicular', label: 'Follicular', icon: <Sun size={16} />, color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' },
  { value: 'ovulatory', label: 'Ovulatory', icon: <Sparkles size={16} />, color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/20' },
  { value: 'luteal', label: 'Luteal', icon: <Moon size={16} />, color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
];

const THEME = {
  primary: 'pink',
  gradient: 'from-pink-500 to-purple-500',
  lightBg: 'bg-pink-500/5',
  border: 'border-pink-500/20',
  text: 'text-pink-400',
  accent: 'pink',
};

export default function FemaleDashboard() {
  const [phaseData, setPhaseData] = useState<any>(null);
  const [showLogForm, setShowLogForm] = useState(false);
  const [logPhase, setLogPhase] = useState('follicular');
  const [logEnergy, setLogEnergy] = useState(3);
  const [logMood, setLogMood] = useState('Neutral');
  const [logFlow, setLogFlow] = useState('Light');

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${API}/api/female/cycle-phase/${USER_ID}`);
        if (r.ok) setPhaseData(await r.json());
      } catch {}
    })();
  }, []);

  const logSymptom = async () => {
    try {
      await fetch(`${API}/api/female/log-symptom/${USER_ID}?phase=${logPhase}&energy_level=${logEnergy}&mood=${logMood}&flow_intensity=${logFlow}`, { method: 'POST' });
    } catch {}
    setShowLogForm(false);
    try {
      const r = await fetch(`${API}/api/female/cycle-phase/${USER_ID}`);
      if (r.ok) setPhaseData(await r.json());
    } catch {}
  };

  const phase = phaseData?.phase || 'unknown';
  const phaseMeta = PHASES.find(p => p.value === phase) || PHASES[0];
  const energyBars = Array.from({ length: 5 }, (_, i) => i + 1);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-pink-950/10 to-gray-950">
      {/* Pink gradient accent line */}
      <div className="h-1 bg-gradient-to-r from-pink-500 via-purple-500 to-pink-500" />

      <div className="max-w-6xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-500 to-purple-500 flex items-center justify-center">
              <Heart size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Femme Dashboard</h1>
              <p className="text-xs text-gray-400">Cycle-synced fitness & nutrition</p>
            </div>
          </div>
          <button onClick={() => setShowLogForm(!showLogForm)}
            className="bg-gradient-to-r from-pink-500 to-purple-500 text-white text-sm px-4 py-2 rounded-xl hover:opacity-90 transition flex items-center gap-2">
            <Heart size={14} /> Log Today
          </button>
        </div>

        {/* Cycle Phase Card */}
        <div className={`bg-gray-900/80 border ${phaseMeta.bg || THEME.border} rounded-2xl p-6`}>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-12 h-12 rounded-xl ${phaseMeta.bg || 'bg-gray-800'} flex items-center justify-center`}>
                {phaseMeta.icon}
              </div>
              <div>
                <div className={`text-lg font-bold capitalize ${phaseMeta.color || 'text-gray-200'}`}>{phase} Phase</div>
                <div className="text-xs text-gray-400 mt-0.5">Day {phaseData?.cycle_day || '--'} of cycle</div>
              </div>
            </div>
            {phaseData?.energy_tip && (
              <div className="hidden md:flex items-start gap-2 max-w-xs bg-gray-800/60 rounded-lg p-3">
                <Brain size={14} className="text-pink-400 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-gray-300">{phaseData.energy_tip}</p>
              </div>
            )}
          </div>
        </div>

        {/* Symptom Log Form */}
        {showLogForm && (
          <div className="bg-gray-900/90 border border-pink-500/30 rounded-2xl p-6 space-y-4 animate-fadeIn">
            <h3 className="text-sm font-semibold text-pink-300 flex items-center gap-2"><Heart size={14} /> Log Cycle Symptoms</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Phase</label>
                <select value={logPhase} onChange={e => setLogPhase(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white">
                  {PHASES.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Energy (1-5)</label>
                <div className="flex gap-1">
                  {energyBars.map(n => (
                    <button key={n} onClick={() => setLogEnergy(n)}
                      className={`w-8 h-8 rounded-lg text-xs font-bold transition ${n <= logEnergy ? 'bg-pink-500 text-white' : 'bg-gray-800 text-gray-500 border border-gray-700'}`}>{n}</button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Mood</label>
                <select value={logMood} onChange={e => setLogMood(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white">
                  {MOODS.map(m => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Flow</label>
                <select value={logFlow} onChange={e => setLogFlow(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white">
                  {FLOWS.map(f => <option key={f} value={f}>{f}</option>)}
                </select>
              </div>
            </div>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setShowLogForm(false)} className="text-xs text-gray-400 px-4 py-2">Cancel</button>
              <button onClick={logSymptom} className="bg-gradient-to-r from-pink-500 to-purple-500 text-white text-xs px-6 py-2 rounded-lg hover:opacity-90 transition">Save</button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Smart Next Move + Checklist */}
          <div className="lg:col-span-2 space-y-6">
            <SmartNextMove userId={USER_ID} />
            <DailyChecklist userId={USER_ID} />

            {/* Cycle-Synced Workout Suggestions */}
            <div className="bg-gray-900/80 border border-purple-500/20 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <Dumbbell size={18} className="text-purple-400" />
                <h3 className="text-sm font-semibold text-white">Cycle-Synced Exercises</h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {(phaseData?.exercises || []).slice(0, 4).map((ex: any, i: number) => (
                  <div key={i} className="bg-gray-800/60 border border-gray-700/50 rounded-lg p-3">
                    <div className="text-sm font-medium text-gray-200">{ex.name}</div>
                    <div className="text-xs text-gray-400 mt-0.5">{ex.targeted_muscle}</div>
                    <div className="flex items-center gap-2 mt-2 text-[10px] text-gray-500">
                      <span className={`px-1.5 py-0.5 rounded ${ex.difficulty === 'Beginner' ? 'bg-green-500/10 text-green-400' : 'bg-yellow-500/10 text-yellow-400'}`}>{ex.difficulty}</span>
                      <span>{ex.equipment}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right: Cycle Info + Nutrition */}
          <div className="space-y-6">
            {/* Cycle Information */}
            <div className="bg-gray-900/80 border border-pink-500/20 rounded-xl p-5">
              <h3 className="text-sm font-semibold text-pink-300 flex items-center gap-2 mb-3"><Activity size={14} /> Today's Recommendation</h3>
              <div className="bg-gray-800/60 rounded-lg p-4 mb-3">
                <div className="text-sm font-medium text-gray-200">{phaseData?.recommended_workout || 'General full-body workout'}</div>
              </div>
              <h4 className="text-xs font-medium text-gray-300 mb-2">Recommended Foods</h4>
              <div className="space-y-2">
                {(phaseData?.recommended_foods || []).map((food: string, i: number) => (
                  <div key={i} className="flex items-center gap-2 text-xs text-gray-400">
                    <Apple size={12} className="text-pink-400 flex-shrink-0" /> {food}
                  </div>
                ))}
              </div>
            </div>

            {/* Energy Level */}
            <div className="bg-gray-900/80 border border-gray-700/50 rounded-xl p-5">
              <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2 mb-3"><Sun size={14} className="text-yellow-400" /> Cycle Phases</h3>
              <div className="space-y-2">
                {PHASES.map(p => (
                  <div key={p.value} className={`flex items-center gap-2 p-2 rounded-lg text-xs ${p.value === phase ? p.bg : ''}`}>
                    {p.icon}
                    <span className={`${p.value === phase ? p.color : 'text-gray-400'} capitalize`}>{p.label}</span>
                    {p.value === phase && <span className="text-[10px] text-gray-500 ml-auto">Current</span>}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
