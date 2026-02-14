
import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Flame, 
  Footprints, 
  Clock, 
  TrendingUp,
  Zap,
  Target,
  BrainCircuit,
  ShieldCheck,
  Cpu,
  CheckCircle2,
  Circle,
  AlertTriangle,
  Fingerprint,
  Heart
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer
} from 'recharts';
import { fetchUserStats, fetchRecoveryScore, fetchNeuralIntegrity } from './api';
import { generateDailyTasks } from './geminiService';
import { UserStats, DailyTask, BioProfile } from './types';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<UserStats | null>(null);
  const [tasks, setTasks] = useState<DailyTask[]>([]);
  const [recovery, setRecovery] = useState<any>(null);
  const [integrity, setIntegrity] = useState<any>(null);
  const [loadingTasks, setLoadingTasks] = useState(false);

  useEffect(() => {
    fetchUserStats('user-1').then(setStats);
    fetchRecoveryScore().then(setRecovery);
    fetchNeuralIntegrity().then(setIntegrity);
    
    const savedProfile = localStorage.getItem('bio_profile');
    if (savedProfile) {
      setLoadingTasks(true);
      generateDailyTasks(JSON.parse(savedProfile))
        .then(setTasks)
        .finally(() => setLoadingTasks(false));
    }
  }, []);

  const toggleTask = (id: string) => {
    setTasks(prev => prev.map(t => t.id === id ? {...t, completed: !t.completed} : t));
  };

  return (
    <div className="space-y-10 animate-in fade-in duration-700">
      {/* Bio-Sync Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center space-x-6">
          <div className="w-16 h-16 rounded-2xl border-2 border-emerald-500/30 bg-slate-900 flex items-center justify-center text-emerald-500">
            <Cpu size={32} />
          </div>
          <div>
            <h2 className="text-4xl font-black text-white italic tracking-tighter uppercase">Mission Status: Operational</h2>
            <div className="flex items-center space-x-3 mt-1">
               <span className="text-[10px] font-black uppercase tracking-widest text-emerald-400 px-2 py-1 bg-emerald-500/10 rounded flex items-center">
                  <ShieldCheck size={12} className="mr-1" /> Core Synced
               </span>
               <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 italic">User-Node: 0xALEX</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: AI Daily Protocol */}
        <div className="lg:col-span-8 space-y-8">
          <div className="glass-panel p-10 rounded-[3rem] border border-white/5 relative overflow-hidden group">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-emerald-500/20 to-transparent"></div>
            
            <div className="flex items-center justify-between mb-8">
              <div>
                <h3 className="text-2xl font-black text-white italic tracking-tighter">NEURAL CHECKLIST</h3>
                <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em]">Computed for Current Biological State</p>
              </div>
              <div className="px-4 py-2 bg-slate-950 border border-white/10 rounded-xl text-[9px] font-black text-slate-500 uppercase tracking-widest">
                AI Refresh: 24h
              </div>
            </div>

            <div className="space-y-4">
              {loadingTasks ? (
                <div className="py-12 flex flex-col items-center justify-center space-y-4">
                  <BrainCircuit className="animate-spin text-emerald-500" size={40} />
                  <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Generating Strategy...</p>
                </div>
              ) : tasks.length > 0 ? (
                tasks.map((task) => (
                  <div 
                    key={task.id} 
                    onClick={() => toggleTask(task.id)}
                    className={`flex items-center justify-between p-6 rounded-2xl border transition-all cursor-pointer group ${
                      task.completed ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-slate-950 border-white/5 hover:border-white/10'
                    }`}
                  >
                    <div className="flex items-center space-x-6">
                      {task.completed ? <CheckCircle2 className="text-emerald-500" /> : <Circle className="text-slate-800" />}
                      <div>
                        <p className={`text-sm font-black italic uppercase tracking-tight ${task.completed ? 'text-emerald-400/50 line-through' : 'text-white'}`}>
                          {task.label}
                        </p>
                        <p className="text-[9px] font-black text-slate-600 uppercase tracking-widest mt-1">Scheduled: {task.time}</p>
                      </div>
                    </div>
                    <span className={`text-[8px] font-black uppercase px-2 py-1 rounded border ${
                      task.priority === 'High' ? 'border-rose-500/30 text-rose-500' : 'border-slate-800 text-slate-600'
                    }`}>
                      {task.priority} Priority
                    </span>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-slate-600 uppercase text-[10px] font-black tracking-widest">
                  Initialize Bio-Link to generate daily protocol.
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
             <div className="cyber-border p-8 rounded-[2.5rem] bg-slate-900/40 relative group overflow-hidden">
                <div className="flex justify-between items-start mb-6">
                   <div className="p-4 bg-orange-500/10 rounded-2xl text-orange-400">
                      <Flame size={24} />
                   </div>
                   <div className="flex items-center text-orange-500 text-[9px] font-black uppercase tracking-widest">
                      <TrendingUp size={12} className="mr-1" /> Metabolic Surge
                   </div>
                </div>
                <h4 className="text-3xl font-black text-white italic tracking-tighter">{stats?.daily_calories || 0} KCAL</h4>
                <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mt-2">Thermal Energy Burn / Node Goal: 3,000</p>
                <div className="mt-6 w-full bg-slate-950 h-1.5 rounded-full overflow-hidden">
                   <div className="bg-orange-500 h-full" style={{ width: `${Math.min(((stats?.daily_calories || 0)/3000)*100, 100)}%` }}></div>
                </div>
             </div>

             <div className="cyber-border p-8 rounded-[2.5rem] bg-slate-900/40 relative group overflow-hidden">
                <div className="flex justify-between items-start mb-6">
                   <div className="p-4 bg-cyan-500/10 rounded-2xl text-cyan-400">
                      <Activity size={24} />
                   </div>
                   <div className="flex items-center text-cyan-500 text-[9px] font-black uppercase tracking-widest">
                      <Zap size={12} className="mr-1" /> Recovery Status
                   </div>
                </div>
                <h4 className="text-3xl font-black text-white italic tracking-tighter">{recovery?.score || 85}% Ready</h4>
                <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mt-2">Neural Readiness Index</p>
                <p className="text-[10px] text-cyan-400/80 italic mt-4">"{recovery?.advice || 'System nominal.'}"</p>
             </div>
          </div>

          {/* NEW: Neural Integrity Engine Widget */}
          <div className="glass-panel p-10 rounded-[3rem] border border-white/5 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-8 text-white/5 group-hover:text-emerald-500/10 transition-colors">
              <Fingerprint size={120} />
            </div>
            <div className="flex items-center space-x-4 mb-8">
              <div className="p-4 bg-emerald-500/10 rounded-2xl text-emerald-400 border border-emerald-500/20">
                <ShieldCheck size={28} />
              </div>
              <div>
                <h3 className="text-2xl font-black text-white italic tracking-tighter uppercase">Neural Integrity Engine</h3>
                <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em]">Historical Biomechanical analysis</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-12 gap-10">
              <div className="md:col-span-5 flex flex-col items-center justify-center p-8 bg-slate-950/50 rounded-[2.5rem] border border-white/5">
                <div className="relative w-32 h-32 flex items-center justify-center mb-4">
                  <svg className="absolute inset-0 w-full h-full -rotate-90">
                    <circle cx="64" cy="64" r="60" stroke="rgba(255,255,255,0.05)" strokeWidth="8" fill="none" />
                    <circle cx="64" cy="64" r="60" stroke="#10b981" strokeWidth="8" fill="none" 
                      strokeDasharray="376.8" 
                      strokeDashoffset={376.8 - (376.8 * (integrity?.integrity_score || 100) / 100)} 
                      className="transition-all duration-1000 ease-out"
                    />
                  </svg>
                  <span className="text-4xl font-black text-white italic tracking-tighter">{(integrity?.integrity_score || 100).toFixed(0)}</span>
                </div>
                <p className="text-[10px] font-black text-emerald-400 uppercase tracking-widest">Integrity Index</p>
                <div className={`mt-4 px-4 py-1.5 rounded-full text-[8px] font-black uppercase tracking-widest border ${
                  integrity?.status === 'STABLE' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
                }`}>
                  System {integrity?.status || 'STABLE'}
                </div>
              </div>

              <div className="md:col-span-7 flex flex-col justify-between py-2">
                <div className="space-y-4">
                  <div className="flex items-center space-x-3 text-white/80">
                    <BrainCircuit size={18} className="text-emerald-400" />
                    <span className="text-[11px] font-black uppercase tracking-widest">Adaptive Corrective Directive:</span>
                  </div>
                  <p className="text-sm font-bold text-slate-300 italic leading-relaxed bg-slate-950/50 p-6 rounded-2xl border border-white/5">
                    "{integrity?.directive || 'No faults archived. Continue session.'}"
                  </p>
                </div>
                
                <div className="flex items-center space-x-6 mt-6">
                  <div className="flex flex-col">
                    <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest mb-1">Kinetic Focus</span>
                    <span className="text-[10px] font-black text-cyan-400 uppercase tracking-widest italic">{integrity?.focus_area || 'None'}</span>
                  </div>
                  <div className="w-px h-8 bg-white/10"></div>
                  <div className="flex flex-col">
                    <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest mb-1">Injury Risk</span>
                    <span className="text-[10px] font-black text-rose-400 uppercase tracking-widest italic">{(100 - (integrity?.integrity_score || 100)).toFixed(0)}% Delta</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: AI Diagnostics */}
        <div className="lg:col-span-4 space-y-8">
           <div className="glass-panel p-8 rounded-[3rem] border border-white/5 relative h-full">
              <div className="scanline absolute top-0 left-0"></div>
              <h3 className="text-2xl font-black text-white italic tracking-tighter mb-8 flex items-center">
                <BrainCircuit className="mr-3 text-emerald-400" /> RECOVERY HUD
              </h3>

              <div className="space-y-6">
                <div className="p-6 bg-slate-950/50 rounded-2xl border border-white/5">
                   <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-2">Stagnation Warning</p>
                   <div className="flex items-center space-x-3 text-emerald-400">
                      <ShieldCheck size={18} />
                      <span className="text-xs font-black italic uppercase">No Plateaus Detected</span>
                   </div>
                </div>

                <div className="p-6 bg-slate-950/50 rounded-2xl border border-white/5">
                   <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-2">Sleep Protocol</p>
                   <div className="space-y-3">
                      <div className="flex items-center space-x-3 text-cyan-400">
                        <Clock size={18} />
                        <span className="text-xs font-black italic uppercase">Circadian Sync: High</span>
                      </div>
                      <p className="text-[10px] text-slate-500 leading-relaxed font-medium italic">
                        "Shift core training window 30m earlier to optimize neural reset."
                      </p>
                   </div>
                </div>

                <div className="pt-8 mt-4 border-t border-white/5">
                   <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4">Weekly Kinetic Delta</p>
                   <ResponsiveContainer width="100%" height={120}>
                      <AreaChart data={[{v: 60}, {v: 80}, {v: 75}, {v: 95}, {v: 90}]}>
                        <Area type="monotone" dataKey="v" stroke="#10b981" fill="#10b981" fillOpacity={0.1} strokeWidth={3} />
                      </AreaChart>
                   </ResponsiveContainer>
                   <div className="mt-4 flex justify-between items-center">
                      <p className="text-[9px] font-black text-slate-500 uppercase">Performance Bias</p>
                      <p className="text-[10px] font-black text-emerald-400 italic">+12.4% ALPHA</p>
                   </div>
                </div>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
