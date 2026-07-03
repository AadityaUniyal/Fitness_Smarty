import React, { useState, useEffect, useRef } from 'react';
import { Timer, Play, Pause, RotateCcw, X } from 'lucide-react';

interface RestTimerProps {
  onClose: () => void;
  defaultSeconds?: number;
}

const PRESETS = [30, 60, 90, 120, 180];

const RestTimer: React.FC<RestTimerProps> = ({ onClose, defaultSeconds = 60 }) => {
  const [seconds, setSeconds] = useState(defaultSeconds);
  const [remaining, setRemaining] = useState(defaultSeconds);
  const [running, setRunning] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    audioRef.current = new Audio(
      'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACAf39/f4B/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f39/f4B/f3+AgH9/f3+AgH9/f3+AgH9/f39/f4B/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f39/f4B/f3+AgH9/f39/f4B/f39/f4B/f39/f4B/f39/f4B/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f3+AgH9/f39/f4B/f3+AgH9/f39/f39/f4B/f39/f39/f4B/f39/f4B/f39/f39/f4B/f39/f39/f4B/f39/f39/f4B/f39/f39/f4B/f39/f4B/f3+AgH9/f3+AgH9/f3+AgH9/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/f39/w=='
    );
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  useEffect(() => {
    if (running) {
      intervalRef.current = setInterval(() => {
        setRemaining(prev => {
          if (prev <= 1) {
            setRunning(false);
            audioRef.current?.play().catch(() => {});
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [running]);

  const setTime = (s: number) => {
    setSeconds(s);
    setRemaining(s);
    setRunning(false);
  };

  const toggleRunning = () => {
    if (remaining === 0) {
      setRemaining(seconds);
    }
    setRunning(prev => !prev);
  };

  const reset = () => {
    setRemaining(seconds);
    setRunning(false);
  };

  const minutes = Math.floor(remaining / 60);
  const secs = remaining % 60;

  const radius = 56;
  const circumference = 2 * Math.PI * radius;
  const progress = seconds > 0 ? (remaining / seconds) * circumference : circumference;

  return (
    <div className="fixed bottom-6 right-6 z-50 bg-slate-900 border border-emerald-500/30 rounded-3xl p-6 shadow-2xl shadow-emerald-500/10 animate-in slide-in-from-bottom-4 duration-300 w-72">
      <button onClick={onClose} className="absolute top-3 right-3 p-1 hover:bg-white/5 rounded-lg text-slate-600 hover:text-white transition">
        <X size={14} />
      </button>

      <div className="flex items-center space-x-2 mb-4">
        <Timer size={14} className="text-emerald-400" />
        <span className="text-[10px] font-black text-emerald-400 uppercase tracking-widest">Rest Timer</span>
      </div>

      <div className="flex justify-center mb-4">
        <div className="relative w-28 h-28 flex items-center justify-center">
          <svg className="absolute inset-0 w-full h-full -rotate-90">
            <circle cx="56" cy="56" r={radius} fill="none" stroke="#1e293b" strokeWidth="6" />
            <circle
              cx="56" cy="56" r={radius}
              fill="none" stroke="#10b981"
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={circumference - progress}
              className="transition-all duration-1000 ease-linear"
            />
          </svg>
          <div className="relative text-center">
            <p className="text-3xl font-black text-white font-mono tracking-tight">
              {minutes}:{secs.toString().padStart(2, '0')}
            </p>
          </div>
        </div>
      </div>

      {/* Presets */}
      <div className="flex justify-center gap-1.5 mb-4">
        {PRESETS.map(p => (
          <button
            key={p}
            onClick={() => setTime(p)}
            className={`px-3 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest transition ${
              seconds === p ? 'bg-emerald-500 text-slate-950' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            {p < 60 ? `${p}s` : `${p / 60}m`}
          </button>
        ))}
      </div>

      {/* Controls */}
      <div className="flex justify-center space-x-3">
        <button
          onClick={toggleRunning}
          className="p-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-xl transition active:scale-95"
        >
          {running ? <Pause size={18} /> : <Play size={18} />}
        </button>
        <button
          onClick={reset}
          className="p-3 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded-xl transition active:scale-95"
        >
          <RotateCcw size={18} />
        </button>
      </div>

      {/* Notification when done */}
      {remaining === 0 && !running && seconds > 0 && (
        <p className="text-center text-emerald-400 text-[10px] font-black uppercase tracking-widest mt-3 animate-pulse">
          Rest complete!
        </p>
      )}
    </div>
  );
};

export default RestTimer;
