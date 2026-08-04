import React, { useState } from 'react';
import { Zap, Clock, Dumbbell, PlayCircle, CheckCircle2, Circle, Timer, StopCircle, Loader2, Target, Trophy } from 'lucide-react';
import { logWorkoutSetProgress } from '../services/apiService';
import { useCurrentUserId } from '../hooks/useCurrentUserId';

interface QuickExercise {
  name: string;
  reps: string;
  sets: number;
  muscle: string;
}

interface WorkoutTemplate {
  id: string;
  name: string;
  description: string;
  duration: number;
  difficulty: string;
  goal: string;
  exercises: QuickExercise[];
  icon: string;
}

const TEMPLATES: WorkoutTemplate[] = [
  {
    id: 'fullbody_15', name: 'Full Body Express', description: 'Hit every major muscle group fast', duration: 15, difficulty: 'Beginner', goal: 'general',
    icon: 'Zap', exercises: [
      { name: 'Bodyweight Squats', reps: '15', sets: 3, muscle: 'Legs' },
      { name: 'Push-ups', reps: '10', sets: 3, muscle: 'Chest' },
      { name: 'Plank', reps: '30s', sets: 3, muscle: 'Core' },
      { name: 'Glute Bridges', reps: '12', sets: 3, muscle: 'Glutes' },
    ]
  },
  {
    id: 'fullbody_30', name: 'Full Body', description: 'Complete full body workout', duration: 30, difficulty: 'Intermediate', goal: 'general',
    icon: 'Zap', exercises: [
      { name: 'Bodyweight Squats', reps: '20', sets: 3, muscle: 'Legs' },
      { name: 'Push-ups', reps: '15', sets: 3, muscle: 'Chest' },
      { name: 'Lunges', reps: '12 each', sets: 3, muscle: 'Legs' },
      { name: 'Diamond Push-ups', reps: '10', sets: 3, muscle: 'Triceps' },
      { name: 'Bicycle Crunches', reps: '20', sets: 3, muscle: 'Core' },
      { name: 'Plank to Downward Dog', reps: '10', sets: 3, muscle: 'Full Body' },
    ]
  },
  {
    id: 'upper_20', name: 'Upper Body Pump', description: 'Upper body strength in 20 min', duration: 20, difficulty: 'Intermediate', goal: 'muscle_gain',
    icon: 'Dumbbell', exercises: [
      { name: 'Push-ups', reps: '15', sets: 4, muscle: 'Chest' },
      { name: 'Tricep Dips (Chair)', reps: '12', sets: 3, muscle: 'Triceps' },
      { name: 'Wide Push-ups', reps: '12', sets: 3, muscle: 'Chest/Shoulders' },
      { name: 'Superman Hold', reps: '20s', sets: 3, muscle: 'Back' },
      { name: 'Plank to Push-up', reps: '10', sets: 3, muscle: 'Full Upper' },
    ]
  },
  {
    id: 'lower_20', name: 'Lower Body Burn', description: 'Leg day express', duration: 20, difficulty: 'Intermediate', goal: 'muscle_gain',
    icon: 'Target', exercises: [
      { name: 'Bodyweight Squats', reps: '25', sets: 3, muscle: 'Quads' },
      { name: 'Reverse Lunges', reps: '12 each', sets: 3, muscle: 'Glutes' },
      { name: 'Glute Bridges', reps: '15', sets: 3, muscle: 'Glutes' },
      { name: 'Calf Raises', reps: '20', sets: 3, muscle: 'Calves' },
      { name: 'Wall Sit', reps: '45s', sets: 2, muscle: 'Quads' },
    ]
  },
  {
    id: 'cardio_15', name: 'Cardio Blast', description: 'Get your heart rate up fast', duration: 15, difficulty: 'Beginner', goal: 'weight_loss',
    icon: 'Zap', exercises: [
      { name: 'High Knees', reps: '30s', sets: 3, muscle: 'Cardio' },
      { name: 'Jumping Jacks', reps: '30s', sets: 3, muscle: 'Cardio' },
      { name: 'Burpees', reps: '10', sets: 3, muscle: 'Full Body' },
      { name: 'Mountain Climbers', reps: '30s', sets: 3, muscle: 'Cardio' },
      { name: 'Butt Kicks', reps: '30s', sets: 3, muscle: 'Cardio' },
    ]
  },
  {
    id: 'hiit_20', name: 'HIIT Circuit', description: 'High intensity interval training', duration: 20, difficulty: 'Advanced', goal: 'weight_loss',
    icon: 'Zap', exercises: [
      { name: 'Burpees', reps: '45s', sets: 4, muscle: 'Full Body' },
      { name: 'Mountain Climbers', reps: '45s', sets: 4, muscle: 'Core' },
      { name: 'Jump Squats', reps: '45s', sets: 4, muscle: 'Legs' },
      { name: 'Plank Jacks', reps: '45s', sets: 4, muscle: 'Core' },
    ]
  },
  {
    id: 'core_15', name: 'Core Crusher', description: 'Strengthen your midsection', duration: 15, difficulty: 'Beginner', goal: 'general',
    icon: 'Target', exercises: [
      { name: 'Plank', reps: '45s', sets: 3, muscle: 'Core' },
      { name: 'Bicycle Crunches', reps: '20', sets: 3, muscle: 'Core' },
      { name: 'Russian Twists', reps: '20', sets: 3, muscle: 'Obliques' },
      { name: 'Leg Raises', reps: '12', sets: 3, muscle: 'Lower Core' },
      { name: 'Dead Bug', reps: '10 each', sets: 3, muscle: 'Core' },
    ]
  },
  {
    id: 'morning_10', name: 'Morning Stretch', description: 'Wake up your body', duration: 10, difficulty: 'Beginner', goal: 'general',
    icon: 'Dumbbell', exercises: [
      { name: 'Cat-Cow Stretch', reps: '10', sets: 2, muscle: 'Spine' },
      { name: 'Downward Dog', reps: '30s', sets: 2, muscle: 'Full Body' },
      { name: 'Standing Toe Touch', reps: '15', sets: 2, muscle: 'Hamstrings' },
      { name: 'Shoulder Rolls', reps: '10 each', sets: 2, muscle: 'Shoulders' },
      { name: 'Neck Stretch', reps: '15s each', sets: 2, muscle: 'Neck' },
    ]
  },
];

