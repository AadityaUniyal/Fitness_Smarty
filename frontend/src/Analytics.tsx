
import React, { useState, useEffect } from 'react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, Legend
} from 'recharts';
import { LineChart, Line } from 'recharts';
import { TrendingUp, Activity, Target, Zap, Info, BrainCircuit, Calendar } from 'lucide-react';
import { fetchAnalytics } from './api';
import { BiometricPoint } from './types';

const Analytics: React.FC = () => {
  const [data, setData] = useState<BiometricPoint[]>([]);
  const [activeMetric, setActiveMetric] = useState<'steps' | 'weight' | 'heart_rate'>('steps');
  const [activeRange, setActiveRange] = useState<number>(7);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setIsLoading(true);
    fetchAnalytics('user-1', activeMetric, activeRange).then((res) => {
      setData(res);
      setIsLoading(false);
    });
  }, [activeMetric, activeRange]);

  const ranges = [
    { label: '7D', value: 7 },
    { label: '30D', value: 30 },
    { label: 'ALL', value: 0 },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h2 className="text-4xl font-black italic tracking-tighter text-white">NEURAL PROGRESS</h2>
          <p className="text-[10px] font-black uppercase tracking-[0.3em] text-emerald-500/80">Biometric Sync History • Node user-1</p>
        </div>
        
        <div className="flex flex-wrap gap-4 items-center">
          {/* Metric Selector */}
          <div className="flex bg-slate-900/80 p-1.5 rounded-2xl border border-white/5 backdrop-blur-xl">
            {(['steps', 'weight', 'heart_rate'] as const).map((m) => (
              <button
                key={m}
                onClick={() => setActiveMetric(m)}
                className={`px-5 py-2 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all ${
                  activeMetric === m 
                    ? 'bg-emerald-500 text-slate-950 shadow-[0_0_15px_rgba(16,185,129,0.4)]' 
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {m.replace('_', ' ')}
              </button>
            ))}
          </div>

          {/* Range Selector */}
          <div className="flex bg-slate-900/80 p-1.5 rounded-2xl border border-white/5 backdrop-blur-xl">
            {ranges.map((r) => (
              <button
                key={r.label}
                onClick={() => setActiveRange(r.value)}
                className={`px-4 py-2 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all ${
                  activeRange === r.value 
                    ? 'bg-cyan-500 text-slate-950 shadow-[0_0_15px_rgba(34,211,238,0.4)]' 
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Main Chart HUD */}
        <div className="lg:col-span-3 glass-panel p-8 rounded-[3rem] border border-white/5 h-[500px] relative overflow-hidden group">
          <div className="scanline absolute top-0 left-0"></div>
          <div className="absolute top-8 right-8 text-emerald-500/20 group-hover:text-emerald-500/40 transition-colors">
            <BrainCircuit size={80} />
          </div>
          
          <div className="mb-10 flex items-center justify-between">
            <div className="flex items-center space-x-4">
               <div className="p-3 bg-emerald-500/10 rounded-2xl text-emerald-400">
                  <Activity size={24} />
               </div>
               <div>
                  <h3 className="text-xl font-black text-white uppercase italic tracking-tighter">Performance Delta</h3>
                  <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">
                    {activeRange === 0 ? 'Full History Sync' : `${activeRange}-Day Adaptive Analysis`}
                  </p>
               </div>
            </div>
            {isLoading && (
              <div className="flex items-center space-x-2 text-cyan-400">
                <Zap size={14} className="animate-pulse" />
                <span className="text-[9px] font-black uppercase tracking-widest">Calibrating...</span>
              </div>
            )}
          </div>

          <ResponsiveContainer width="100%" height="75%">
            <AreaChart data={data}>
              <defs>
                <linearGradient id="colorMetric" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} opacity={0.3} />
              <XAxis 
                dataKey="timestamp" 
                axisLine={false} 
                tickLine={false} 
                tick={{fill: '#475569', fontSize: 9, fontWeight: 900}}
                tickFormatter={(str) => {
                  const date = new Date(str);
                  return activeRange > 30 
                    ? date.toLocaleDateString(undefined, {month: 'short', day: 'numeric'})
                    : date.toLocaleDateString(undefined, {weekday: 'short'});
                }}
              />
              <YAxis hide />
              <Tooltip 
                contentStyle={{backgroundColor: '#020617', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '16px', fontSize: '12px'}}
                itemStyle={{color: '#10b981', fontWeight: 900}}
                labelStyle={{color: '#64748b', marginBottom: '4px'}}
                labelFormatter={(label) => new Date(label).toLocaleDateString(undefined, { dateStyle: 'long' })}
              />
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke="#10b981" 
                strokeWidth={3}
                fillOpacity={1} 
                fill="url(#colorMetric)" 
                animationDuration={2000}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* HUD Stats Column */}
        <div className="space-y-6">
          <div className="cyber-border p-6 rounded-[2.5rem] bg-slate-900/40 border border-white/5 relative overflow-hidden group">
            <div className="absolute inset-0 bg-emerald-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">
              {activeRange === 0 ? 'Historical Avg' : `${activeRange}D Rolling Avg`}
            </p>
            <h4 className="text-4xl font-black text-white italic tracking-tighter">
              {activeMetric === 'weight' 
                ? `${(data.reduce((acc, curr) => acc + curr.value, 0) / (data.length || 1)).toFixed(1)}kg` 
                : Math.round(data.reduce((acc, curr) => acc + curr.value, 0) / (data.length || 1)).toLocaleString()}
            </h4>
            <div className="mt-4 flex items-center text-emerald-400 text-[10px] font-black">
              <TrendingUp size={14} className="mr-2" />
              STABLE PROGRESS
            </div>
          </div>

          <div className="glass-panel p-6 rounded-[2.5rem] border border-white/5 relative overflow-hidden group">
            <div className="flex items-center space-x-4 mb-4">
               <Target className="text-cyan-400" size={18} />
               <span className="text-[10px] font-black uppercase text-slate-400">Current Objective</span>
            </div>
            <p className="text-xs text-white font-bold italic leading-relaxed">
              Maintain metabolic intensity above 2.4k kcal/day for optimized hypertrophy.
            </p>
            <div className="mt-6 w-full bg-slate-950 h-1.5 rounded-full overflow-hidden">
               <div className="bg-cyan-400 h-full w-[65%] animate-pulse shadow-[0_0_8px_#22d3ee]"></div>
            </div>
          </div>

          <div className="p-6 rounded-[2.5rem] bg-gradient-to-br from-emerald-500 to-cyan-500 relative group overflow-hidden cursor-pointer active:scale-95 transition-all">
             <div className="absolute -top-4 -right-4 text-white/20 group-hover:scale-110 transition-transform">
                <Zap size={80} className="fill-white/10" />
             </div>
             <p className="text-[10px] font-black text-slate-950 uppercase tracking-widest">System Boost</p>
             <h4 className="text-lg font-black text-slate-950 mt-1 italic tracking-tight">ACTIVATE ELITE SYNC</h4>
             <button className="mt-4 bg-slate-950/20 px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest text-slate-950 border border-slate-950/10">Execute</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
