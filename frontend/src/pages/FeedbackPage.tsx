import React, { useState, useEffect } from 'react';
import {
  Star, Send, MessageSquare, CheckCircle2, Loader2,
  ThumbsUp, ThumbsDown, Sparkles, Clock, RefreshCw
} from 'lucide-react';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';
import { useCurrentUserId } from '../hooks/useCurrentUserId';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

type Category = 'general' | 'bug_report' | 'feature_request' | 'ai_quality' | 'ux' | 'performance';
type Module = 'dashboard' | 'workout' | 'nutrition' | 'ai_chat' | 'food_scanner' | 'live_coach' | 'progress' | 'bio_link' | 'femmecare';

const CATEGORIES: { value: Category; label: string; emoji: string }[] = [
  { value: 'general', label: 'General', emoji: '💬' },
  { value: 'bug_report', label: 'Bug Report', emoji: '🐛' },
  { value: 'feature_request', label: 'Feature', emoji: '✨' },
  { value: 'ai_quality', label: 'AI Quality', emoji: '🤖' },
  { value: 'ux', label: 'UX', emoji: '🎨' },
  { value: 'performance', label: 'Performance', emoji: '⚡' },
];

const MODULES: { value: Module; label: string }[] = [
  { value: 'dashboard', label: 'Dashboard' },
  { value: 'workout', label: 'Workout Planner' },
  { value: 'nutrition', label: 'Nutrition Hub' },
  { value: 'ai_chat', label: 'AI Chat' },
  { value: 'food_scanner', label: 'Food Scanner' },
  { value: 'live_coach', label: 'Live Coach' },
  { value: 'progress', label: 'Progress Tracking' },
  { value: 'bio_link', label: 'Bio Link' },
  { value: 'femmecare', label: 'FemmeCare' },
];

