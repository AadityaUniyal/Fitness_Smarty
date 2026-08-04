import React, { useState, useEffect } from 'react';
import {
  Dumbbell, Sparkles, Loader2, CheckCircle2, Circle,
  Timer, BarChart3, Flame, Zap, Target, Trophy, Wrench,
  ClipboardList, Database, PlayCircle, StopCircle, Calendar, Coffee
} from 'lucide-react';
import { generateWorkoutPlan } from '../services/geminiService';
import { WorkoutPlan, BodyGoal } from '../types';
import RestTimer from '../components/RestTimer';
import { logWorkoutSetProgress } from '../services/apiService';
import { useUserProfile } from '../hooks/useUserProfile';
import { useCurrentUserId } from '../hooks/useCurrentUserId';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface WorkoutSession {
  name: string;
  duration: number;
  caloriesBurned: number;
  exercisesCompleted: number;
  exercisesTotal: number;
  timestamp: string;
  goal: string;
}

interface WeeklyPlanDay {
  day: number;
  type: string;
  focus: string;
  exercises: any[];
}

interface WeeklyPlan {
  split_type: string;
  goal: string;
  difficulty: string;
  weekly_plan: WeeklyPlanDay[];
}

const WorkoutAssistant: React.FC = () => {
  const [goal, setGoal] = useState<BodyGoal>(BodyGoal.ATHLETIC);
  const [level, setLevel] = useState('Intermediate');
  const [duration, setDuration] = useState(45);
  const [plan, setPlan] = useState<WorkoutPlan | null>(null);
  const [weeklyPlan, setWeeklyPlan] = useState<WeeklyPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'single' | 'weekly'>('single');
  const [selectedDay, setSelectedDay] = useState(1);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  // Workout session state
  const [sessionActive, setSessionActive] = useState(false);
  const [sessionStart, setSessionStart] = useState<Date | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [completedExercises, setCompletedExercises] = useState<Set<number>>(new Set());
  const [exerciseTracking, setExerciseTracking] = useState<Record<number, { reps: number, sets: number }>>({});
  const [saving, setSaving] = useState(false);
  const [sessionSaved, setSessionSaved] = useState(false);
  const [savedCalories, setSavedCalories] = useState(0);
  const [showRestTimer, setShowRestTimer] = useState(false);
  const [feedbackSent, setFeedbackSent] = useState<Record<string, boolean>>({});
  const { profile } = useUserProfile();
  const userId = useCurrentUserId();

  const handleWorkoutFeedback = async (rating: number) => {
    try {
      const uId = userId;
      await fetch(`${API_BASE}/api/feedback/coach`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          domain: 'exercise',
          item_id: plan?.title || 'workout_session',
          rating,
          context_json: {
            goal: profile.goal || profile.primary_goal,
            gender: profile.gender,
            level,
          }
        })
      });
      setFeedbackSent(prev => ({ ...prev, workout_session: true }));
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (profile.primary_goal || profile.goal) {
      const g = (profile.primary_goal || profile.goal).toLowerCase();
      if (g.includes('loss')) setGoal(BodyGoal.SLIM);
      else if (g.includes('gain')) setGoal(BodyGoal.BULK);
      else if (g.includes('athletic')) setGoal(BodyGoal.ATHLETIC);
      else setGoal(BodyGoal.MAINTAIN);
    }
    if (profile.activityLevel || profile.activity_level) {
      const act = profile.activityLevel || profile.activity_level;
      if (act === 'active' || act === 'very_active') setLevel('Advanced');
      else if (act === 'moderate') setLevel('Intermediate');
      else setLevel('Beginner');
    }

    import('../services/api').then(({ fetchDailyCoach }) => {
      setLoading(true);
      fetchDailyCoach(undefined, async () => null)
        .then(data => {
          if (data && data.workout_recommendation) {
            const rec = data.workout_recommendation;
            if (rec.exercises && rec.exercises.length > 0) {
              setPlan({
                title: `${rec.type} Session (My Coach)`,
                duration: "45 mins",
                intensity: "Medium",
                exercises: rec.exercises.map((ex: any) => ({
                  name: ex.name,
                  sets: ex.sets || 3,
                  reps: ex.reps || "10-12",
                  description: ex.reasoning || "Optimized for your current recovery status.",
                  targeted_muscle: ex.targeted_muscle || ex.muscle || "General",
                  difficulty: ex.difficulty || "Intermediate",
                  equipment: ex.equipment || "Standard"
                })),
                nutrition_advice: {
                  pre_workout: "Sip water and eat a light carb meal before starting.",
                  post_workout: "Aim for 20-30g protein post-session.",
                  recommended_foods: ["Greek Yogurt", "Protein Shake", "Chicken & Rice"],
                  hydration_tip: "Drink at least 500ml water during exercise."
                }
              });
            }
          }
        })
        .catch(() => {})
        .finally(() => setLoading(false));
    });
  }, []);

  // Timer
  useEffect(() => {
    if (!sessionActive) return;
    const interval = setInterval(() => {
      setElapsed(prev => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [sessionActive]);

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60).toString().padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const handleGenerate = async () => {
    setLoading(true);
    setSessionActive(false);
    setSessionSaved(false);
    setCompletedExercises(new Set());
    setElapsed(0);
    setPlan(null);
    setWeeklyPlan(null);

    try {
      if (viewMode === 'weekly') {
        const res = await fetch(`${API_BASE}/api/recommendations/generate-6day-plan?goal=${goal}&difficulty=${level}`);
        const data = await res.json();
        setWeeklyPlan(data);
        // Default to first non-rest day
        const firstDay = data.weekly_plan.find((d: any) => d.type !== 'Rest');
        if (firstDay) setSelectedDay(firstDay.day);
      } else {
        const data = await generateWorkoutPlan(goal, level, duration);
        setPlan(data);
      }
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const startSession = () => {
    setSessionActive(true);
    setSessionStart(new Date());
    setElapsed(0);
    setCompletedExercises(new Set());
    setSessionSaved(false);

    // Initialize tracking with plan values
    const initialTracking: Record<number, { reps: number, sets: number }> = {};
    const exercises = viewMode === 'weekly' ? weeklyPlan?.weekly_plan.find(d => d.day === selectedDay)?.exercises : plan?.exercises;
    exercises?.forEach((ex, i) => {
      const repsStr = ex.reps.includes('-') ? ex.reps.split('-')[1] : ex.reps.replace(/\D/g, '') || '10';
      initialTracking[i] = { reps: parseInt(repsStr), sets: Number(ex.sets) || 3 };
    });
    setExerciseTracking(initialTracking);
  };

  const toggleExerciseDone = (idx: number) => {
    if (!sessionActive) return;
    setCompletedExercises(prev => {
      const next = new Set(prev);
      next.has(idx) ? next.delete(idx) : next.add(idx);
      return next;
    });
  };

  const updateTracking = (idx: number, field: 'reps' | 'sets', val: number) => {
    setExerciseTracking(prev => ({
      ...prev,
      [idx]: { ...prev[idx], [field]: Math.max(0, val) }
    }));
  };

  const calculateCalories = async (): Promise<number> => {
    const exercises = viewMode === 'weekly' ? weeklyPlan?.weekly_plan.find(d => d.day === selectedDay)?.exercises : plan?.exercises;
    if (!exercises) return 0;

    const trackingData = Array.from(completedExercises).map(idx => ({
      exercise_id: exercises[idx].id || 0, // In Gemini-only mode id might be missing, fallback to 0
      reps: exerciseTracking[idx]?.reps || 10,
      sets: exerciseTracking[idx]?.sets || 3
    })).filter(e => e.exercise_id > 0);

    if (trackingData.length === 0) {
      // Fallback to simple estimation if no indexed exercises (Gemini mode)
      let total = 0;
      completedExercises.forEach(idx => {
        const ex = exercises[idx];
        if (!ex) return;
        const track = exerciseTracking[idx];
        const cpm = 8; // Avg
        total += (track.sets * 0.75) * cpm;
      });
      return Math.round(total);
    }

    try {
      const res = await fetch(`${API_BASE}/api/recommendations/calculate-workout-burn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exercises: trackingData })
      });
      const data = await res.json();
      return data.total_burn;
    } catch (e) {
      return 0;
    }
  };

  const handleCompleteWorkout = async () => {
    const exercises = viewMode === 'weekly' ? weeklyPlan?.weekly_plan.find(d => d.day === selectedDay)?.exercises : plan?.exercises;
    if (!exercises || completedExercises.size === 0) return;
    setSaving(true);

    const calsBurned = await calculateCalories();
    const actualDuration = Math.round(elapsed / 60) || duration;
    setSavedCalories(calsBurned);

    const session: WorkoutSession = {
      name: viewMode === 'weekly' ? `Day ${selectedDay}: ${weeklyPlan?.weekly_plan.find(d => d.day === selectedDay)?.type}` : plan?.title || 'Single Session',
      duration: actualDuration,
      caloriesBurned: calsBurned,
      exercisesCompleted: completedExercises.size,
      exercisesTotal: exercises.length,
      timestamp: new Date().toISOString(),
      goal: goal,
    };

    // Sync to backend
    try {
      await fetch(`${API_BASE}/api/workouts/log`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          workout_name: session.name,
          duration_minutes: actualDuration,
          calories_burned: calsBurned,
          exercises_data: {
            total: exercises.length,
            completed: completedExercises.size,
            exercises: exercises.map((ex, i) => ({
              name: ex.name,
              sets: exerciseTracking[i]?.sets,
              reps: exerciseTracking[i]?.reps,
              completed: completedExercises.has(i),
            })),
          },
        }),
      });
      await logWorkoutSetProgress(userId, {
        sets_added: completedExercises.size,
        workout_planned_id: null
      });
    } catch {
      // Silent fail
    }

    setSessionActive(false);
    setSessionSaved(true);
    setSaving(false);
  };

  const currentDayExercises = viewMode === 'weekly' ? weeklyPlan?.weekly_plan.find(d => d.day === selectedDay)?.exercises : plan?.exercises;
  const completionPct = currentDayExercises ? Math.round((completedExercises.size / currentDayExercises.length) * 100) : 0;

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-in slide-in-from-bottom-6 duration-700">

      {/* Config Panel */}
      <div className="glass-panel p-8 rounded-[3rem] border border-emerald-500/20 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-[100px] -mr-32 -mt-32" />
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <div className="p-4 bg-emerald-500 text-slate-950 rounded-3xl shadow-[0_0_20px_rgba(16,185,129,0.3)]">
              <Dumbbell size={28} />
            </div>
            <div>
              <h2 className="text-3xl font-black italic tracking-tighter text-white uppercase">Neural Trainer</h2>
              <p className="text-[10px] font-black uppercase tracking-[0.3em] text-emerald-500">6-Day Split + Advanced Logging</p>
            </div>
          </div>

          <div className="flex bg-slate-950 border border-white/10 rounded-2xl p-1">
            <button onClick={() => setViewMode('single')}
              className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${viewMode === 'single' ? 'bg-emerald-500 text-slate-950' : 'text-slate-500 hover:text-emerald-400'}`}>
              Targeted
            </button>
            <button onClick={() => setViewMode('weekly')}
              className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${viewMode === 'weekly' ? 'bg-emerald-500 text-slate-950' : 'text-slate-500 hover:text-emerald-400'}`}>
              6-Day Split
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-6">
          <div className="space-y-2">
            <label className="flex items-center text-[10px] font-black text-slate-500 uppercase tracking-widest">
              <BarChart3 size={12} className="mr-2" /> Goal
            </label>
            <select value={goal} onChange={e => setGoal(e.target.value as BodyGoal)}
              className="w-full bg-slate-950 border border-white/10 rounded-2xl px-5 py-4 text-xs font-black tracking-widest focus:ring-2 focus:ring-emerald-500/20 outline-none text-emerald-400 uppercase">
              {Object.values(BodyGoal).map(g => <option key={g} value={g}>{g}</option>)}
            </select>
          </div>
          <div className="space-y-2">
            <label className="flex items-center text-[10px] font-black text-slate-500 uppercase tracking-widest">
              <Zap size={12} className="mr-2" /> Level (Difficulty)
            </label>
            <select value={level} onChange={e => setLevel(e.target.value)}
              className="w-full bg-slate-950 border border-white/10 rounded-2xl px-5 py-4 text-xs font-black tracking-widest focus:ring-2 focus:ring-emerald-500/20 outline-none text-emerald-400 uppercase">
              <option>Beginner</option><option>Intermediate</option><option>Advanced</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="flex items-center text-[10px] font-black text-slate-500 uppercase tracking-widest">
              <Timer size={12} className="mr-2" /> {viewMode === 'weekly' ? 'Plan Cycle' : 'Duration (min)'}
            </label>
            <div className="flex bg-slate-950 border border-white/10 rounded-2xl px-5 py-4 text-xs font-black tracking-widest text-emerald-400">
              {viewMode === 'weekly' ? '6 DAYS ACTIVE / 1 REST' : (
                <input type="number" value={duration} onChange={e => setDuration(Number(e.target.value))} min={15} max={120} className="bg-transparent w-full outline-none" />
              )}
            </div>
          </div>
        </div>

        <button onClick={handleGenerate} disabled={loading}
          className="w-full bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-800 text-slate-950 font-black py-5 rounded-3xl transition-all flex items-center justify-center space-x-3 shadow-[0_10px_30px_rgba(16,185,129,0.2)]">
          {loading ? <Loader2 className="animate-spin" size={20} /> : <Sparkles size={20} />}
          <span className="uppercase tracking-[0.2em] text-sm">{loading ? 'Syncing with Neural Vault...' : (viewMode === 'weekly' ? 'Generate 6-Day Protocol' : 'Generate Hybrid Session')}</span>
        </button>
      </div>

      {/* 6-Day Plan Tabs */}
      {viewMode === 'weekly' && weeklyPlan && (
        <div className="flex flex-wrap gap-2 px-2 animate-in fade-in duration-500">
          {weeklyPlan.weekly_plan.map(d => (
            <button key={d.day} onClick={() => { setSelectedDay(d.day); setCompletedExercises(new Set()); setSessionActive(false); }}
              className={`px-4 py-3 rounded-2xl border font-black text-[10px] uppercase tracking-widest transition-all ${selectedDay === d.day ? 'bg-emerald-500 border-emerald-500 text-slate-950 shadow-[0_5px_15px_rgba(16,185,129,0.3)]' : 'bg-slate-950 border-white/5 text-slate-500 hover:border-emerald-500/30'}`}>
              Day {d.day} <span className="block text-[8px] opacity-60 font-medium">{d.type}</span>
            </button>
          ))}
        </div>
      )}

      {/* Session Success Banner */}
      {sessionSaved && (
        <div className="p-6 bg-emerald-500/10 border border-emerald-500/30 rounded-3xl flex flex-col md:flex-row items-center justify-between gap-4 animate-in slide-in-from-top-4 duration-500">
          <div className="flex items-center space-x-4">
            <CheckCircle2 size={28} className="text-emerald-400" />
            <div>
              <p className="text-lg font-black text-emerald-400 uppercase tracking-widest">Session Logged!</p>
              <p className="text-sm text-slate-400">{completedExercises.size} movements archived • {formatTime(elapsed)} elapsed</p>
              
              {/* Feedback controls */}
              <div className="mt-2 flex items-center space-x-3">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">How was this workout recommendation?</span>
                {feedbackSent['workout_session'] ? (
                  <span className="text-[9px] font-black text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">Saved</span>
                ) : (
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleWorkoutFeedback(5)}
                      className="p-1 hover:bg-emerald-500/10 rounded-lg text-slate-400 hover:text-emerald-400 transition"
                      title="Awesome"
                    >
                      👍
                    </button>
                    <button
                      onClick={() => handleWorkoutFeedback(1)}
                      className="p-1 hover:bg-rose-500/10 rounded-lg text-slate-400 hover:text-rose-400 transition"
                      title="Needs changes"
                    >
                      👎
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
          <div className="text-right">
            <p className="text-3xl font-black text-orange-400">{savedCalories}</p>
            <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">kcal burned</p>
          </div>
        </div>
      )}

      {(plan || (weeklyPlan && currentDayExercises)) && (
        <div className="space-y-6 animate-in fade-in zoom-in-95 duration-700">
          {/* Plan header + session controls */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 px-2">
            <div>
              <div className="flex items-center space-x-3 mb-1">
                <span className="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 text-[8px] font-black uppercase tracking-widest rounded border border-emerald-500/20">
                  {viewMode === 'weekly' ? level : plan?.intensity} Intensity
                </span>
                <span className="px-2 py-0.5 bg-cyan-500/10 text-cyan-400 text-[8px] font-black uppercase tracking-widest rounded border border-cyan-500/20">
                  {viewMode === 'weekly' ? weeklyPlan?.weekly_plan.find(d => d.day === selectedDay)?.focus : plan?.duration}
                </span>
              </div>
              <h3 className="text-3xl font-black italic text-white tracking-tighter uppercase">
                {viewMode === 'weekly' ? `Day ${selectedDay}: ${weeklyPlan?.weekly_plan.find(d => d.day === selectedDay)?.type} Focus` : plan?.title}
              </h3>
            </div>

            <div className="flex items-center space-x-3">
              {(viewMode === 'single' || (weeklyPlan?.weekly_plan.find(d => d.day === selectedDay)?.type !== 'Rest')) && !sessionActive && !sessionSaved && (
                <button onClick={startSession}
                  className="px-6 py-3 bg-emerald-500 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest flex items-center space-x-2 hover:bg-emerald-400 transition shadow-[0_8px_20px_rgba(16,185,129,0.3)]">
                  <PlayCircle size={16} />
                  <span>Start Live Tracking</span>
                </button>
              )}

              {sessionActive && (
                <>
                  <div className="flex items-center space-x-2 px-4 py-3 bg-slate-900 border border-white/10 rounded-2xl">
                    <Timer size={14} className="text-emerald-400 animate-pulse" />
                    <span className="text-sm font-black text-white font-mono">{formatTime(elapsed)}</span>
                  </div>
                  <button
                    onClick={() => setShowRestTimer(true)}
                    className="px-4 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-2xl font-black text-[10px] uppercase tracking-widest flex items-center space-x-2 transition border border-white/10"
                  >
                    <Coffee size={14} />
                    <span>Rest</span>
                  </button>
                  <button onClick={handleCompleteWorkout} disabled={saving || completedExercises.size === 0}
                    className="px-6 py-3 bg-orange-500 hover:bg-orange-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest flex items-center space-x-2 transition shadow-[0_8px_20px_rgba(249,115,22,0.3)]">
                    {saving ? <Loader2 size={16} className="animate-spin" /> : <StopCircle size={16} />}
                    <span>{saving ? 'Archiving...' : `Sync Workout (${completedExercises.size}/${currentDayExercises?.length})`}</span>
                  </button>
                </>
              )}
              {showRestTimer && <RestTimer onClose={() => setShowRestTimer(false)} />}
            </div>
          </div>

          {/* Session progress bar */}
          {sessionActive && (
            <div className="px-2">
              <div className="flex items-center justify-between mb-2">
                <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">Neural Sync Progress</p>
                <p className="text-[9px] font-black text-emerald-400">{completionPct}% complete</p>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-linear-to-r from-emerald-500 to-cyan-400 rounded-full transition-all duration-500"
                  style={{ width: `${completionPct}%` }} />
              </div>
            </div>
          )}

          {/* Exercise list */}
          <div className="glass-panel rounded-[2.5rem] border border-white/5 overflow-hidden">
            <div className="hidden md:grid grid-cols-12 gap-4 px-8 py-5 border-b border-white/5 bg-slate-900/50">
              {sessionActive && <div className="col-span-1 text-[10px] font-black text-slate-500 uppercase tracking-widest">Done</div>}
              <div className={`${sessionActive ? 'col-span-3' : 'col-span-4'} text-[10px] font-black text-slate-500 uppercase tracking-widest`}>Movement</div>
              <div className="col-span-2 text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center"><Target size={10} className="mr-1" /> Muscle</div>
              <div className="col-span-2 text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center"><Trophy size={10} className="mr-1" /> Difficulty</div>
              <div className="col-span-2 text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center"><Wrench size={10} className="mr-1" /> Equipment</div>
              <div className="col-span-2 text-[10px] font-black text-slate-500 uppercase tracking-widest text-right">Targets</div>
            </div>

            <div className="divide-y divide-white/5">
              {currentDayExercises?.map((ex: any, idx: number) => {
                const done = completedExercises.has(idx);
                return (
                  <div key={idx}>
                    <div
                      className={`group transition-all p-6 md:p-8 ${done ? 'bg-emerald-500/5' : 'hover:bg-white/2'} ${sessionActive ? 'cursor-pointer' : ''}`}
                      onClick={() => { if (sessionActive) toggleExerciseDone(idx); else setExpandedIdx(expandedIdx === idx ? null : idx); }}
                    >
                      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
                        {sessionActive && (
                          <div className="md:col-span-1 flex items-center">
                            {done
                              ? <CheckCircle2 size={24} className="text-emerald-400 shrink-0" />
                              : <Circle size={24} className="text-slate-700 shrink-0 group-hover:text-slate-500 transition" />
                            }
                          </div>
                        )}

                        <div className={`${sessionActive ? 'md:col-span-3' : 'md:col-span-4'} flex items-center space-x-3`}>
                          <span className="text-lg font-black text-slate-800 italic">{String(idx + 1).padStart(2, '0')}</span>
                          <div>
                            <p className={`text-sm font-black italic uppercase tracking-tight transition-colors ${done ? 'text-emerald-400 line-through opacity-60' : 'text-white group-hover:text-emerald-400'}`}>
                              {ex.name}
                            </p>
                          </div>
                        </div>

                        <div className="md:col-span-2">
                          <span className="text-[9px] font-black text-cyan-400 uppercase bg-cyan-500/5 border border-cyan-500/10 px-3 py-1.5 rounded-xl flex items-center w-fit">
                            <Target size={10} className="mr-1.5 shrink-0" />{ex.targeted_muscle || ex.muscle}
                          </span>
                        </div>
                        <div className="md:col-span-2">
                          <span className="text-[9px] font-black text-orange-400 uppercase bg-orange-500/5 border border-orange-500/10 px-3 py-1.5 rounded-xl flex items-center w-fit">
                            <Trophy size={10} className="mr-1.5 shrink-0" />{ex.difficulty}
                          </span>
                        </div>
                        <div className="md:col-span-2">
                          <span className="text-[9px] font-black text-purple-400 uppercase bg-purple-500/5 border border-purple-500/10 px-3 py-1.5 rounded-xl flex items-center w-fit">
                            <Wrench size={10} className="mr-1.5 shrink-0" />{ex.equipment}
                          </span>
                        </div>

                        <div className="md:col-span-2 flex items-center justify-between md:justify-end space-x-3">
                          {!sessionActive ? (
                            <div className="text-right">
                              <p className="text-lg font-black text-white italic leading-none">{ex.reps}</p>
                              <p className="text-[9px] font-black text-slate-600 uppercase tracking-widest">{ex.sets} sets</p>
                            </div>
                          ) : (
                            <div className="flex items-center space-x-2 bg-slate-950 p-2 rounded-xl border border-white/5" onClick={e => e.stopPropagation()}>
                              <input type="number" value={exerciseTracking[idx]?.reps || 0} onChange={e => updateTracking(idx, 'reps', parseInt(e.target.value))}
                                className="w-10 bg-transparent text-center font-black text-emerald-400 text-xs outline-none" />
                              <span className="text-[8px] text-slate-600 font-black">×</span>
                              <input type="number" value={exerciseTracking[idx]?.sets || 0} onChange={e => updateTracking(idx, 'sets', parseInt(e.target.value))}
                                className="w-10 bg-transparent text-center font-black text-emerald-400 text-xs outline-none" />
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Food Logger (New Section) */}
      <div className="glass-panel p-8 rounded-[3rem] border border-cyan-500/20">
        <div className="flex items-center space-x-4 mb-8">
          <div className="p-4 bg-cyan-500 text-slate-950 rounded-3xl shadow-[0_0_20px_rgba(6,182,212,0.3)]">
            <Database size={28} />
          </div>
          <div>
            <h2 className="text-3xl font-black italic tracking-tighter text-white uppercase">Bio-Fuel Logger</h2>
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-cyan-500">Precision Per-Gram Nutrition Tracking</p>
          </div>
        </div>
        <div className="p-6 bg-slate-950/50 border border-white/5 rounded-3xl text-center">
          <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mb-4 italic">Scan meal image or search expanded library for per-gram tracking</p>
          <div className="flex justify-center space-x-4">
            <button className="px-6 py-4 bg-slate-900 border border-cyan-500/20 text-cyan-400 rounded-2xl font-black text-[10px] uppercase tracking-widest hover:bg-cyan-500/10 transition">Search Food Node</button>
            <button className="px-6 py-4 bg-cyan-500 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest shadow-[0_5px_15px_rgba(6,182,212,0.3)]">Upload Visual Data</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkoutAssistant;
