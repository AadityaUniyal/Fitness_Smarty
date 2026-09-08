import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lightbulb, ArrowRight, Loader2, Brain, CheckCircle2, Clock } from 'lucide-react';
import { use3DTilt } from '../hooks/use3DTilt';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface NextAction {
  title: string;
  description?: string;
  detail?: string;
  category?: string;
  route: string;
  reasoning?: string;
  priority?: string;
  is_femme_mode?: boolean;
}

interface Props {
  userId?: number | string;
  action?: NextAction;
  tasksCompleted?: number;
  tasksTotal?: number;
  timeCategory?: string;
  genderMode?: string;
  onAction?: (action: NextAction) => void;
}

export default function SmartNextMove({
  userId,
  action: propAction,
  tasksCompleted: propTasksCompleted,
  tasksTotal: propTasksTotal,
  timeCategory: propTimeCategory,
  genderMode,
  onAction
}: Props) {
  const [data, setData] = useState<{ time_category: string; tasks_total: number; tasks_completed: number; next_action: NextAction } | null>(null);
  const [loading, setLoading] = useState(!propAction && !!userId);
  const navigate = useNavigate();
  const cardTilt = use3DTilt<HTMLDivElement>({ maxTilt: 6 });

  useEffect(() => {
    if (propAction) {
      setLoading(false);
      return;
    }
    if (!userId) return;
    (async () => {
      try {
        const r = await fetch(`${API}/api/nextmove/${userId}`);
        if (r.ok) setData(await r.json());
      } catch {} finally { setLoading(false); }
    })();
  }, [userId, propAction]);

  if (loading) return (
    <div className="glass-panel rounded-[2rem] border border-white/10 p-6 flex items-center justify-center gap-2 text-slate-400 text-xs font-bold uppercase tracking-wider">
      <Loader2 size={16} className="animate-spin text-emerald-400" /> Analyzing current telemetry...
    </div>
  );

  const activeAction = propAction || data?.next_action;
  if (!activeAction) return null;

  const tasks_completed = propTasksCompleted !== undefined ? propTasksCompleted : (data?.tasks_completed || 0);
  const tasks_total = propTasksTotal !== undefined ? propTasksTotal : (data?.tasks_total || 0);
  const time_category = propTimeCategory || data?.time_category || 'today';
  
  const isFemme = genderMode === 'femmecare' || activeAction.is_femme_mode || false;
  const allDone = tasks_completed >= tasks_total && tasks_total > 0;

  const gradient = isFemme ? 'from-pink-500 to-purple-500' : 'from-emerald-500 to-cyan-500';
  const bgGlow = isFemme ? 'bg-pink-500/10' : 'bg-emerald-500/10';
  const borderGlow = isFemme ? 'border-pink-500/20' : 'border-emerald-500/20';
  const iconColor = isFemme ? 'text-pink-400' : 'text-emerald-400';

  return (
    <div 
      ref={cardTilt.ref as any}
      style={cardTilt.style}
      onMouseMove={cardTilt.onMouseMove as any}
      onMouseLeave={cardTilt.onMouseLeave as any}
      className={`${bgGlow} border ${borderGlow} rounded-[2.5rem] p-6 transition-all duration-300 backdrop-blur-xl card-3d`}
    >
      <div className="card-3d-shine" />
      <div className="flex items-center gap-2 mb-3">
        {allDone ? <CheckCircle2 size={18} className="text-emerald-400" /> : <Brain size={18} className={iconColor} />}
        <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">
          {allDone ? 'Day Protocol Completed' : 'Smart Next Move'}
        </span>
        <span className="text-[9px] font-black uppercase tracking-widest text-slate-500 ml-auto flex items-center gap-1">
          <Clock size={10} /> {time_category}
        </span>
      </div>

      <div className={`bg-linear-to-r ${gradient} bg-clip-text text-transparent font-black italic text-xl mb-1 uppercase tracking-tight`}>
        {activeAction.title}
      </div>
      <p className="text-slate-300 text-xs font-semibold leading-relaxed mb-4">{activeAction.detail || activeAction.description || 'Action required.'}</p>

      <div className="flex items-center justify-between gap-4">
        <div className="text-[10px] font-bold text-slate-400 flex items-center gap-1.5 uppercase tracking-wider">
          <Lightbulb size={14} className="text-amber-400 shrink-0" /> {activeAction.reasoning || `Priority: ${activeAction.priority || 'Medium'}`}
        </div>
        <button 
          onClick={() => { navigate(activeAction.route); onAction?.(activeAction); }}
          className={`bg-linear-to-r ${gradient} text-slate-950 text-xs font-black uppercase tracking-widest px-6 py-3 rounded-2xl shadow-lg transition flex items-center gap-2 shrink-0 active:scale-95`}
        >
          Execute <ArrowRight size={14} />
        </button>
      </div>

      {tasks_total > 0 && (
        <div className="mt-4 pt-3 border-t border-white/5 flex items-center gap-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
          <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden border border-white/5">
            <div className={`bg-linear-to-r ${gradient} h-1.5 rounded-full transition-all duration-500`} style={{ width: `${(tasks_completed / tasks_total) * 100}%` }} />
          </div>
          <span>{tasks_completed}/{tasks_total}</span>
        </div>
      )}
    </div>
  );
}