const SENTIMENT_CONFIG = {
  positive: { label: 'Positive', color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20', icon: ThumbsUp },
  neutral: { label: 'Neutral', color: 'text-slate-400', bg: 'bg-slate-500/10 border-slate-500/20', icon: MessageSquare },
  negative: { label: 'Negative', color: 'text-rose-400', bg: 'bg-rose-500/10 border-rose-500/20', icon: ThumbsDown },
};

interface FeedbackEntry {
  id: number;
  user_id: string;
  rating: number;
  category: string;
  message: string;
  module: string | null;
  sentiment: string | null;
  status: string;
  ai_response: string | null;
  is_anonymous: boolean;
  created_at: string;
}

const STAR_LABELS = ['', 'Terrible', 'Poor', 'Average', 'Good', 'Excellent'];

const StarRating: React.FC<{ value: number; onChange: (v: number) => void; hovered: number; onHover: (v: number) => void }> = ({ value, onChange, hovered, onHover }) => (
  <div className="flex space-x-2">
    {[1, 2, 3, 4, 5].map(star => (
      <button key={star} type="button" onClick={() => onChange(star)} onMouseEnter={() => onHover(star)} onMouseLeave={() => onHover(0)} className="transition-transform hover:scale-125">
        <Star size={24} className={star <= (hovered || value) ? 'text-amber-400 fill-amber-400' : 'text-slate-700'} />
      </button>
    ))}
  </div>
);

const FeedbackPage: React.FC = () => {
  const userId = useCurrentUserId();
  const { toasts, showToast, dismissToast } = useToast();
  const [rating, setRating] = useState(0);
  const [hoveredStar, setHoveredStar] = useState(0);
  const [category, setCategory] = useState<Category>('general');
  const [module, setModule] = useState<Module | ''>('');
  const [message, setMessage] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState<FeedbackEntry | null>(null);
  const [history, setHistory] = useState<FeedbackEntry[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [activeTab, setActiveTab] = useState<'submit' | 'history'>('submit');

  useEffect(() => { if (activeTab === 'history') loadHistory(); }, [activeTab]);

  const loadHistory = async () => {
    setLoadingHistory(true);
    try {
      const res = await fetch(`${API_BASE}/api/feedback/user/${userId}`);
      if (res.ok) setHistory(await res.json());
    } catch {
      setHistory([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rating === 0) { showToast('Please select a star rating', 'warning'); return; }
    if (message.trim().length < 5) { showToast('Message must be at least 5 characters', 'warning'); return; }

    setSubmitting(true);
    try {
      const payload = {
        user_id: isAnonymous ? 'anonymous' : (userId || 'user-1'),
        rating,
        category,
        message: message.trim(),
        module: module || null,
        is_anonymous: isAnonymous,
      };

      const res = await fetch(`${API_BASE}/api/feedback/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data: FeedbackEntry = await res.json();
        setSubmitted(data);
        showToast('Feedback submitted successfully!', 'success');
      } else {
        const localEntry: FeedbackEntry = {
          id: Date.now(),
          ...payload,
          sentiment: rating >= 4 ? 'positive' : rating <= 2 ? 'negative' : 'neutral',
          status: 'open',
          ai_response: null,
          created_at: new Date().toISOString(),
        };
        setSubmitted(localEntry);
        showToast('Feedback saved locally (backend offline)', 'info');
      }
    } catch {
      const localEntry: FeedbackEntry = {
        id: Date.now(),
        user_id: isAnonymous ? 'anonymous' : (userId || 'user-1'),
        rating, category, message: message.trim(),
        module: module || null,
        sentiment: rating >= 4 ? 'positive' : rating <= 2 ? 'negative' : 'neutral',
        status: 'open', ai_response: null, is_anonymous: isAnonymous,
        created_at: new Date().toISOString(),
      };
      setSubmitted(localEntry);
      showToast('Feedback saved locally', 'info');
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setRating(0); setCategory('general'); setModule('');
    setMessage(''); setIsAnonymous(false); setSubmitted(null);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-10">
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
      <div className="flex items-center space-x-6">
        <div className="w-16 h-16 bg-violet-500/10 border border-violet-500/20 rounded-2xl flex items-center justify-center text-violet-400">
          <MessageSquare size={32} />
        </div>
        <div>
          <h2 className="text-3xl font-black italic text-white uppercase">Neural Feedback</h2>
          <p className="text-xs text-slate-500">Help us improve the Smarty AI platform</p>
        </div>
      </div>

      <div className="flex bg-slate-900 p-1 rounded-2xl border border-white/5 w-fit">
        {(['submit', 'history'] as const).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-6 py-2 text-xs font-black uppercase rounded-xl transition-all ${activeTab === tab ? 'bg-violet-500 text-white' : 'text-slate-500'}`}>
            {tab === 'submit' ? 'Submit' : 'History'}
          </button>
        ))}
      </div>

      {activeTab === 'submit' && (
        submitted ? (
          <div className="glass-panel p-8 rounded-3xl text-center space-y-4">
            <CheckCircle2 size={40} className="text-emerald-400 mx-auto" />
            <h3 className="text-xl font-bold text-white">Feedback Received!</h3>
            <button onClick={resetForm} className="px-6 py-2 bg-violet-500 text-white rounded-xl text-xs font-bold">Submit Another</button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="glass-panel p-8 rounded-3xl space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-400">Category</label>
                <select
                  value={category}
                  onChange={e => setCategory(e.target.value as Category)}
                  className="w-full bg-slate-950 border border-white/10 rounded-xl p-3 text-xs text-white"
                >
                  {CATEGORIES.map(c => (
                    <option key={c.value} value={c.value}>{c.emoji} {c.label}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-400">Module</label>
                <select
                  value={module}
                  onChange={e => setModule(e.target.value as Module)}
                  className="w-full bg-slate-950 border border-white/10 rounded-xl p-3 text-xs text-white"
                >
                  {MODULES.map(m => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-400">Rating</label>
              <StarRating value={rating} onChange={setRating} hovered={hoveredStar} onHover={setHoveredStar} />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-400">Message</label>
              <textarea value={message} onChange={e => setMessage(e.target.value)} rows={4} className="w-full bg-slate-950 border border-white/10 rounded-xl p-4 text-xs text-white" placeholder="Tell us how we can improve..." />
            </div>
            <button type="submit" disabled={submitting} className="px-6 py-3 bg-violet-500 hover:bg-violet-400 text-white rounded-xl text-xs font-bold transition">
              {submitting ? 'Submitting...' : 'Send Feedback'}
            </button>
          </form>
        )
      )}

      {activeTab === 'history' && (
        <div className="space-y-4">
          {loadingHistory ? (
            <p className="text-xs text-slate-500 text-center py-8">Loading history...</p>
          ) : history.length === 0 ? (
            <div className="glass-panel p-8 rounded-3xl text-center text-slate-500 text-xs">
              No feedback submitted yet.
            </div>
          ) : (
            history.map(item => (
              <div key={item.id} className="glass-panel p-6 rounded-2xl border border-white/5 space-y-2">
                <div className="flex items-center justify-between text-xs font-bold text-slate-400">
                  <span>Rating: {item.rating}★</span>
                  <span>{new Date(item.created_at).toLocaleDateString()}</span>
                </div>
                <p className="text-xs text-white">{item.message}</p>
                {item.ai_response && (
                  <p className="text-xs text-violet-400 italic">AI: {item.ai_response}</p>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default FeedbackPage;
