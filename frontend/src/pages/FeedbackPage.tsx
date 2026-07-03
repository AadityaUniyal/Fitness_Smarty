import React, { useState, useEffect } from 'react';
import {
  Star, Send, MessageSquare, CheckCircle2, Loader2,
  AlertTriangle, ThumbsUp, ThumbsDown, Sparkles, Clock,
  ChevronDown, BarChart3, Zap, RefreshCw
} from 'lucide-react';
import { useToast } from '../hooks/useToast';
import ToastContainer from '../components/ToastContainer';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

type Category = 'general' | 'bug_report' | 'feature_request' | 'ai_quality' | 'ux' | 'performance';
type Module = 'dashboard' | 'workout' | 'nutrition' | 'ai_chat' | 'food_scanner' | 'live_coach' | 'progress' | 'bio_link' | 'femmecare';

const CATEGORIES: { value: Category; label: string; emoji: string }[] = [
  { value: 'general', label: 'General Feedback', emoji: '💬' },
  { value: 'bug_report', label: 'Bug Report', emoji: '🐛' },
  { value: 'feature_request', label: 'Feature Request', emoji: '✨' },
  { value: 'ai_quality', label: 'AI Quality', emoji: '🤖' },
  { value: 'ux', label: 'User Experience', emoji: '🎨' },
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

const StarRating: React.FC<{ value: number; onChange: (v: number) => void; hovered: number; onHover: (v: number) => void }> = ({ value, onChange, hovered, onHover }) => (
  <div className="flex space-x-2">
    {[1, 2, 3, 4, 5].map(star => (
      <button
        key={star}
        type="button"
        onClick={() => onChange(star)}
        onMouseEnter={() => onHover(star)}
        onMouseLeave={() => onHover(0)}
        className="transition-transform hover:scale-125 active:scale-110"
      >
        <Star
          size={36}
          className={`transition-colors ${
            star <= (hovered || value)
              ? 'text-amber-400 fill-amber-400'
              : 'text-slate-700'
          }`}
        />
      </button>
    ))}
  </div>
);

const STAR_LABELS = ['', 'Terrible', 'Poor', 'Average', 'Good', 'Excellent'];

const FeedbackPage: React.FC = () => {
  const user = JSON.parse(localStorage.getItem('smarty_user') || '{}');
  const { toasts, showToast, dismissToast } = useToast();

  // Form state
  const [rating, setRating] = useState(0);
  const [hoveredStar, setHoveredStar] = useState(0);
  const [category, setCategory] = useState<Category>('general');
  const [module, setModule] = useState<Module | ''>('');
  const [message, setMessage] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState<FeedbackEntry | null>(null);

  // History
  const [history, setHistory] = useState<FeedbackEntry[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [activeTab, setActiveTab] = useState<'submit' | 'history'>('submit');

  useEffect(() => {
    if (activeTab === 'history') loadHistory();
  }, [activeTab]);

  const loadHistory = async () => {
    setLoadingHistory(true);
    try {
      const res = await fetch(`${API_BASE}/api/feedback/user/${user.id || 'anonymous'}`);
      if (res.ok) setHistory(await res.json());
    } catch {
      // Show local mock if backend down
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
        user_id: isAnonymous ? 'anonymous' : (user.id || user.email || 'user-1'),
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
        // Fallback: store locally if backend down
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
      // Offline mode
      const localEntry: FeedbackEntry = {
        id: Date.now(),
        user_id: isAnonymous ? 'anonymous' : (user.id || 'user-1'),
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
    <div className="max-w-4xl mx-auto space-y-10 animate-in fade-in duration-700">
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Header */}
      <div className="flex items-center space-x-6">
        <div className="w-20 h-20 bg-violet-500/10 border border-violet-500/20 rounded-3xl flex items-center justify-center text-violet-400 shadow-[0_0_30px_rgba(139,92,246,0.1)]">
          <MessageSquare size={40} />
        </div>
        <div>
          <h2 className="text-4xl font-black italic tracking-tighter text-white uppercase">Neural Feedback</h2>
          <p className="text-[10px] font-black uppercase tracking-[0.4em] text-slate-500">
            Help us improve the Smarty AI platform
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex bg-slate-900/80 p-1.5 rounded-2xl border border-white/5 w-fit">
        {(['submit', 'history'] as const).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-8 py-2.5 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all ${
              activeTab === tab ? 'bg-violet-500 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'
            }`}>
            {tab === 'submit' ? '✍️ Submit' : '📋 History'}
          </button>
        ))}
      </div>

      {activeTab === 'submit' && (
        submitted ? (
          /* ── Success State ── */
          <div className="glass-panel p-12 rounded-[3rem] border border-white/5 text-center space-y-6 animate-in zoom-in-95 duration-500">
            <div className="w-24 h-24 bg-emerald-500/10 border border-emerald-500/20 rounded-3xl flex items-center justify-center mx-auto">
              <CheckCircle2 size={48} className="text-emerald-400" />
            </div>
            <div>
              <h3 className="text-2xl font-black text-white italic tracking-tighter">Feedback Received</h3>
              <p className="text-slate-400 text-sm mt-2">Your {submitted.rating}-star {submitted.category.replace('_', ' ')} feedback has been logged.</p>
            </div>

            {/* Sentiment badge */}
            {submitted.sentiment && (() => {
              const s = SENTIMENT_CONFIG[submitted.sentiment as keyof typeof SENTIMENT_CONFIG];
              if (!s) return null;
              const Icon = s.icon;
              return (
                <div className={`inline-flex items-center space-x-2 px-4 py-2 rounded-xl border ${s.bg}`}>
                  <Icon size={14} className={s.color} />
                  <span className={`text-[10px] font-black uppercase tracking-widest ${s.color}`}>{s.label} Sentiment</span>
                </div>
              );
            })()}

            {/* AI Response */}
            {submitted.ai_response && (
              <div className="p-6 bg-slate-950 border border-violet-500/20 rounded-2xl text-left">
                <div className="flex items-center space-x-2 mb-3">
                  <Sparkles size={14} className="text-violet-400" />
                  <span className="text-[9px] font-black uppercase tracking-widest text-violet-400">SMARTY AI Response</span>
                </div>
                <p className="text-sm text-slate-300 italic leading-relaxed">"{submitted.ai_response}"</p>
              </div>
            )}

            <button onClick={resetForm}
              className="inline-flex items-center space-x-2 px-8 py-4 bg-violet-500 hover:bg-violet-400 text-white rounded-2xl font-black text-xs uppercase tracking-widest transition-all active:scale-95">
              <RefreshCw size={14} />
              <span>Submit Another</span>
            </button>
          </div>
        ) : (
          /* ── Feedback Form ── */
          <form onSubmit={handleSubmit} className="glass-panel p-10 rounded-[3rem] border border-white/5 space-y-8">

            {/* Star Rating */}
            <div className="space-y-4">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">
                Overall Rating *
              </label>
              <StarRating value={rating} onChange={setRating} hovered={hoveredStar} onHover={setHoveredStar} />
              {(hoveredStar || rating) > 0 && (
                <p className={`text-sm font-black italic transition-colors ${
                  (hoveredStar || rating) >= 4 ? 'text-emerald-400' :
                  (hoveredStar || rating) === 3 ? 'text-amber-400' : 'text-rose-400'
                }`}>
                  {STAR_LABELS[hoveredStar || rating]}
                </p>
              )}
            </div>

            {/* Category + Module */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Category</label>
                <div className="grid grid-cols-2 gap-2">
                  {CATEGORIES.map(c => (
                    <button key={c.value} type="button" onClick={() => setCategory(c.value)}
                      className={`p-3 rounded-2xl border text-left transition-all ${
                        category === c.value
                          ? 'bg-violet-500/15 border-violet-500/40 text-violet-300'
                          : 'bg-slate-950/50 border-white/5 text-slate-500 hover:border-white/10'
                      }`}>
                      <span className="text-lg">{c.emoji}</span>
                      <p className="text-[8px] font-black uppercase tracking-widest mt-1 leading-tight">{c.label}</p>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-6">
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Module (optional)</label>
                  <select value={module} onChange={e => setModule(e.target.value as Module | '')}
                    className="w-full bg-slate-950 border border-white/10 rounded-2xl px-4 py-3 text-xs font-black text-slate-300 focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500/40 outline-none transition-all">
                    <option value="">— Select module —</option>
                    {MODULES.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                  </select>
                </div>

                {/* Anonymous toggle */}
                <div className="flex items-center justify-between p-4 bg-slate-950 border border-white/5 rounded-2xl">
                  <div>
                    <p className="text-xs font-black text-white">Submit Anonymously</p>
                    <p className="text-[9px] text-slate-500 mt-0.5">Your name won't be attached</p>
                  </div>
                  <button type="button" onClick={() => setIsAnonymous(v => !v)}
                    className={`w-12 h-6 rounded-full transition-all ${isAnonymous ? 'bg-violet-500' : 'bg-slate-800'}`}>
                    <div className={`w-5 h-5 bg-white rounded-full shadow-md transition-transform mx-0.5 ${isAnonymous ? 'translate-x-6' : 'translate-x-0'}`} />
                  </button>
                </div>
              </div>
            </div>

            {/* Message */}
            <div className="space-y-3">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center justify-between">
                <span>Your Feedback *</span>
                <span className={`${message.length > 1800 ? 'text-rose-400' : 'text-slate-600'}`}>{message.length}/2000</span>
              </label>
              <textarea
                value={message}
                onChange={e => setMessage(e.target.value)}
                rows={5}
                placeholder="Tell us what you think — bugs, ideas, praise, anything..."
                className="w-full bg-slate-950 border border-white/10 rounded-2xl px-6 py-4 text-sm text-white placeholder:text-slate-600 focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500/40 outline-none transition-all resize-none"
              />
            </div>

            <button type="submit" disabled={submitting || rating === 0}
              className="w-full py-5 bg-gradient-to-r from-violet-600 to-purple-500 hover:from-violet-500 hover:to-purple-400 disabled:from-slate-800 disabled:to-slate-800 disabled:text-slate-600 text-white rounded-2xl font-black text-sm uppercase tracking-widest shadow-xl shadow-violet-500/20 transition-all flex items-center justify-center space-x-3 active:scale-[0.99]">
              {submitting ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
              <span>{submitting ? 'Submitting...' : 'Send Feedback'}</span>
            </button>
          </form>
        )
      )}

      {activeTab === 'history' && (
        <div className="space-y-4">
          {loadingHistory ? (
            <div className="py-16 flex flex-col items-center space-y-4">
              <Loader2 size={32} className="animate-spin text-violet-400" />
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Loading feedback history...</p>
            </div>
          ) : history.length === 0 ? (
            <div className="glass-panel p-12 rounded-[3rem] border border-white/5 text-center">
              <MessageSquare size={48} className="text-slate-800 mx-auto mb-4" />
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">No feedback submitted yet.</p>
              <button onClick={() => setActiveTab('submit')}
                className="mt-6 px-8 py-3 bg-violet-500/10 border border-violet-500/20 text-violet-400 rounded-2xl text-[9px] font-black uppercase tracking-widest hover:bg-violet-500/20 transition-all">
                Submit Your First Feedback
              </button>
            </div>
          ) : (
            history.map(fb => {
              const sentConf = SENTIMENT_CONFIG[(fb.sentiment || 'neutral') as keyof typeof SENTIMENT_CONFIG];
              return (
                <div key={fb.id} className="glass-panel p-6 rounded-3xl border border-white/5 group hover:border-violet-500/20 transition-all">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      {[1,2,3,4,5].map(s => (
                        <Star key={s} size={14} className={s <= fb.rating ? 'text-amber-400 fill-amber-400' : 'text-slate-700'} />
                      ))}
                      <span className="text-[9px] font-black uppercase tracking-widest text-slate-500">{fb.category.replace('_', ' ')}</span>
                      {fb.module && <span className="text-[8px] font-black uppercase px-2 py-0.5 bg-slate-900 border border-white/5 rounded-lg text-slate-500">{fb.module}</span>}
                    </div>
                    <div className="flex items-center space-x-2">
                      {sentConf && (
                        <span className={`text-[8px] font-black uppercase px-2 py-0.5 rounded-lg border ${sentConf.bg} ${sentConf.color}`}>
                          {sentConf.label}
                        </span>
                      )}
                      <span className={`text-[8px] font-black uppercase px-2 py-0.5 rounded-lg border ${
                        fb.status === 'resolved' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
                        fb.status === 'reviewed' ? 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400' :
                        'bg-slate-500/10 border-slate-500/20 text-slate-500'
                      }`}>{fb.status}</span>
                    </div>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed">{fb.message}</p>
                  {fb.ai_response && (
                    <div className="mt-3 p-3 bg-violet-500/5 border border-violet-500/15 rounded-xl">
                      <p className="text-[9px] font-black text-violet-400 uppercase tracking-widest mb-1">
                        <Sparkles size={10} className="inline mr-1" />SMARTY Response
                      </p>
                      <p className="text-xs text-slate-400 italic">{fb.ai_response}</p>
                    </div>
                  )}
                  <p className="text-[8px] text-slate-600 mt-3 flex items-center">
                    <Clock size={10} className="mr-1.5" />
                    {new Date(fb.created_at).toLocaleString()}
                  </p>
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
};

export default FeedbackPage;
