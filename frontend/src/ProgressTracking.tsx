
import React from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
  Cell
} from 'recharts';
import { Calendar, Trophy, Target, Star } from 'lucide-react';

const weightHistory = [
  { date: 'Jan 1', weight: 85.0 },
  { date: 'Jan 15', weight: 84.2 },
  { date: 'Feb 1', weight: 83.5 },
  { date: 'Feb 15', weight: 82.8 },
  { date: 'Mar 1', weight: 81.5 },
  { date: 'Mar 15', weight: 80.2 },
];

const strengthData = [
  { lift: 'Bench', start: 60, current: 85 },
  { lift: 'Squat', start: 80, current: 110 },
  { lift: 'Deadlift', start: 100, current: 140 },
  { lift: 'OHP', start: 40, current: 55 },
];

const ProgressTracking: React.FC = () => {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-3xl font-bold">Your Transformation</h2>
          <p className="text-slate-400">Tracking every step of your journey.</p>
        </div>
        <div className="flex space-x-2">
            <div className="bg-slate-900 p-2 rounded-lg border border-slate-800 flex items-center space-x-2 text-xs font-bold uppercase text-slate-400">
                <Calendar size={14} />
                <span>Last 90 Days</span>
            </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-slate-900/40 border border-slate-800 p-8 rounded-3xl h-[450px]">
          <h3 className="text-xl font-bold mb-8 flex items-center">
            <Target className="mr-2 text-emerald-400" /> Weight Progress
          </h3>
          <ResponsiveContainer width="100%" height="80%">
            <LineChart data={weightHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis dataKey="date" stroke="#64748b" tick={{fontSize: 12}} axisLine={false} tickLine={false} />
              <YAxis domain={['auto', 'auto']} stroke="#64748b" tick={{fontSize: 12}} axisLine={false} tickLine={false} />
              <Tooltip 
                contentStyle={{backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px'}}
              />
              <Line 
                type="monotone" 
                dataKey="weight" 
                stroke="#10b981" 
                strokeWidth={4} 
                dot={{r: 6, fill: '#10b981', strokeWidth: 3, stroke: '#0f172a'}} 
                activeDot={{r: 8, strokeWidth: 0}}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-slate-900/40 border border-slate-800 p-8 rounded-3xl h-[450px]">
          <h3 className="text-xl font-bold mb-8 flex items-center">
            <Trophy className="mr-2 text-blue-400" /> Strength Gains (kg)
          </h3>
          <ResponsiveContainer width="100%" height="80%">
            <BarChart data={strengthData} barGap={12}>
              <XAxis dataKey="lift" stroke="#64748b" tick={{fontSize: 12}} axisLine={false} tickLine={false} />
              <YAxis stroke="#64748b" tick={{fontSize: 12}} axisLine={false} tickLine={false} />
              <Tooltip 
                 cursor={{fill: 'rgba(255,255,255,0.05)'}}
                 contentStyle={{backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px'}}
              />
              <Legend verticalAlign="top" height={36}/>
              <Bar dataKey="start" fill="#334155" radius={[4, 4, 0, 0]} name="Baseline" />
              <Bar dataKey="current" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Current Max" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-gradient-to-br from-emerald-500 to-cyan-600 rounded-3xl p-8 text-slate-950 flex flex-col md:flex-row items-center justify-between shadow-2xl shadow-emerald-500/20">
        <div className="flex items-center space-x-6">
            <div className="bg-white/20 p-6 rounded-full">
                <Star size={48} className="text-white fill-white" />
            </div>
            <div>
                <h3 className="text-2xl font-black uppercase italic tracking-tighter">Consistency Award</h3>
                <p className="text-emerald-50 text-sm font-medium mt-1">You've hit your goals 14 days in a row! You're in the top 5% of users this week.</p>
            </div>
        </div>
        <button className="mt-6 md:mt-0 bg-slate-950 text-white font-bold px-8 py-3 rounded-xl hover:bg-slate-900 transition-colors uppercase tracking-widest text-xs">
            Share Milestone
        </button>
      </div>
    </div>
  );
};

export default ProgressTracking;
