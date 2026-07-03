import React, { useState, useEffect, useCallback } from 'react';
import { Bell, BellOff, Clock, RotateCcw, CheckCircle2, AlertTriangle } from 'lucide-react';
import { Reminder, getReminders, saveReminders, requestNotificationPermission, hasNotificationPermission } from '../services/notificationService';

const DAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const DAY_FULL = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

const Reminders: React.FC = () => {
  const [reminders, setReminders] = useState<Reminder[]>(getReminders);
  const [notificationGranted, setNotificationGranted] = useState(hasNotificationPermission());
  const [justFired, setJustFired] = useState<string | null>(null);
  const [testStatus, setTestStatus] = useState<string | null>(null);

  useEffect(() => { saveReminders(reminders); }, [reminders]);

  const toggleReminder = (id: string) => {
    setReminders(prev => prev.map(r => r.id === id ? { ...r, enabled: !r.enabled } : r));
  };

  const updateTime = (id: string, time: string) => {
    setReminders(prev => prev.map(r => r.id === id ? { ...r, time } : r));
  };

  const toggleDay = (id: string, day: number) => {
    setReminders(prev => prev.map(r => {
      if (r.id !== id) return r;
      const days = r.days.includes(day) ? r.days.filter(d => d !== day) : [...r.days, day].sort();
      return { ...r, days };
    }));
  };

  const handleRequestPermission = async () => {
    const granted = await requestNotificationPermission();
    setNotificationGranted(granted);
    if (granted) setTestStatus('Notifications enabled');
    else setTestStatus('Permission denied — check browser settings');
    setTimeout(() => setTestStatus(null), 3000);
  };

  const handleTest = useCallback(() => {
    if (!hasNotificationPermission()) {
      setTestStatus('Enable notifications first');
      setTimeout(() => setTestStatus(null), 2000);
      return;
    }
    try {
      new Notification('SMARTY Reminder', { body: 'This is a test notification from your fitness assistant!' });
      setTestStatus('Test notification sent!');
    } catch {
      setTestStatus('Failed to send test notification');
    }
    setTimeout(() => setTestStatus(null), 2000);
  }, []);

  const resetDefaults = () => {
    const { getReminders } = require('../services/notificationService');
    setReminders(getReminders());
  };

  const enabledCount = reminders.filter(r => r.enabled).length;
  const totalCount = reminders.length;

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <div className="w-16 h-16 bg-amber-500/10 border border-amber-500/20 rounded-3xl flex items-center justify-center text-amber-400">
            <Bell size={32} />
          </div>
          <div>
            <h2 className="text-4xl font-black italic tracking-tighter text-white uppercase">Reminders</h2>
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">
              {enabledCount}/{totalCount} active
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <button onClick={handleTest}
            className="flex items-center space-x-2 px-5 py-3 bg-white/5 border border-white/10 text-white hover:bg-white/10 rounded-2xl font-black text-[10px] uppercase tracking-widest transition">
            <Bell size={14} />
            <span>Test</span>
          </button>
          <button onClick={resetDefaults}
            className="flex items-center space-x-2 px-5 py-3 bg-white/5 border border-white/10 text-white hover:bg-white/10 rounded-2xl font-black text-[10px] uppercase tracking-widest transition">
            <RotateCcw size={14} />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* Status bar */}
      {!notificationGranted ? (
        <div className="glass-panel p-6 rounded-[2rem] border border-amber-500/20 bg-amber-500/5">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 rounded-2xl bg-amber-500/10 flex items-center justify-center text-amber-400">
                <AlertTriangle size={24} />
              </div>
              <div>
                <p className="text-sm font-black text-amber-400">Notifications Not Enabled</p>
                <p className="text-[9px] text-slate-500 font-black uppercase tracking-widest mt-0.5">
                  Reminders work best with browser notifications
                </p>
              </div>
            </div>
            <button onClick={handleRequestPermission}
              className="px-6 py-3 bg-amber-500 hover:bg-amber-400 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest transition flex items-center space-x-2">
              <Bell size={14} />
              <span>Enable</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="glass-panel p-5 rounded-[2rem] border border-emerald-500/20 bg-emerald-500/5">
          <div className="flex items-center space-x-3">
            <CheckCircle2 size={18} className="text-emerald-400" />
            <span className="text-[10px] font-black text-emerald-400 uppercase tracking-widest">
              Notifications active — you'll be reminded at set times
            </span>
          </div>
        </div>
      )}

      {testStatus && (
        <div className={`px-5 py-3 rounded-2xl text-[10px] font-black uppercase tracking-widest border ${
          testStatus.includes('sent') || testStatus.includes('enabled')
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
            : 'bg-amber-500/10 border-amber-500/20 text-amber-400'
        }`}>
          {testStatus}
        </div>
      )}

      {/* Reminder list */}
      <div className="space-y-3">
        {reminders.map(r => {
          const isCurrentlyTime = (() => {
            const now = new Date();
            const [h, m] = r.time.split(':').map(Number);
            return now.getHours() === h && now.getMinutes() === m;
          })();
          return (
            <div key={r.id}
              className={`glass-panel rounded-[2rem] border transition-all ${
                r.enabled ? 'border-white/5 hover:border-white/10' : 'border-white/[0.02] opacity-50 hover:opacity-70'
              }`}>
              <div className="p-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className={`w-12 h-12 rounded-2xl flex items-center justify-center text-xl ${
                      r.enabled ? 'bg-amber-500/10 border border-amber-500/20' : 'bg-slate-900 border border-slate-800'
                    }`}>
                      {r.icon}
                    </div>
                    <div>
                      <div className="flex items-center space-x-3">
                        <p className={`text-sm font-black ${r.enabled ? 'text-white' : 'text-slate-500'}`}>{r.label}</p>
                        {isCurrentlyTime && r.enabled && (
                          <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-[7px] font-black uppercase tracking-widest rounded-full animate-pulse">
                            Now
                          </span>
                        )}
                      </div>
                      <p className="text-[9px] text-slate-600 font-black uppercase tracking-widest mt-0.5">{r.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-1.5">
                      <Clock size={12} className="text-slate-500" />
                      <input type="time" value={r.time} onChange={e => updateTime(r.id, e.target.value)}
                        className={`bg-transparent border-none text-[10px] font-black uppercase tracking-widest outline-none w-16 ${
                          r.enabled ? 'text-slate-300' : 'text-slate-600'
                        }`} />
                    </div>
                    <button onClick={() => toggleReminder(r.id)}
                      className={`p-2.5 rounded-xl transition-all ${
                        r.enabled
                          ? 'bg-amber-500/10 text-amber-400 hover:bg-amber-500/20'
                          : 'bg-slate-900 text-slate-600 hover:text-slate-400'
                      }`}>
                      {r.enabled ? <Bell size={14} /> : <BellOff size={14} />}
                    </button>
                  </div>
                </div>
                <div className="flex items-center space-x-1.5 mt-3 ml-0.5">
                  {DAY_LABELS.map((label, di) => (
                    <button key={di} onClick={() => toggleDay(r.id, di)}
                      className={`px-2.5 py-1 rounded-lg text-[7px] font-black uppercase tracking-widest transition-all ${
                        r.days.includes(di)
                          ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25'
                          : 'bg-slate-900 text-slate-600 border border-slate-800 hover:text-slate-400'
                      }`}>
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Reminders;
