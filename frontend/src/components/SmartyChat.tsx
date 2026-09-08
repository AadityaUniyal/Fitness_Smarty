import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Loader2, Zap, Trash2, Volume2, VolumeX, Sparkles } from 'lucide-react';
import { sendCoachMessage, playCoachSpeech } from '../services/geminiService';
import { fetchDailyCoach } from '../services/apiService';
import { useUserProfile } from '../hooks/useUserProfile';
import VoiceLogger from './VoiceLogger';

interface Message {
  role: 'user' | 'model';
  text: string;
  provider?: string;
}

const STORAGE_KEY = 'smarty_chat_messages';

const QUICK_PROMPTS = [
  'Optimize my workout for today',
  'What should I eat to hit my protein goal?',
  'How do I break through a plateau?',
  'Best recovery tips after leg day',
];

const formatText = (text: string): React.ReactNode[] => {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="font-black text-emerald-300">{part.slice(2, -2)}</strong>;
    }
    return <span key={i}>{part}</span>;
  });
};

const introMessage: Message = {
  role: 'model',
  text: 'Neural link established. I am **SMARTY**, your multi-provider AI fitness consultant (powered by Groq, Gemini, OpenRouter & Deepgram). How can I optimize your performance today?',
  provider: 'Groq/Gemini',
};

const loadMessages = (): Message[] => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) return JSON.parse(saved);
  } catch {}
  return [introMessage];
};

