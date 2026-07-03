import React, { useState, useEffect, useMemo } from 'react';
import { Bluetooth, RefreshCw, CheckCircle2, XCircle, Activity, Heart, Moon, Droplets, TrendingUp, Clock, Watch, Smartphone, Loader2 } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from 'recharts';

const STORAGE_KEY = 'smarty_wearable_connections';

interface WearableDevice { id: string; name: string; brand: string; icon: string; color: string; description: string; }
interface Connection { deviceId: string; connected: boolean; lastSync: string | null; }

const WEARABLES: WearableDevice[] = [
  { id: 'apple_health', name: 'Apple Health', brand: 'Apple', icon: '🍎', color: 'text-rose-400', description: 'Steps, HR, sleep, workouts' },
  { id: 'garmin', name: 'Garmin Connect', brand: 'Garmin', icon: '⌚', color: 'text-emerald-400', description: 'Running, cycling, HR, GPS' },
  { id: 'fitbit', name: 'Fitbit', brand: 'Google', icon: '📿', color: 'text-blue-400', description: 'Activity, sleep, HR, SpO2' },
  { id: 'whoop', name: 'Whoop', brand: 'Whoop', icon: '🫀', color: 'text-amber-400', description: 'HRV, recovery, strain, sleep' },
  { id: 'oura', name: 'Oura Ring', brand: 'Oura', icon: '💍', color: 'text-purple-400', description: 'Sleep, HRV, temp, readiness' },
];

const DAYS_7 = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const DAYS_7_DATA = DAYS_7.map((d, i) => ({
  day: d, steps: Math.round(5000 + Math.random() * 7000),
  hr: Math.round(62 + Math.random() * 12),
  sleep: +(6 + Math.random() * 2.5).toFixed(1),
  hrv: Math.round(45 + Math.random() * 35),
  spo2: +(96 + Math.random() * 3).toFixed(1),
  calories: Math.round(1800 + Math.random() * 800),
}));

