import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Pause, StopCircle, MapPin, Route, Timer, Zap, TrendingUp, Footprints, Flame, ChevronDown, ChevronUp, Trash2, Check } from 'lucide-react';
import { useUserProfile } from '../hooks/useUserProfile';

const STORAGE_KEY = 'smarty_activity_logs';

interface TrackPoint {
  lat: number;
  lng: number;
  timestamp: number;
}

interface ActivitySession {
  id: string;
  date: string;
  type: 'running' | 'walking' | 'hiking';
  duration: number;
  distanceKm: number;
  calories: number;
  avgPace: string;
  avgSpeed: number;
  route: TrackPoint[];
  label?: string;
}

function haversineKm(p1: TrackPoint, p2: TrackPoint): number {
  const R = 6371;
  const dLat = (p2.lat - p1.lat) * Math.PI / 180;
  const dLng = (p2.lng - p1.lng) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(p1.lat * Math.PI / 180) * Math.cos(p2.lat * Math.PI / 180) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function formatPace(speedKmh: number): string {
  if (speedKmh <= 0) return '--:--';
  const minPerKm = 60 / speedKmh;
  const m = Math.floor(minPerKm);
  const s = Math.round((minPerKm - m) * 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function estimateCalories(durationMin: number, speedKmh: number, weightKg: number): number {
  const met = speedKmh < 5 ? 3.5 : speedKmh < 8 ? 6.0 : speedKmh < 10 ? 8.0 : speedKmh < 12 ? 10.0 : 12.0;
  return Math.round(met * weightKg * (durationMin / 60));
}

const ActivityTracker: React.FC = () => {
  const { profile } = useUserProfile();
  const [activities, setActivities] = useState<ActivitySession[]>(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); } catch { return []; }
  });
  const [tracking, setTracking] = useState(false);
  const [paused, setPaused] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [distance, setDistance] = useState(0);
  const [route, setRoute] = useState<TrackPoint[]>([]);
  const [currentSpeed, setCurrentSpeed] = useState(0);
  const [activityType, setActivityType] = useState<'running' | 'walking' | 'hiking'>('running');
  const [expandHistory, setExpandHistory] = useState(true);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [label, setLabel] = useState('');
  const [labelInput, setLabelInput] = useState('');
  const [showFinishConfirm, setShowFinishConfirm] = useState(false);

  const watchId = useRef<number | null>(null);
  const startTime = useRef<number>(0);
  const lastPoint = useRef<TrackPoint | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animFrame = useRef<number>(0);

  useEffect(() => { localStorage.setItem(STORAGE_KEY, JSON.stringify(activities)); }, [activities]);

  // Timer
  useEffect(() => {
    if (!tracking || paused) return;
    const interval = setInterval(() => { setElapsed(Math.floor((Date.now() - startTime.current) / 1000)); }, 1000);
    return () => clearInterval(interval);
  }, [tracking, paused]);

  // Draw route on canvas
  const drawRoute = useCallback(() => {
    if (!canvasRef.current || route.length < 2) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = canvas.clientWidth * dpr;
    canvas.height = canvas.clientHeight * dpr;
    ctx.scale(dpr, dpr);
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    ctx.clearRect(0, 0, w, h);

    const lats = route.map(p => p.lat);
    const lngs = route.map(p => p.lng);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);
    const pad = 30;
    const scaleX = (w - pad * 2) / (maxLng - minLng || 1);
    const scaleY = (h - pad * 2) / (maxLat - minLat || 1);
    const scale = Math.min(scaleX, scaleY);

    const points = route.map(p => ({
      x: pad + (p.lng - minLng) * scale,
      y: h - pad - (p.lat - minLat) * scale,
    }));

    // Grid dots
    ctx.fillStyle = 'rgba(255,255,255,0.03)';
    for (let x = 0; x < w; x += 40) {
      for (let y = 0; y < h; y += 40) {
        ctx.beginPath(); ctx.arc(x, y, 1, 0, Math.PI * 2); ctx.fill();
      }
    }

    // Route line
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i].x, points[i].y);
    }
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.shadowColor = 'rgba(16,185,129,0.4)';
    ctx.shadowBlur = 8;
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Start point
    ctx.beginPath();
    ctx.arc(points[0].x, points[0].y, 5, 0, Math.PI * 2);
    ctx.fillStyle = '#34d399';
    ctx.fill();
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Current point
    const last = points[points.length - 1];
    ctx.beginPath();
    ctx.arc(last.x, last.y, 6, 0, Math.PI * 2);
    ctx.fillStyle = '#f59e0b';
    ctx.fill();
    ctx.shadowColor = 'rgba(245,158,11,0.6)';
    ctx.shadowBlur = 12;
    ctx.strokeStyle = '#fbbf24';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Labels
    ctx.fillStyle = 'rgba(255,255,255,0.15)';
    ctx.font = '8px sans-serif';
    ctx.fillText('S', points[0].x - 3, points[0].y + 14);
    ctx.fillText('NOW', last.x - 7, last.y - 12);
  }, [route]);

  useEffect(() => { drawRoute(); }, [drawRoute]);

  const handleGeoSuccess = useCallback((pos: GeolocationPosition) => {
    const point: TrackPoint = { lat: pos.coords.latitude, lng: pos.coords.longitude, timestamp: pos.timestamp };
    setCurrentSpeed(pos.coords.speed && pos.coords.speed > 0 ? pos.coords.speed * 3.6 : 0);
    setRoute(prev => {
      const updated = [...prev, point];
      if (lastPoint.current) {
        setDistance(d => d + haversineKm(lastPoint.current, point));
      }
      lastPoint.current = point;
      return updated;
    });
  }, []);

  const startTracking = () => {
    if (!navigator.geolocation) return;
    setTracking(true);
    setPaused(false);
    setElapsed(0);
    setDistance(0);
    setRoute([]);
    setCurrentSpeed(0);
    lastPoint.current = null;
    startTime.current = Date.now();
    watchId.current = navigator.geolocation.watchPosition(handleGeoSuccess, () => {}, {
      enableHighAccuracy: true, timeout: 5000, maximumAge: 0,
    });
  };

  const togglePause = () => {
    if (paused) {
      startTime.current = Date.now() - elapsed * 1000;
      watchId.current = navigator.geolocation.watchPosition(handleGeoSuccess, () => {}, {
        enableHighAccuracy: true, timeout: 5000, maximumAge: 0,
      });
    } else if (watchId.current !== null) {
      navigator.geolocation.clearWatch(watchId.current);
      watchId.current = null;
    }
    setPaused(!paused);
  };

  const finishActivity = () => {
    if (watchId.current !== null) navigator.geolocation.clearWatch(watchId.current);
    watchId.current = null;
    setTracking(false);
    setPaused(false);
    const durationMin = elapsed / 60;
    const avgSpeed = durationMin > 0 ? (distance / (durationMin / 60)) : 0;
    const weight = profile.weight_kg || 75;
    const session: ActivitySession = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      date: new Date().toISOString(),
      type: activityType,
      duration: elapsed,
      distanceKm: distance,
      calories: estimateCalories(durationMin, avgSpeed, weight),
      avgPace: formatPace(avgSpeed),
      avgSpeed: Math.round(avgSpeed * 10) / 10,
      route,
      label: labelInput.trim() || undefined,
    };
    setActivities(prev => [session, ...prev]);
    setShowFinishConfirm(false);
    setLabelInput('');
  };

  const discardActivity = () => {
    if (watchId.current !== null) navigator.geolocation.clearWatch(watchId.current);
    watchId.current = null;
    setTracking(false);
    setPaused(false);
    setElapsed(0);
    setDistance(0);
    setRoute([]);
    setCurrentSpeed(0);
    lastPoint.current = null;
    setShowFinishConfirm(false);
  };

  const deleteActivity = (id: string) => {
    if (deleteConfirm === id) {
      setActivities(prev => prev.filter(a => a.id !== id));
      setDeleteConfirm(null);
    } else {
      setDeleteConfirm(id);
      setTimeout(() => setDeleteConfirm(null), 3000);
    }
  };

  const formatTime = (sec: number) => {
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = sec % 60;
    if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const pace = elapsed > 0 && distance > 0 ? formatPace(distance / (elapsed / 3600)) : '--:--';
  const speedKmh = elapsed > 0 ? distance / (elapsed / 3600) : 0;
  const weightKg = profile.weight_kg || 75;
  const estCalories = tracking ? estimateCalories(elapsed / 60, speedKmh || currentSpeed, weightKg) : 0;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <div className={`w-16 h-16 rounded-3xl flex items-center justify-center transition-colors ${
            tracking ? 'bg-emerald-500/20 border border-emerald-500/30 text-emerald-400' : 'bg-rose-500/10 border border-rose-500/20 text-rose-400'
          }`}>
            {tracking ? <MapPin size={32} /> : <Footprints size={32} />}
          </div>
          <div>
            <h2 className="text-4xl font-black italic tracking-tighter text-white uppercase">Activity Tracker</h2>
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">
              {tracking ? 'Tracking in progress' : 'GPS running & walking'}
            </p>
          </div>
        </div>
        {!tracking && (
          <div className="flex items-center space-x-2">
            {(['running', 'walking', 'hiking'] as const).map(t => (
              <button key={t} onClick={() => setActivityType(t)}
                className={`px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all border ${
                  activityType === t
                    ? 'bg-emerald-500/20 border-emerald-500/30 text-emerald-400'
                    : 'bg-slate-900 border-slate-800 text-slate-500 hover:text-slate-400'
                }`}>
                {t}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Active tracking */}
      {tracking && (
        <div className="glass-panel rounded-[2.5rem] border border-emerald-500/20 overflow-hidden">
          {/* Canvas map */}
          <div className="h-56 bg-slate-950/50 relative">
            <canvas ref={canvasRef} className="w-full h-full" />
            {route.length < 2 && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <MapPin size={32} className="mx-auto text-slate-700 animate-pulse" />
                  <p className="text-[10px] text-slate-600 font-black uppercase tracking-widest mt-2">Waiting for GPS signal...</p>
                </div>
              </div>
            )}
            {paused && (
              <div className="absolute inset-0 bg-slate-950/60 flex items-center justify-center backdrop-blur-sm">
                <p className="text-lg font-black text-amber-400 uppercase tracking-wider">Paused</p>
              </div>
            )}
          </div>

          {/* Stats */}
          <div className="grid grid-cols-4 gap-px bg-white/[0.03]">
            {[
              { label: 'Duration', value: formatTime(elapsed), icon: Timer, color: 'text-emerald-400' },
              { label: 'Distance', value: `${distance.toFixed(2)}`, unit: 'km', icon: Route, color: 'text-blue-400' },
              { label: 'Pace', value: pace, unit: '/km', icon: TrendingUp, color: 'text-amber-400' },
              { label: 'Calories', value: estCalories, unit: 'kcal', icon: Flame, color: 'text-rose-400' },
            ].map((s, i) => (
              <div key={i} className="p-5 text-center">
                <s.icon size={16} className={`mx-auto mb-2 ${s.color}`} />
                <p className="text-xl font-black text-white">{s.value}<span className="text-xs text-slate-600 ml-1">{s.unit}</span></p>
                <p className="text-[7px] text-slate-600 font-black uppercase tracking-widest mt-1">{s.label}</p>
              </div>
            ))}
          </div>

          {/* Controls */}
          <div className="p-5 flex items-center justify-center space-x-6">
            {paused ? (
              <button onClick={togglePause}
                className="w-16 h-16 rounded-full bg-emerald-500 hover:bg-emerald-400 text-slate-950 flex items-center justify-center transition">
                <Play size={24} className="ml-1" />
              </button>
            ) : (
              <button onClick={togglePause}
                className="w-16 h-16 rounded-full bg-amber-500 hover:bg-amber-400 text-slate-950 flex items-center justify-center transition">
                <Pause size={24} />
              </button>
            )}
            <button onClick={() => setShowFinishConfirm(true)}
              className="w-16 h-16 rounded-full bg-rose-500 hover:bg-rose-400 text-slate-950 flex items-center justify-center transition">
              <StopCircle size={24} />
            </button>
          </div>

          {/* Label input */}
          <div className="px-5 pb-5">
            <input value={labelInput} onChange={e => setLabelInput(e.target.value)}
              placeholder="Add a label (e.g. Morning run)"
              className="w-full bg-slate-950 border border-white/10 rounded-xl px-4 py-2.5 text-[10px] text-white placeholder:text-slate-600 font-medium" />
          </div>
        </div>
      )}

      {/* Finish confirm dialog */}
      {showFinishConfirm && (
        <div className="glass-panel rounded-[2.5rem] border border-rose-500/20 bg-rose-500/5 p-6">
          <p className="text-sm font-black text-rose-400 mb-4">Finish this activity?</p>
          <div className="flex items-center space-x-4">
            <button onClick={finishActivity}
              className="px-6 py-3 bg-rose-500 hover:bg-rose-400 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest transition">
              Save & Finish
            </button>
            <button onClick={discardActivity}
              className="px-6 py-3 bg-slate-800 text-slate-400 rounded-2xl font-black text-[10px] uppercase tracking-widest hover:text-white transition">
              Discard
            </button>
            <button onClick={() => setShowFinishConfirm(false)}
              className="text-[10px] text-slate-600 font-black uppercase tracking-widest hover:text-slate-400 transition">
              Continue
            </button>
          </div>
        </div>
      )}

      {/* Start button (when not tracking) */}
      {!tracking && (
        <button onClick={startTracking}
          className="w-full py-6 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-[2.5rem] font-black text-sm uppercase tracking-widest transition flex items-center justify-center space-x-3">
          <Play size={20} />
          <span>Start {activityType}</span>
        </button>
      )}

      {/* History */}
      {activities.length > 0 && (
        <div className="glass-panel rounded-[2.5rem] border border-white/5 overflow-hidden">
          <button onClick={() => setExpandHistory(!expandHistory)}
            className="w-full flex items-center justify-between p-5 hover:bg-white/[0.02] transition">
            <div className="flex items-center space-x-3">
              <Route size={16} className="text-slate-500" />
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                Activity History ({activities.length})
              </p>
            </div>
            {expandHistory ? <ChevronUp size={14} className="text-slate-600" /> : <ChevronDown size={14} className="text-slate-600" />}
          </button>
          {expandHistory && (
            <div className="divide-y divide-white/5">
              {activities.map(a => {
                const date = new Date(a.date);
                return (
                  <div key={a.id} className="flex items-center justify-between p-4 hover:bg-white/[0.02] transition-colors">
                    <div className="flex items-center space-x-4 min-w-0">
                      <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400 shrink-0">
                        <Footprints size={18} />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center space-x-2">
                          <p className="text-xs font-black text-white capitalize">{a.type}</p>
                          <span className="text-[8px] text-slate-600 font-black uppercase">{a.avgPace}/km</span>
                          {a.label && <span className="text-[8px] text-slate-600 italic truncate max-w-[120px]">— {a.label}</span>}
                        </div>
                        <div className="flex items-center space-x-3 mt-0.5">
                          <span className="text-[8px] text-emerald-400 font-black">{a.distanceKm.toFixed(2)} km</span>
                          <span className="text-[8px] text-rose-400 font-black">{a.calories} kcal</span>
                          <span className="text-[8px] text-blue-400 font-black">{formatTime(a.duration)}</span>
                          <span className="text-[8px] text-slate-600">{date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                      </div>
                    </div>
                    <button onClick={() => deleteActivity(a.id)}
                      className="p-2 rounded-xl hover:bg-rose-500/10 text-rose-400/60 hover:text-rose-400 transition shrink-0">
                      {deleteConfirm === a.id ? <Check size={14} /> : <Trash2 size={14} />}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!tracking && activities.length === 0 && (
        <div className="glass-panel rounded-[2.5rem] p-16 border border-white/5 text-center">
          <Footprints size={48} className="mx-auto text-slate-600 mb-4" />
          <p className="text-lg font-black text-slate-500 uppercase tracking-wider">No activities yet</p>
          <p className="text-[10px] font-black text-slate-600 mt-2 uppercase tracking-widest">Hit start to track your first run or walk</p>
        </div>
      )}
    </div>
  );
};

export default ActivityTracker;