const QuickWorkout: React.FC = () => {
  const userId = useCurrentUserId();
  const [selectedTemplate, setSelectedTemplate] = useState<WorkoutTemplate | null>(null);
  const [sessionActive, setSessionActive] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [completed, setCompleted] = useState<Set<number>>(new Set());
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [goalFilter, setGoalFilter] = useState<string>('all');
  const [durationFilter, setDurationFilter] = useState<number>(0);

  React.useEffect(() => {
    if (!sessionActive) return;
    const interval = setInterval(() => setElapsed(prev => prev + 1), 1000);
    return () => clearInterval(interval);
  }, [sessionActive]);

  const filtered = TEMPLATES.filter(t => {
    if (goalFilter !== 'all' && t.goal !== goalFilter) return false;
    if (durationFilter > 0 && t.duration !== durationFilter) return false;
    return true;
  });

  const startSession = () => {
    setSessionActive(true);
    setElapsed(0);
    setCompleted(new Set());
    setSaved(false);
  };

  const toggleExercise = (idx: number) => {
    setCompleted(prev => {
      const next = new Set(prev);
      next.has(idx) ? next.delete(idx) : next.add(idx);
      return next;
    });
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60).toString().padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const completeSession = () => {
    setSaving(true);
    const calsBurned = Math.round(elapsed * 0.12 * (selectedTemplate?.exercises.length || 1));
    const session = {
      name: selectedTemplate?.name || 'Quick Workout',
      duration: Math.round(elapsed / 60) || selectedTemplate?.duration || 15,
      caloriesBurned: calsBurned,
      exercisesCompleted: completed.size,
      exercisesTotal: selectedTemplate?.exercises.length || 0,
      timestamp: new Date().toISOString(),
      goal: selectedTemplate?.goal || 'general',
    };
    fetch(`${API_BASE}/api/workouts/log`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: Number(userId),
        workout_name: session.name,
        duration_minutes: session.duration,
        calories_burned: session.caloriesBurned,
        exercises_data: {
          total: session.exercisesTotal,
          completed: session.exercisesCompleted,
          exercises: selectedTemplate?.exercises.map((ex, i) => ({
            name: ex.name,
            sets: ex.sets,
            reps: ex.reps,
            completed: completed.has(i),
          })) || [],
        },
      }),
    }).finally(async () => {
      await logWorkoutSetProgress(String(userId), {
        sets_added: completed.size,
        workout_planned_id: null
      });
      setSessionActive(false);
      setSaving(false);
      setSaved(true);
    });
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="flex items-center space-x-6">
        <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/20 rounded-3xl flex items-center justify-center text-emerald-400">
          <Zap size={32} />
        </div>
        <div>
          <h2 className="text-4xl font-black italic tracking-tighter text-white uppercase">Quick Workouts</h2>
          <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Pre-built sessions for any timeframe</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 items-center">
        <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest mr-2">Filter:</span>
        <div className="flex bg-slate-900 border border-white/10 rounded-2xl p-1">
          {['all', 'weight_loss', 'muscle_gain', 'general'].map(g => (
            <button key={g} onClick={() => setGoalFilter(g)}
              className={`px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all ${goalFilter === g ? 'bg-emerald-500 text-slate-950' : 'text-slate-500 hover:text-emerald-400'}`}>
              {g === 'all' ? 'All Goals' : g.replace('_', ' ')}
            </button>
          ))}
        </div>
        <div className="flex bg-slate-900 border border-white/10 rounded-2xl p-1">
          {[0, 10, 15, 20, 30].map(d => (
            <button key={d} onClick={() => setDurationFilter(d)}
              className={`px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all ${durationFilter === d ? 'bg-emerald-500 text-slate-950' : 'text-slate-500 hover:text-emerald-400'}`}>
              {d === 0 ? 'Any' : `${d}m`}
            </button>
          ))}
        </div>
      </div>

      {/* Template Grid or Active Session */}
      {!sessionActive && !saved && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 stagger-children">
          {filtered.map(t => (
            <button key={t.id} onClick={() => { setSelectedTemplate(t); }}
              className={`p-6 rounded-2xl border text-left transition-all card-hover ${selectedTemplate?.id === t.id ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-slate-900 border-white/5 hover:border-emerald-500/20'}`}>
              <div className="flex items-start justify-between mb-4">
                <div className="w-10 h-10 bg-emerald-500/10 rounded-xl flex items-center justify-center text-emerald-400">
                  <Clock size={18} />
                </div>
                <span className="text-xs font-black text-emerald-400">{t.duration} min</span>
              </div>
              <h3 className="text-base font-black text-white">{t.name}</h3>
              <p className="text-[10px] text-slate-400 mt-1">{t.description}</p>
              <div className="flex items-center space-x-2 mt-4">
                <span className="text-[8px] font-black px-2 py-1 rounded bg-slate-800 text-slate-500 uppercase">{t.difficulty}</span>
                <span className="text-[8px] font-black px-2 py-1 rounded bg-slate-800 text-slate-500 uppercase">{t.exercises.length} moves</span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Selected template preview */}
      {selectedTemplate && !sessionActive && !saved && (
        <div className="glass-panel p-8 rounded-[2.5rem] border border-emerald-500/20">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-2xl font-black text-white italic">{selectedTemplate.name}</h3>
              <p className="text-xs text-slate-400 mt-1">{selectedTemplate.description}</p>
            </div>
            <button onClick={startSession}
              className="flex items-center space-x-2 px-8 py-4 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest transition shadow-[0_8px_25px_rgba(16,185,129,0.3)]">
              <PlayCircle size={18} />
              <span>Start</span>
            </button>
          </div>
          <div className="space-y-2">
            {selectedTemplate.exercises.map((ex, i) => (
              <div key={i} className="flex items-center justify-between p-4 bg-slate-950/50 rounded-xl border border-white/5">
                <div className="flex items-center space-x-3">
                  <span className="text-lg font-black text-slate-800 italic">{String(i + 1).padStart(2, '0')}</span>
                  <div>
                    <p className="text-sm font-black text-white">{ex.name}</p>
                    <p className="text-[9px] text-slate-500">{ex.muscle}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-black text-emerald-400">{ex.reps}</p>
                  <p className="text-[9px] text-slate-500">{ex.sets} sets</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active Session */}
      {sessionActive && selectedTemplate && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="px-5 py-3 bg-slate-900 border border-emerald-500/30 rounded-2xl flex items-center space-x-3">
                <Timer size={18} className="text-emerald-400 animate-pulse" />
                <span className="text-2xl font-black text-white font-mono">{formatTime(elapsed)}</span>
              </div>
              <div className="text-sm text-slate-500">
                <span className="text-emerald-400 font-black">{completed.size}</span>/{selectedTemplate.exercises.length} completed
              </div>
            </div>
            <button onClick={completeSession} disabled={saving || completed.size === 0}
              className="px-6 py-3 bg-orange-500 hover:bg-orange-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest flex items-center space-x-2 transition">
              {saving ? <Loader2 size={16} className="animate-spin" /> : <StopCircle size={16} />}
              <span>Complete Workout</span>
            </button>
          </div>

          <div className="glass-panel rounded-[2.5rem] border border-white/5 overflow-hidden">
            <div className="space-y-0 divide-y divide-white/5">
              {selectedTemplate.exercises.map((ex, i) => {
                const done = completed.has(i);
                return (
                  <div key={i} onClick={() => toggleExercise(i)}
                    className={`flex items-center justify-between p-6 cursor-pointer transition-all ${done ? 'bg-emerald-500/5' : 'hover:bg-white/[0.02]'}`}>
                    <div className="flex items-center space-x-4">
                      {done ? <CheckCircle2 size={24} className="text-emerald-400" /> : <Circle size={24} className="text-slate-700" />}
                      <div>
                        <p className={`text-sm font-black italic uppercase ${done ? 'text-emerald-400/50 line-through' : 'text-white'}`}>{ex.name}</p>
                        <p className="text-[9px] text-slate-500">{ex.muscle}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-sm font-black ${done ? 'text-emerald-400/50' : 'text-emerald-400'}`}>{ex.reps}</p>
                      <p className="text-[9px] text-slate-500">{ex.sets} sets</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Saved banner */}
      {saved && (
        <div className="p-8 bg-emerald-500/10 border border-emerald-500/30 rounded-3xl text-center">
          <CheckCircle2 size={40} className="mx-auto mb-3 text-emerald-400" />
          <p className="text-xl font-black text-emerald-400 uppercase tracking-widest">Workout Complete!</p>
          <p className="text-sm text-slate-400 mt-1">{completed.size} exercises • {formatTime(elapsed)}</p>
          <div className="flex justify-center space-x-4 mt-6">
            <button onClick={() => { setSelectedTemplate(null); setSaved(false); }}
              className="px-6 py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest transition">
              Pick Another
            </button>
            <button onClick={() => { setSaved(false); setSelectedTemplate(null); }}
              className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded-2xl font-black text-[10px] uppercase tracking-widest transition">
              Back to List
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuickWorkout;