function timeAgo(ts: string | null): string {
  if (!ts) return 'Never';
  const s = Math.floor((Date.now() - new Date(ts).getTime()) / 1000);
  if (s < 60) return 'Just now'; if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`; return `${Math.floor(s / 86400)}d ago`;
}

const WearableIntegrations: React.FC = () => {
  const [connections, setConnections] = useState<Connection[]>(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); } catch { return []; }
  });
  const [syncing, setSyncing] = useState<string | null>(null);
  const [selectedMetric, setSelectedMetric] = useState('steps');
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => { localStorage.setItem(STORAGE_KEY, JSON.stringify(connections)); }, [connections]);

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(null), 2000); };

  const getConnection = (deviceId: string) => connections.find(c => c.deviceId === deviceId);

  const toggleConnection = (deviceId: string) => {
    setConnections(prev => {
      const existing = prev.find(c => c.deviceId === deviceId);
      if (existing) {
        if (existing.connected) {
          showToast(`Disconnected from ${WEARABLES.find(w => w.id === deviceId)?.name}`);
          return prev.filter(c => c.deviceId !== deviceId);
        }
        return prev.map(c => c.deviceId === deviceId ? { ...c, connected: true } : c);
      }
      return [...prev, { deviceId, connected: true, lastSync: null }];
    });
    if (!getConnection(deviceId)?.connected) showToast(`Connected to ${WEARABLES.find(w => w.id === deviceId)?.name}`);
  };

  const handleSync = async (deviceId: string) => {
    setSyncing(deviceId);
    await new Promise(r => setTimeout(r, 1500 + Math.random() * 1000));
    setConnections(prev => prev.map(c => c.deviceId === deviceId ? { ...c, lastSync: new Date().toISOString() } : c));
    setSyncing(null);
    showToast(`Synced ${WEARABLES.find(w => w.id === deviceId)?.name} data`);
  };

  const syncAll = async () => {
    const connected = connections.filter(c => c.connected);
    if (connected.length === 0) { showToast('No devices connected'); return; }
    for (const c of connected) {
      setSyncing(c.deviceId);
      await new Promise(r => setTimeout(r, 800 + Math.random() * 600));
      setConnections(prev => prev.map(cc => cc.deviceId === c.deviceId ? { ...cc, lastSync: new Date().toISOString() } : cc));
    }
    setSyncing(null);
    showToast(`Synced ${connected.length} device${connected.length > 1 ? 's' : ''}`);
  };

  const todayData = useMemo(() => {
    const d = DAYS_7_DATA[6];
    return [
      { label: 'Steps', value: d.steps.toLocaleString(), unit: '', icon: Activity, color: 'text-emerald-400', metric: 'steps' },
      { label: 'Heart Rate', value: d.hr, unit: 'bpm', icon: Heart, color: 'text-rose-400', metric: 'hr' },
      { label: 'Sleep', value: d.sleep, unit: 'hrs', icon: Moon, color: 'text-indigo-400', metric: 'sleep' },
      { label: 'HRV', value: d.hrv, unit: 'ms', icon: TrendingUp, color: 'text-amber-400', metric: 'hrv' },
      { label: 'SpO₂', value: d.spo2, unit: '%', icon: Droplets, color: 'text-blue-400', metric: 'spo2' },
      { label: 'Calories', value: d.calories.toLocaleString(), unit: 'kcal', icon: Activity, color: 'text-orange-400', metric: 'calories' },
    ];
  }, []);

  const connectedCount = connections.filter(c => c.connected).length;

  const METRIC_LABELS: Record<string, string> = { steps: 'Steps', hr: 'Heart Rate (bpm)', sleep: 'Sleep (hrs)', hrv: 'HRV (ms)', spo2: 'SpO₂ (%)', calories: 'Calories' };
  const METRIC_COLORS: Record<string, string> = { steps: '#10b981', hr: '#f43f5e', sleep: '#818cf8', hrv: '#f59e0b', spo2: '#3b82f6', calories: '#f97316' };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {toast && (
        <div className="fixed top-6 right-6 z-50 px-5 py-3 bg-emerald-500/20 border border-emerald-500/30 rounded-2xl text-emerald-400 text-[10px] font-black uppercase tracking-widest backdrop-blur-xl animate-fade-in">
          {toast}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <div className="w-16 h-16 bg-cyan-500/10 border border-cyan-500/20 rounded-3xl flex items-center justify-center text-cyan-400">
            <Watch size={32} />
          </div>
          <div>
            <h2 className="text-4xl font-black italic tracking-tighter text-white uppercase">Wearables</h2>
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">
              {connectedCount} device{connectedCount !== 1 ? 's' : ''} connected
            </p>
          </div>
        </div>
        <button onClick={syncAll} disabled={connectedCount === 0}
          className="flex items-center space-x-2 px-5 py-3 bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest transition disabled:opacity-50">
          <RefreshCw size={14} className={syncing ? 'animate-spin' : ''} />
          <span>Sync All</span>
        </button>
      </div>

      {/* Device cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {WEARABLES.map(device => {
          const conn = getConnection(device.id);
          const isConnected = conn?.connected || false;
          return (
            <div key={device.id} className={`glass-panel rounded-[2rem] border p-5 transition-all ${
              isConnected ? 'border-white/10 hover:border-white/20' : 'border-white/[0.03] opacity-60 hover:opacity-80'
            }`}>
              <div className="flex flex-col items-center text-center">
                <div className={`w-16 h-16 rounded-2xl flex items-center justify-center text-3xl mb-4 ${
                  isConnected ? 'bg-white/[0.05] border border-white/10' : 'bg-slate-900 border border-slate-800'
                }`}>{device.icon}</div>
                <p className={`text-sm font-black ${isConnected ? 'text-white' : 'text-slate-500'}`}>{device.name}</p>
                <p className="text-[8px] text-slate-600 font-black uppercase tracking-widest mt-1">{device.brand}</p>
                <p className="text-[8px] text-slate-700 mt-2">{device.description}</p>
                <div className="mt-5 w-full space-y-2">
                  <button onClick={() => toggleConnection(device.id)}
                    className={`w-full py-2.5 rounded-xl text-[8px] font-black uppercase tracking-widest transition border ${
                      isConnected
                        ? 'bg-rose-500/10 border-rose-500/20 text-rose-400 hover:bg-rose-500/20'
                        : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20'
                    }`}>
                    {isConnected ? 'Disconnect' : 'Connect'}
                  </button>
                  {isConnected && (
                    <button onClick={() => handleSync(device.id)} disabled={syncing === device.id}
                      className="w-full py-2 rounded-xl bg-white/[0.03] border border-white/5 text-slate-500 hover:text-white text-[8px] font-black uppercase tracking-widest transition disabled:opacity-50 flex items-center justify-center space-x-1.5">
                      {syncing === device.id ? <Loader2 size={10} className="animate-spin" /> : <RefreshCw size={10} />}
                      <span>{syncing === device.id ? 'Syncing...' : 'Sync Now'}</span>
                    </button>
                  )}
                </div>
                {isConnected && conn?.lastSync && (
                  <p className="text-[7px] text-slate-700 mt-3">Last sync: {timeAgo(conn.lastSync)}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Today's metrics */}
      {connectedCount > 0 && (
        <>
          <div className="glass-panel rounded-[2.5rem] border border-white/5 p-6">
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-5 flex items-center space-x-2">
              <Activity size={14} />
              <span>Today's Aggregated Metrics</span>
            </p>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {todayData.map(s => (
                <button key={s.label} onClick={() => setSelectedMetric(s.metric)}
                  className={`p-4 rounded-2xl border transition-all text-center ${
                    selectedMetric === s.metric
                      ? 'bg-white/[0.05] border-white/20'
                      : 'bg-white/[0.02] border-white/5 hover:border-white/10'
                  }`}>
                  <s.icon size={18} className={`mx-auto mb-2 ${s.color}`} />
                  <p className={`text-2xl font-black ${s.color}`}>{s.value}<span className="text-xs text-slate-600 ml-0.5">{s.unit}</span></p>
                  <p className="text-[8px] text-slate-600 font-black uppercase tracking-widest mt-1">{s.label}</p>
                </button>
              ))}
            </div>
          </div>

          {/* 7-day chart */}
          <div className="glass-panel rounded-[2.5rem] border border-white/5 p-8">
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-6">
              {METRIC_LABELS[selectedMetric] || 'Metrics'} — 7 Days
            </p>
            <div className="h-72">
              <ResponsiveContainer>
                <AreaChart data={DAYS_7_DATA}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                  <XAxis dataKey="day" tick={{ fontSize: 10, fill: '#64748b' }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: '#64748b' }} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', fontSize: '10px', color: '#e2e8f0' }} />
                  <defs>
                    <linearGradient id="wearableGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={METRIC_COLORS[selectedMetric] || '#10b981'} stopOpacity={0.3} />
                      <stop offset="100%" stopColor={METRIC_COLORS[selectedMetric] || '#10b981'} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <Area type="monotone" dataKey={selectedMetric} stroke={METRIC_COLORS[selectedMetric] || '#10b981'} fill="url(#wearableGradient)" strokeWidth={2.5} dot={{ fill: METRIC_COLORS[selectedMetric] || '#10b981', r: 4 }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="flex items-center justify-center space-x-3 mt-4">
              {['steps', 'hr', 'sleep', 'hrv', 'spo2', 'calories'].map(m => (
                <button key={m} onClick={() => setSelectedMetric(m)}
                  className={`px-3 py-1.5 rounded-lg text-[7px] font-black uppercase tracking-widest transition ${
                    selectedMetric === m ? 'bg-white/10 text-white' : 'text-slate-600 hover:text-slate-400'
                  }`}>{m}</button>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Empty state */}
      {connectedCount === 0 && (
        <div className="glass-panel rounded-[2.5rem] p-16 border border-white/5 text-center">
          <Bluetooth size={48} className="mx-auto text-slate-600 mb-4" />
          <p className="text-lg font-black text-slate-500 uppercase tracking-wider">No devices connected</p>
          <p className="text-[10px] font-black text-slate-600 mt-2 uppercase tracking-widest">Connect Apple Health, Garmin, Fitbit, Whoop, or Oura</p>
        </div>
      )}
    </div>
  );
};

export default WearableIntegrations;