const SmartyChat: React.FC = () => {
  const { profile } = useUserProfile();
  const [messages, setMessages] = useState<Message[]>(loadMessages);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [playingIndex, setPlayingIndex] = useState<number | null>(null);
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);
  const [dailyCoach, setDailyCoach] = useState<any>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Preload today's coach context
    fetchDailyCoach(undefined, async () => null)
      .then(data => setDailyCoach(data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const clearHistory = () => {
    if (currentAudio) {
      currentAudio.pause();
      setCurrentAudio(null);
      setPlayingIndex(null);
    }
    setMessages([introMessage]);
    localStorage.setItem(STORAGE_KEY, JSON.stringify([introMessage]));
  };

  const handlePlayVoice = async (text: string, index: number) => {
    if (playingIndex === index && currentAudio) {
      currentAudio.pause();
      setCurrentAudio(null);
      setPlayingIndex(null);
      return;
    }
    if (currentAudio) {
      currentAudio.pause();
    }
    setPlayingIndex(index);
    try {
      const audio = await playCoachSpeech(text);
      setCurrentAudio(audio);
      audio.onended = () => {
        setPlayingIndex(null);
        setCurrentAudio(null);
      };
    } catch (err) {
      console.error('Error playing coach voice with Deepgram:', err);
      setPlayingIndex(null);
    }
  };

  const handleSend = async (text?: string) => {
    const userMessage = (text || input).trim();
    if (!userMessage || loading) return;

    setInput('');
    const updated = [...messages, { role: 'user' as const, text: userMessage }];
    setMessages(updated);
    setLoading(true);

    try {
      const enhancedProfile = {
        ...profile,
        today_coach_summary: dailyCoach?.coach_summary || '',
        today_coach_workout: dailyCoach?.workout_recommendation?.reasoning || '',
        today_coach_meal: dailyCoach?.meal_recommendation?.next_meal || '',
        today_coach_tasks: dailyCoach?.daily_tasks || [],
      };
      const response = await sendCoachMessage(userMessage, enhancedProfile, messages);
      setMessages(prev => [
        ...prev,
        {
          role: 'model',
          text: response || "I couldn't process that. Try asking again.",
          provider: 'Smarty Multi-Provider Engine',
        },
      ]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [
        ...prev,
        {
          role: 'model',
          text: '**Connection notice:** Re-routing via backup neural layer. How can I assist with your workout or diet plan today?',
          provider: 'Local Neural Fallback',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100dvh-12rem)] min-h-[500px] flex flex-col glass-panel rounded-[2.5rem] border border-white/10 overflow-hidden card-3d">
      <div className="card-3d-shine" />
      <div className="p-6 border-b border-white/10 flex items-center justify-between bg-slate-950/60 backdrop-blur-md shrink-0">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-emerald-500 rounded-2xl flex items-center justify-center text-slate-950 shadow-lg shadow-emerald-500/20 relative">
            <Bot size={26} />
            <div className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-emerald-400 border-2 border-slate-900 animate-ping" />
          </div>
          <div>
            <h3 className="text-base font-black text-white uppercase tracking-widest flex items-center gap-2">
              SMARTY AI Assistant
              <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 text-[9px] font-black rounded-md tracking-normal">
                ONLINE
              </span>
            </h3>
            <p className="text-[9px] text-emerald-400 font-black uppercase tracking-[0.3em] flex items-center">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-2 animate-pulse" />
              Groq • Gemini • OpenRouter • Deepgram Voice
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {messages.length > 1 && (
            <button
              onClick={clearHistory}
              className="p-2 hover:bg-white/5 rounded-xl text-slate-600 hover:text-rose-400 transition"
              title="Clear conversation"
            >
              <Trash2 size={15} />
            </button>
          )}
          <div className="px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center space-x-2">
            <Zap size={12} className="text-emerald-400" />
            <span className="text-[9px] font-black text-emerald-400 uppercase tracking-widest">Multi-Provider Live</span>
          </div>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-6 space-y-5 scroll-smooth custom-scrollbar"
      >
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-2 duration-300`}
          >
            <div className={`flex max-w-[85%] space-x-3 ${msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : 'flex-row'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1 ${
                msg.role === 'user' ? 'bg-slate-800 text-slate-400 border border-slate-700' : 'bg-linear-to-br from-emerald-500 to-cyan-500 text-slate-950'
              }`}>
                {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
              </div>
              <div className={`p-4 rounded-3xl relative group ${
                msg.role === 'user'
                  ? 'bg-emerald-500 text-slate-950 font-semibold rounded-tr-lg'
                  : 'bg-slate-800/80 text-slate-200 border border-slate-700/50 rounded-tl-lg'
              }`}>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{formatText(msg.text)}</p>
                
                {msg.role === 'model' && (
                  <div className="mt-2 pt-2 border-t border-slate-700/40 flex items-center justify-between text-[10px] text-slate-400">
                    <span className="flex items-center gap-1">
                      <Sparkles size={10} className="text-emerald-400" />
                      {msg.provider || 'Smarty AI'}
                    </span>
                    <button
                      onClick={() => handlePlayVoice(msg.text, i)}
                      className="p-1 px-2 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 flex items-center gap-1.5 transition text-[9px] font-bold uppercase tracking-wider"
                      title="Listen with Deepgram Neural Voice"
                    >
                      {playingIndex === i ? (
                        <>
                          <VolumeX size={12} className="text-rose-400" />
                          <span className="text-rose-400">Stop</span>
                        </>
                      ) : (
                        <>
                          <Volume2 size={12} />
                          <span>Listen</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-800 p-4 rounded-3xl flex items-center space-x-3 border border-slate-700/50 rounded-tl-lg">
              <Loader2 size={16} className="animate-spin text-emerald-400" />
              <div className="flex space-x-1">
                {[0, 1, 2].map(i => (
                  <div key={i} className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-bounce" style={{ animationDelay: `${i * 150}ms` }} />
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="px-6 pb-3 flex gap-2 overflow-x-auto shrink-0" style={{ scrollbarWidth: 'none' }}>
        {QUICK_PROMPTS.map((p, i) => (
          <button
            key={i}
            onClick={() => handleSend(p)}
            disabled={loading}
            className="shrink-0 px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-[9px] font-black text-emerald-400 uppercase tracking-wider hover:bg-emerald-500/20 transition-all whitespace-nowrap disabled:opacity-50"
          >
            {p}
          </button>
        ))}
      </div>

      <div className="p-5 bg-slate-900/60 backdrop-blur-md border-t border-slate-800 shrink-0">
        <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="relative flex items-center gap-2">
          <div className="relative flex-1">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask SMARTY anything about fitness, nutrition, recovery (or use mic)..."
              className="w-full bg-slate-800 border border-slate-700 rounded-2xl py-4 pl-6 pr-14 text-sm focus:outline-none focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/10 transition-all placeholder:text-slate-500"
            />
            <div className="absolute right-2 top-2">
              <VoiceLogger
                mode="general"
                onTranscript={(transcript) => {
                  if (transcript) {
                    setInput(prev => (prev ? `${prev} ${transcript}` : transcript));
                  }
                }}
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="p-4 bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-950 rounded-2xl transition-all shadow-lg shadow-emerald-500/10 active:scale-95 flex items-center justify-center shrink-0"
          >
            {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </form>
      </div>
    </div>
  );
};

export default SmartyChat;
