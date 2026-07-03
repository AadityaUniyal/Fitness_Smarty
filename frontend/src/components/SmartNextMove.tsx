import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lightbulb, ArrowRight, Loader2, Brain, CheckCircle2, Clock } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface NextAction {
  title: string; description: string; category: string; route: string; reasoning: string; is_femme_mode: boolean;
}

interface Props {
  userId: number;
  onAction?: (action: NextAction) => void;
}

export default function SmartNextMove({ userId, onAction }: Props) {
  const [data, setData] = useState<{ time_category: string; tasks_total: number; tasks_completed: number; next_action: NextAction } | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${API}/api/nextmove/${userId}`);
        if (r.ok) setData(await r.json());
      } catch {} finally { setLoading(false); }
    })();
  }, [userId]);

  if (loading) return (
    <div className="bg-gray-900/80 border border-gray-700/50 rounded-xl p-5 flex items-center justify-center gap-2 text-gray-400 text-sm">
      <Loader2 size={16} className="animate-spin" /> Analyzing your day...
    </div>
  );

  if (!data) return null;

  const { next_action, tasks_completed, tasks_total, time_category } = data;
  const isFemme = next_action.is_femme_mode;
  const allDone = tasks_completed >= tasks_total && tasks_total > 0;

  const gradient = isFemme ? 'from-pink-500 to-purple-500' : 'from-indigo-500 to-purple-500';
  const bgGlow = isFemme ? 'bg-pink-500/5' : 'bg-indigo-500/5';
  const borderGlow = isFemme ? 'border-pink-500/20' : 'border-indigo-500/20';

  return (
    <div className={`${bgGlow} border ${borderGlow} rounded-xl p-5 transition hover:border-opacity-40`}>
      <div className="flex items-center gap-2 mb-3">
        {allDone ? <CheckCircle2 size={18} className="text-green-400" /> : <Brain size={18} className={`text-${isFemme ? 'pink' : 'indigo'}-400`} />}
        <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
          {allDone ? 'Day Complete' : 'Next Move'}
        </span>
        <span className="text-[10px] text-gray-500 ml-auto flex items-center gap-1">
          <Clock size={10} /> {time_category}
        </span>
      </div>

      <div className={`bg-gradient-to-r ${gradient} bg-clip-text text-transparent font-bold text-lg mb-1`}>
        {next_action.title}
      </div>
      <p className="text-gray-400 text-sm mb-3">{next_action.description}</p>

      <div className="flex items-center justify-between">
        <div className="text-xs text-gray-500 flex items-center gap-1">
          <Lightbulb size={12} className="text-yellow-400" /> {next_action.reasoning}
        </div>
        <button onClick={() => { navigate(next_action.route); onAction?.(next_action); }}
          className={`bg-gradient-to-r ${gradient} text-white text-xs font-medium px-4 py-2 rounded-lg hover:opacity-90 transition flex items-center gap-1.5`}>
          Go <ArrowRight size={14} />
        </button>
      </div>

      <div className="mt-3 pt-3 border-t border-gray-700/30 flex items-center gap-2 text-xs text-gray-500">
        <div className="w-full bg-gray-700 rounded-full h-1">
          <div className={`bg-gradient-to-r ${gradient} h-1 rounded-full transition-all`} style={{ width: `${tasks_total ? (tasks_completed / tasks_total) * 100 : 0}%` }} />
        </div>
        <span>{tasks_completed}/{tasks_total}</span>
      </div>
    </div>
  );
}
