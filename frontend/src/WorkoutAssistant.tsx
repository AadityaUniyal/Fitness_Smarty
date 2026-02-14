import React, { useState } from 'react';
import { 
  Dumbbell, 
  Sparkles, 
  Loader2, 
  PlayCircle, 
  CheckCircle2, 
  Cpu, 
  Database,
  Timer,
  BarChart3,
  Flame,
  Zap,
  Target,
  Trophy,
  Wrench,
  ChevronDown,
  ChevronUp,
  ClipboardList,
  Video,
  Info,
  ExternalLink,
  ShieldCheck,
  Cloud
} from 'lucide-react';
import { useUser } from '@clerk/clerk-react';
import { generateWorkoutPlan } from './geminiService';
import { WorkoutPlan, BodyGoal } from './types';

const WorkoutAssistant: React.FC = () => {
  const { user } = useUser();
  const [goal, setGoal] = useState<BodyGoal>(BodyGoal.ATHLETIC);
  const [level, setLevel] = useState('Intermediate');
  const [duration, setDuration] = useState(45);
  const [plan, setPlan] = useState<WorkoutPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [synced, setSynced] = useState(false);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  const handleGenerate = async () => {
    setLoading(true);
    setSynced(false);
    setExpandedIdx(null);
    try {
      const data = await generateWorkoutPlan(goal, level, duration);
      setPlan(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSyncToCore = async () => {
    if (!plan) return;
    setSyncing(true);
    try {
      // Store workout plan locally for now
      // Backend workout logging endpoint would be implemented in future tasks
      localStorage.setItem('last_workout', JSON.stringify({
        plan,
        userId: user?.id || 'guest-user',
        timestamp: new Date().toISOString()
      }));
      setSynced(true);
    } catch (error) {
      console.error("Sync Failure:", error);
    } finally {
      setSyncing(false);
    }
  };

  const toggleExpand = (idx: number) => {
    setExpandedIdx(expandedIdx === idx ? null : idx);
  };

  return (
    <div className="max-w-7xl mx-auto space-y-10 animate-in slide-in-from-bottom-6 duration-700">
      {/* Configuration HUD */}
      <div className="glass-panel p-10 rounded-[3.5rem] border border-emerald-500/20 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-[100px] -mr-32 -mt-32"></div>
        
        <div className="flex flex-col lg:grid lg:grid-cols-12 gap-12 items-start">
          <div className="lg:col-span-8 space-y-8 w-full">
            <div className="flex items-center space-x-4">
              <div className="p-4 bg-emerald-500 text-slate-950 rounded-3xl shadow-[0_0_20px_rgba(16,185,129,0.3)]">
                <Cpu size={32} />
              </div>
              <div>
                <h2 className="text-4xl font-black italic tracking-tighter text-white uppercase">NEURAL PLANNER</h2>
                <p className="text-[10px] font-black uppercase tracking-[0.4em] text-emerald-500">Generating Optimized Training Nodes</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-3">
                <label className="flex items-center text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">
                  <BarChart3 size={14} className="mr-2" /> Objective
                </label>
                <select 
                  value={goal}
                  onChange={(e) => setGoal(e.target.value as BodyGoal)}
                  className="w-full bg-slate-950 border border-white/10 rounded-2xl px-6 py-4 text-xs font-black tracking-widest focus:ring-4 focus:ring-emerald-500/10 outline-none transition-all text-emerald-400 uppercase"
                >
                  {Object.values(BodyGoal).map((g) => (
                    <option key={g} value={g}>{g}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-3">
                <label className="flex items-center text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">
                  <Zap size={14} className="mr-2" /> Proficiency
                </label>
                <select 
                  value={level}
                  onChange={(e) => setLevel(e.target.value)}
                  className="w-full bg-slate-950 border border-white/10 rounded-2xl px-6 py-4 text-xs font-black tracking-widest focus:ring-4 focus:ring-emerald-500/10 outline-none transition-all text-emerald-400 uppercase"
                >
                  <option>Beginner</option>
                  <option>Intermediate</option>
                  <option>Advanced</option>
                  <option>Elite Operator</option>
                </select>
              </div>

              <div className="space-y-3">
                <label className="flex items-center text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">
                  <Timer size={14} className="mr-2" /> Sync Time
                </label>
                <div className="relative">
                  <input 
                    type="number" 
                    value={duration}
                    onChange={(e) => setDuration(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-white/10 rounded-2xl px-6 py-4 text-xs font-black tracking-widest focus:ring-4 focus:ring-emerald-500/10 outline-none transition-all text-emerald-400 uppercase"
                  />
                  <div className="absolute right-6 top-1/2 -translate-y-1/2 text-[10px] font-black text-slate-700 uppercase">MIN</div>
                </div>
              </div>
            </div>

            <button 
              onClick={handleGenerate}
              disabled={loading}
              className="w-full bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-800 text-slate-950 font-black py-6 rounded-[2rem] transition-all flex items-center justify-center space-x-4 shadow-[0_15px_40px_rgba(16,185,129,0.2)] group active:scale-[0.98]"
            >
              {loading ? (
                <Loader2 className="animate-spin" size={24} />
              ) : (
                <Sparkles size={24} className="group-hover:rotate-12 transition-transform" />
              )}
              <span className="uppercase tracking-[0.2em] text-sm italic">Initialize Protocol Sync</span>
            </button>
          </div>

          <div className="lg:col-span-4 hidden lg:flex flex-col items-center justify-center space-y-4">
            <div className="w-64 h-64 relative group">
              <div className="absolute -inset-2 bg-gradient-to-br from-emerald-500 to-cyan-500 rounded-[3rem] blur-2xl opacity-20 group-hover:opacity-40 transition-opacity duration-700"></div>
              <img 
                src={`https://api.dicebear.com/7.x/identicon/svg?seed=${goal}`} 
                className="relative w-full h-full bg-slate-950 rounded-[3rem] border border-white/10 p-8 grayscale group-hover:grayscale-0 transition-all duration-700" 
                alt="Neural Profile" 
              />
            </div>
            <p className="text-[10px] font-black text-slate-600 uppercase tracking-[0.3em]">Adaptive Neural Identity</p>
          </div>
        </div>
      </div>

      {/* Generated Protocol Display */}
      {plan && (
        <div className="space-y-8 animate-in fade-in zoom-in-95 duration-1000">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 px-4">
            <div className="flex items-center space-x-6">
              <div className="w-16 h-16 bg-slate-900 border border-white/10 rounded-2xl flex items-center justify-center text-emerald-500 shadow-xl">
                <ClipboardList size={32} />
              </div>
              <div>
                <div className="flex items-center space-x-3 mb-1">
                  <span className="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 text-[8px] font-black uppercase tracking-widest rounded border border-emerald-500/20">
                    {plan.intensity} Intensity
                  </span>
                  <span className="px-2 py-0.5 bg-cyan-500/10 text-cyan-400 text-[8px] font-black uppercase tracking-widest rounded border border-cyan-500/20">
                    {plan.duration}
                  </span>
                  {synced && (
                    <span className="px-2 py-0.5 bg-emerald-500 text-slate-950 text-[8px] font-black uppercase tracking-widest rounded border border-emerald-400 flex items-center animate-in zoom-in duration-300">
                      <Cloud size={10} className="mr-1" /> Core Integrity Verified
                    </span>
                  )}
                </div>
                <h3 className="text-4xl font-black italic text-white tracking-tighter uppercase leading-none">{plan.title}</h3>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <button 
                onClick={handleSyncToCore}
                disabled={syncing || synced}
                className={`px-8 py-4 rounded-2xl flex items-center space-x-3 transition-all font-black text-[10px] uppercase tracking-widest border group shadow-lg relative overflow-hidden ${
                  synced 
                    ? 'bg-emerald-500 border-emerald-400 text-slate-950 shadow-[0_0_30px_rgba(16,185,129,0.6)] animate-success-glow' 
                    : 'bg-white/5 border-white/10 text-slate-300 hover:bg-emerald-500/10 hover:border-emerald-500/30 hover:text-emerald-400'
                }`}
              >
                {syncing ? (
                  <Loader2 className="animate-spin" size={16} />
                ) : synced ? (
                  <div className="flex items-center animate-in zoom-in spin-in-12 duration-500">
                    <CheckCircle2 size={16} className="mr-2" />
                  </div>
                ) : (
                  <Database size={16} className="group-hover:animate-pulse" />
                )}
                <span>{syncing ? 'Synchronizing...' : synced ? 'Neural Sync Complete' : 'Sync to Neural Core'}</span>
                
                {synced && (
                  <div className="absolute inset-0 bg-emerald-500/10 animate-pulse pointer-events-none"></div>
                )}
              </button>
              
              <button className="bg-emerald-500 text-slate-950 px-8 py-4 rounded-2xl font-black text-[10px] uppercase tracking-widest shadow-xl shadow-emerald-500/10 flex items-center space-x-3 hover:bg-emerald-400 transition-colors">
                <PlayCircle size={18} />
                <span>Execute Session</span>
              </button>
            </div>
          </div>

          {/* COLUMNAR EXERCISE LIST */}
          <div className="glass-panel rounded-[3rem] border border-white/5 overflow-hidden">
            <div className="hidden md:grid grid-cols-12 gap-4 px-10 py-6 border-b border-white/10 bg-slate-900/50">
              <div className="col-span-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Training Node / Desc</div>
              <div className="col-span-2 text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center"><Target size={12} className="mr-2" /> Target</div>
              <div className="col-span-2 text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center"><Trophy size={12} className="mr-2" /> Complexity</div>
              <div className="col-span-2 text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center"><Wrench size={12} className="mr-2" /> Assets</div>
              <div className="col-span-2 text-[10px] font-black text-slate-500 uppercase tracking-widest text-right">Volume</div>
            </div>

            <div className="divide-y divide-white/5">
              {plan.exercises.map((ex, idx) => (
                <div key={idx}>
                  <div 
                    onClick={() => toggleExpand(idx)}
                    className={`group hover:bg-emerald-500/[0.04] transition-all cursor-pointer p-8 md:p-10 ${expandedIdx === idx ? 'bg-emerald-500/[0.06]' : ''}`}
                  >
                    <div className="grid grid-cols-1 md:grid-cols-12 gap-6 md:gap-4 items-start">
                      {/* Node Name & Description */}
                      <div className="md:col-span-4 space-y-2">
                        <div className="flex items-center space-x-3">
                          <span className="text-xl font-black text-slate-700 italic group-hover:text-emerald-500/50 transition-colors">{String(idx + 1).padStart(2, '0')}</span>
                          <h4 className="text-lg font-black text-white italic tracking-tight group-hover:text-emerald-400 transition-colors uppercase flex items-center">
                            {ex.name}
                            <span className="ml-2 opacity-0 group-hover:opacity-100 transition-opacity">
                              {expandedIdx === idx ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                            </span>
                          </h4>
                        </div>
                        <p className="text-xs text-slate-500 leading-relaxed font-medium line-clamp-1 pr-4">
                          {ex.description}
                        </p>
                      </div>

                      {/* Targeted Muscle (Column 2) */}
                      <div className="md:col-span-2 flex flex-col justify-center h-full">
                        <div className="md:hidden text-[8px] font-black text-slate-600 uppercase tracking-widest mb-1">Target Muscle</div>
                        <div className="flex items-center text-[10px] font-black text-cyan-400 uppercase italic tracking-tight bg-cyan-500/5 px-3 py-2 rounded-xl border border-cyan-500/10 w-fit md:w-full">
                          <Target size={14} className="mr-2 shrink-0" />
                          <span className="truncate">{ex.targeted_muscle}</span>
                        </div>
                      </div>

                      {/* Difficulty (Column 3) */}
                      <div className="md:col-span-2 flex flex-col justify-center h-full">
                        <div className="md:hidden text-[8px] font-black text-slate-600 uppercase tracking-widest mb-1">Complexity</div>
                        <div className="flex items-center text-[10px] font-black text-orange-400 uppercase italic tracking-tight bg-orange-500/5 px-3 py-2 rounded-xl border border-orange-500/10 w-fit md:w-full">
                          <Trophy size={14} className="mr-2 shrink-0" />
                          <span className="truncate">{ex.difficulty}</span>
                        </div>
                      </div>

                      {/* Equipment (Column 4) */}
                      <div className="md:col-span-2 flex flex-col justify-center h-full">
                        <div className="md:hidden text-[8px] font-black text-slate-600 uppercase tracking-widest mb-1">Equipment Assets</div>
                        <div className="flex items-center text-[10px] font-black text-purple-400 uppercase italic tracking-tight bg-purple-500/5 px-3 py-2 rounded-xl border border-purple-500/10 w-fit md:w-full">
                          <Wrench size={14} className="mr-2 shrink-0" />
                          <span className="truncate">{ex.equipment}</span>
                        </div>
                      </div>

                      {/* Volume: Sets/Reps (Column 5) */}
                      <div className="md:col-span-2 flex flex-col items-end justify-center h-full">
                        <div className="md:hidden text-[8px] font-black text-slate-600 uppercase tracking-widest mb-1">Session Volume</div>
                        <div className="text-right">
                            <p className="text-xl font-black text-white italic tracking-tighter leading-none">{ex.reps}</p>
                            <p className="text-[9px] font-black text-slate-600 uppercase tracking-widest mt-1">
                              {ex.sets} SETS <span className="mx-1">•</span> SYNCHRONIZED
                            </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* EXPANDABLE DETAIL SECTION */}
                  {expandedIdx === idx && (
                    <div className="bg-emerald-500/[0.03] border-t border-emerald-500/10 animate-in slide-in-from-top-4 duration-500 overflow-hidden">
                      <div className="p-8 md:p-12 grid grid-cols-1 lg:grid-cols-12 gap-10">
                        <div className="lg:col-span-7 space-y-6">
                           <div className="flex items-center space-x-3 text-emerald-400">
                             <Info size={16} />
                             <span className="text-[10px] font-black uppercase tracking-[0.2em]">Full Bio-mechanical Description</span>
                           </div>
                           <p className="text-sm text-slate-300 leading-relaxed italic">
                             {ex.description}
                           </p>
                           <div className="p-6 rounded-2xl bg-slate-950/50 border border-emerald-500/10 space-y-3">
                              <h5 className="text-[9px] font-black text-emerald-500 uppercase tracking-widest">Neural Cues for Form</h5>
                              <ul className="text-xs text-slate-400 space-y-2 font-medium">
                                <li className="flex items-start"><Sparkles size={12} className="mr-2 mt-0.5 text-emerald-400 shrink-0" /> Maintain constant core tension to stabilize the {ex.targeted_muscle} complex.</li>
                                <li className="flex items-start"><Sparkles size={12} className="mr-2 mt-0.5 text-emerald-400 shrink-0" /> Optimize force distribution through the mid-foot throughout the entire kinetic chain.</li>
                              </ul>
                           </div>
                        </div>

                        <div className="lg:col-span-5 flex flex-col justify-center space-y-6">
                           <div className="aspect-video bg-slate-950 rounded-[2rem] border border-white/5 flex flex-col items-center justify-center relative group overflow-hidden">
                              <div className="absolute inset-0 bg-emerald-500/5 group-hover:bg-emerald-500/10 transition-colors"></div>
                              <Video size={48} className="text-slate-800 mb-4 group-hover:scale-110 transition-transform duration-500" />
                              <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest">Visual Stream Pending</p>
                              
                              <a 
                                href={ex.video_url || `https://www.youtube.com/results?search_query=${encodeURIComponent(ex.name + ' exercise')}`} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="mt-4 px-6 py-3 bg-cyan-500 text-slate-950 rounded-xl font-black text-[10px] uppercase tracking-widest flex items-center space-x-2 hover:bg-cyan-400 transition-all shadow-[0_10px_20px_rgba(6,182,212,0.3)] z-10"
                              >
                                <span>Launch Visual Link</span>
                                <ExternalLink size={14} />
                              </a>
                           </div>
                           
                           <button className="w-full flex items-center justify-center space-x-3 py-4 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 rounded-2xl transition-all font-black text-[10px] uppercase tracking-widest">
                             <CheckCircle2 size={16} />
                             <span>Mark Node Optimized</span>
                           </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
          
          <div className="flex justify-center pt-8">
            <div className="flex items-center space-x-4 text-slate-600 bg-slate-950/50 px-8 py-4 rounded-3xl border border-white/5">
               <div className="flex -space-x-2">
                  {[1,2,3].map(i => (
                    <div key={i} className="w-6 h-6 rounded-full border border-slate-900 bg-emerald-500/20 flex items-center justify-center">
                      <Zap size={10} className="text-emerald-500" />
                    </div>
                  ))}
               </div>
               <div className="w-px h-6 bg-white/10 mx-2"></div>
               <span className="text-[10px] font-black uppercase tracking-[0.2em] italic">
                 Metabolic Trajectory: ~{Number(plan.duration.split(' ')[0]) * 9} KCAL
               </span>
               <div className="w-px h-6 bg-white/10 mx-2"></div>
               <div className="flex items-center space-x-2 text-cyan-400">
                  <Flame size={14} className="animate-pulse" />
                  <span className="text-[9px] font-black uppercase">Fat Oxidation Optimized</span>
               </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkoutAssistant;