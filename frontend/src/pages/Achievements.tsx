import React, { useState, useEffect } from 'react';
import { Trophy, Flame, Dumbbell, Utensils, Zap, Star, Target, Heart, Calendar, Award, Lock, TrendingUp, Camera, MessageCircle, Timer } from 'lucide-react';
import { fetchGamificationSummary, fetchUserAchievements } from '../services/apiService';
import { useCurrentUserId } from '../hooks/useCurrentUserId';
import { useUserProfile } from '../hooks/useUserProfile';

const STORAGE_KEY = 'smarty_earned_achievements';

interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  category: string;
  check: () => boolean;
}

const createAchievements = (): Achievement[] => [
  {
    id: 'first_workout', title: 'First Steps', description: 'Complete your first workout', category: 'Workouts',
    icon: <Dumbbell size={20} />, color: 'emerald',
    check: () => { const logs = JSON.parse(localStorage.getItem('smarty_workout_logs') || '[]'); return logs.length >= 1; }
  },
  {
    id: 'streak_3', title: 'Getting Consistent', description: 'Complete workouts 3 days in a row', category: 'Workouts',
    icon: <Flame size={20} />, color: 'orange',
    check: () => { const logs: any[] = JSON.parse(localStorage.getItem('smarty_workout_logs') || '[]'); const dates = [...new Set(logs.map(l => new Date(l.timestamp).toDateString()))].sort().reverse(); if (dates.length < 3) return false; const today = new Date().toDateString(); for (let i = 0; i < 3; i++) { const d = new Date(); d.setDate(d.getDate() - i); if (!dates.includes(d.toDateString())) return false; } return true; }
  },
  {
    id: 'streak_7', title: 'Unstoppable', description: '7-day workout streak', category: 'Workouts',
    icon: <Zap size={20} />, color: 'amber',
    check: () => { const logs: any[] = JSON.parse(localStorage.getItem('smarty_workout_logs') || '[]'); const dates = [...new Set(logs.map(l => new Date(l.timestamp).toDateString()))].sort().reverse(); if (dates.length < 7) return false; for (let i = 0; i < 7; i++) { const d = new Date(); d.setDate(d.getDate() - i); if (!dates.includes(d.toDateString())) return false; } return true; }
  },
  {
    id: 'workout_10', title: 'Dedicated', description: 'Complete 10 workouts total', category: 'Workouts',
    icon: <Trophy size={20} />, color: 'emerald',
    check: () => { const logs = JSON.parse(localStorage.getItem('smarty_workout_logs') || '[]'); return logs.length >= 10; }
  },
  {
    id: 'workout_50', title: 'Veteran', description: 'Complete 50 workouts total', category: 'Workouts',
    icon: <Award size={20} />, color: 'purple',
    check: () => { const logs = JSON.parse(localStorage.getItem('smarty_workout_logs') || '[]'); return logs.length >= 50; }
  },
  {
    id: 'first_meal', title: 'Fuel Up', description: 'Log your first meal', category: 'Nutrition',
    icon: <Utensils size={20} />, color: 'amber',
    check: () => { const logs = JSON.parse(localStorage.getItem('smarty_meal_logs') || '[]'); return logs.length >= 1; }
  },
  {
    id: 'meal_30', title: 'Meal Tracker', description: 'Log 30 meals total', category: 'Nutrition',
    icon: <Target size={20} />, color: 'orange',
    check: () => { const logs = JSON.parse(localStorage.getItem('smarty_meal_logs') || '[]'); return logs.length >= 30; }
  },
  {
    id: 'calorie_burn_1000', title: 'Heat Wave', description: 'Burn 1000+ calories in a single workout', category: 'Performance',
    icon: <Flame size={20} />, color: 'rose',
    check: () => { const logs: any[] = JSON.parse(localStorage.getItem('smarty_workout_logs') || '[]'); return logs.some(l => (l.caloriesBurned || 0) >= 1000); }
  },
  {
    id: 'calorie_total_10000', title: 'Calorie Crusher', description: 'Burn 10,000 total calories', category: 'Performance',
    icon: <Flame size={20} />, color: 'orange',
    check: () => { const logs: any[] = JSON.parse(localStorage.getItem('smarty_workout_logs') || '[]'); return logs.reduce((s, l) => s + (l.caloriesBurned || 0), 0) >= 10000; }
  },
  {
    id: 'protein_100', title: 'Protein King', description: 'Log 100g+ protein in a single day', category: 'Nutrition',
    icon: <Star size={20} />, color: 'blue',
    check: () => { const logs: any[] = JSON.parse(localStorage.getItem('smarty_meal_logs') || '[]'); const today = new Date().toDateString(); const todayMeals = logs.filter(l => new Date(l.timestamp).toDateString() === today); return todayMeals.reduce((s, l) => s + (l.totalProtein || 0), 0) >= 100; }
  },
  {
    id: 'perfect_day', title: 'Perfect Day', description: 'Complete a workout AND log all meals for a day', category: 'Lifestyle',
    icon: <Heart size={20} />, color: 'rose',
    check: () => { const wLogs: any[] = JSON.parse(localStorage.getItem('smarty_workout_logs') || '[]'); const mLogs: any[] = JSON.parse(localStorage.getItem('smarty_meal_logs') || '[]'); const today = new Date().toDateString(); return wLogs.some(l => new Date(l.timestamp).toDateString() === today) && mLogs.some(l => new Date(l.timestamp).toDateString() === today); }
  },
  {
    id: 'water_goal', title: 'Hydrated', description: 'Hit your water goal for the day', category: 'Lifestyle',
    icon: <Heart size={20} />, color: 'cyan',
    check: () => { const ml = Number(localStorage.getItem('smarty_hydration_ml') || 0); return ml >= 3000; }
  },
  {
    id: 'profile_set', title: 'Identified', description: 'Complete your bio profile', category: 'Milestones',
    icon: <Target size={20} />, color: 'emerald',
    check: () => Boolean(profile.weight || profile.weight_kg) && Boolean(profile.height || profile.height_cm) && Boolean(profile.goal || profile.primary_goal)
  },
  {
    id: 'measurement_3', title: 'Tracked', description: 'Log 3 body measurements', category: 'Milestones',
    icon: <TrendingUp size={20} />, color: 'cyan',
    check: () => { try { const m = JSON.parse(localStorage.getItem('smarty_body_measurements') || '[]'); return m.length >= 3; } catch { return false; } }
  },
  {
    id: 'mood_logged', title: 'Self Aware', description: 'Log your mood after a workout', category: 'Milestones',
    icon: <MessageCircle size={20} />, color: 'purple',
    check: () => { try { const m = JSON.parse(localStorage.getItem('smarty_mood_logs') || '[]'); return m.length >= 1; } catch { return false; } }
  },
  {
    id: 'workout_1h', title: 'Marathon Session', description: 'Complete a 60+ minute workout', category: 'Performance',
    icon: <Timer size={20} />, color: 'purple',
    check: () => { const logs: any[] = JSON.parse(localStorage.getItem('smarty_workout_logs') || '[]'); return logs.some(l => (l.duration || 0) >= 60); }
  },
];

const categoryIcons: Record<string, React.ReactNode> = {
  Workouts: <Dumbbell size={14} />, Nutrition: <Utensils size={14} />, Performance: <Zap size={14} />,
  Lifestyle: <Heart size={14} />, Milestones: <Award size={14} />,
};
const categoryColors: Record<string, string> = {
  Workouts: 'text-emerald-400', Nutrition: 'text-amber-400', Performance: 'text-orange-400',
  Lifestyle: 'text-rose-400', Milestones: 'text-purple-400',
};

const Achievements: React.FC = () => {
  const allAchievements = createAchievements();
  const userId = useCurrentUserId();
  const { profile } = useUserProfile();
  const [earned, setEarned] = useState<string[]>(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); } catch { return []; }
  });
  const [justEarned, setJustEarned] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    const load = async () => {
      const [summary, userAch] = await Promise.all([
        fetchGamificationSummary(userId),
        fetchUserAchievements(userId),
      ]);
      const serverEarned = new Set<string>();
      userAch?.achievements?.forEach((a: any) => serverEarned.add(String(a.id)));
      if (summary?.achievements_completed != null) {
        // summary loaded; nothing extra needed here except ensuring UI refresh
      }
      const merged = [...new Set([...earned, ...Array.from(serverEarned)])];
      setEarned(merged);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
    };
    load();
  }, []);

  const categories = ['all', ...new Set(allAchievements.map(a => a.category))];
  const filtered = filter === 'all' ? allAchievements : allAchievements.filter(a => a.category === filter);
  const earnedCount = earned.length;
  const totalCount = allAchievements.length;

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Just earned notification */}
      {justEarned && (() => {
        const ach = allAchievements.find(a => a.id === justEarned);
        return ach ? (
          <div className="fixed top-24 right-6 z-50 bg-gradient-to-br from-emerald-500 to-cyan-500 text-slate-950 rounded-3xl p-6 shadow-2xl animate-in slide-in-from-right-4 duration-500">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-white/20 rounded-2xl">{ach.icon}</div>
              <div>
                <p className="text-[9px] font-black uppercase tracking-widest opacity-70">Achievement Unlocked</p>
                <p className="text-lg font-black mt-0.5">{ach.title}</p>
                <p className="text-xs opacity-80 mt-0.5">{ach.description}</p>
              </div>
            </div>
          </div>
        ) : null;
      })()}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <div className="w-16 h-16 bg-amber-500/10 border border-amber-500/20 rounded-3xl flex items-center justify-center text-amber-400">
            <Trophy size={32} />
          </div>
          <div>
            <h2 className="text-4xl font-black italic tracking-tighter text-white uppercase">Achievements</h2>
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Earn badges by hitting milestones</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-3xl font-black text-amber-400">{earnedCount}<span className="text-lg text-slate-500">/{totalCount}</span></p>
          <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Badges Earned</p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="glass-panel p-6 rounded-2xl border border-white/5">
        <div className="flex items-center justify-between mb-3">
          <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Overall Progress</span>
          <span className="text-[10px] font-black text-amber-400">{Math.round((earnedCount / totalCount) * 100)}%</span>
        </div>
        <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-amber-500 to-orange-500 rounded-full transition-all duration-1000" style={{ width: `${(earnedCount / totalCount) * 100}%` }} />
        </div>
      </div>

      {/* Category filters */}
      <div className="flex flex-wrap gap-2">
        {categories.map(cat => (
          <button key={cat} onClick={() => setFilter(cat)}
            className={`px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all ${filter === cat ? 'bg-amber-500 text-slate-950' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}>
            {cat === 'all' ? 'All' : cat}
          </button>
        ))}
      </div>

      {/* Achievement grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {filtered.map(ach => {
          const isEarned = earned.includes(ach.id);
          return (
            <div key={ach.id}
              className={`relative p-6 rounded-2xl border transition-all ${isEarned ? 'bg-gradient-to-br from-amber-500/10 to-orange-500/5 border-amber-500/30 card-hover' : 'bg-slate-900 border-slate-800 opacity-60'}`}>
              {!isEarned && (
                <div className="absolute top-3 right-3 text-slate-700">
                  <Lock size={14} />
                </div>
              )}
              <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-4 ${isEarned ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-800 text-slate-600'}`}>
                {ach.icon}
              </div>
              <h3 className={`text-base font-black tracking-tight ${isEarned ? 'text-white' : 'text-slate-500'}`}>{ach.title}</h3>
              <p className={`text-[10px] mt-1 ${isEarned ? 'text-slate-400' : 'text-slate-600'}`}>{ach.description}</p>
              <div className="flex items-center mt-4 space-x-2">
                <span className={`text-[8px] font-black uppercase tracking-widest ${categoryColors[ach.category] || 'text-slate-500'}`}>
                  {ach.category}
                </span>
                {isEarned && (
                  <span className="text-[8px] font-black text-emerald-400 uppercase tracking-widest flex items-center">
                    <Award size={10} className="mr-1" /> Earned
                  </span>
                )}
              </div>
              {isEarned && (
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-amber-400 rounded-full flex items-center justify-center">
                  <Star size={8} className="text-slate-950 fill-slate-950" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Achievements;
