/**
 * Smarty AI — Centralized Storage Service
 * All localStorage read/write operations go through here for type safety and consistency.
 */

import { BioProfile, WorkoutPlan } from '../types';

// ─────────────────────────────────────────────
// Keys
// ─────────────────────────────────────────────
const KEYS = {
  USER: 'smarty_user',
  PROFILE: 'smarty_profile',
  MEAL_LOGS: 'smarty_meal_logs',
  WORKOUT_LOGS: 'smarty_workout_logs',
  WEIGHT_LOG: 'smarty_weight_log',
  HYDRATION: 'smarty_hydration',
  TASKS: 'smarty_tasks',
} as const;

// ─────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────
export interface StoredUser {
  name: string;
  email: string;
  loggedIn: boolean;
}

export interface MealLog {
  id: string;
  mealName: string;
  totalCalories: number;
  totalProtein: number;
  totalCarbs: number;
  totalFats: number;
  mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  timestamp: string;
  items?: Array<{ name: string; calories: number; protein: number; carbs: number; fats: number }>;
}

export interface WorkoutLog {
  id: string;
  name: string;
  duration: number;
  caloriesBurned: number;
  exercisesCompleted: number;
  exercisesTotal: number;
  timestamp: string;
  goal: string;
}

export interface WeightEntry {
  date: string;
  weight: number;
}

// ─────────────────────────────────────────────
// Generic helpers
// ─────────────────────────────────────────────
function get<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function set<T>(key: string, value: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (e) {
    console.error('[StorageService] Write failed:', e);
  }
}

// ─────────────────────────────────────────────
// User
// ─────────────────────────────────────────────
export const StorageService = {
  getUser: (): StoredUser | null => get<StoredUser | null>(KEYS.USER, null),
  setUser: (user: StoredUser) => set(KEYS.USER, user),
  clearUser: () => localStorage.removeItem(KEYS.USER),

  // ─── Profile ───
  getProfile: (): BioProfile & { name?: string; dailyCalorieGoal?: number; targetWeight?: number } =>
    get(KEYS.PROFILE, {}),
  setProfile: (profile: any) => set(KEYS.PROFILE, profile),

  // ─── Meal Logs ───
  getMealLogs: (): MealLog[] => get<MealLog[]>(KEYS.MEAL_LOGS, []),
  addMealLog: (meal: MealLog) => {
    const logs = StorageService.getMealLogs();
    set(KEYS.MEAL_LOGS, [meal, ...logs]);
  },
  getTodayMeals: (): MealLog[] => {
    const today = new Date().toDateString();
    return StorageService.getMealLogs().filter(m => new Date(m.timestamp).toDateString() === today);
  },
  getTodayCalories: (): number =>
    StorageService.getTodayMeals().reduce((s, m) => s + (m.totalCalories || 0), 0),
  getTodayProtein: (): number =>
    StorageService.getTodayMeals().reduce((s, m) => s + (m.totalProtein || 0), 0),

  // ─── Workout Logs ───
  getWorkoutLogs: (): WorkoutLog[] => get<WorkoutLog[]>(KEYS.WORKOUT_LOGS, []),
  addWorkoutLog: (log: WorkoutLog) => {
    const logs = StorageService.getWorkoutLogs();
    set(KEYS.WORKOUT_LOGS, [log, ...logs]);
  },
  getTodayCalsBurned: (): number => {
    const today = new Date().toDateString();
    return StorageService.getWorkoutLogs()
      .filter(w => new Date(w.timestamp).toDateString() === today)
      .reduce((s, w) => s + (w.caloriesBurned || 0), 0);
  },
  getWorkoutStreak: (): number => {
    const logs = StorageService.getWorkoutLogs();
    let streak = 0;
    let d = new Date();
    while (streak < 365) {
      if (logs.some(w => new Date(w.timestamp).toDateString() === d.toDateString())) {
        streak++;
      } else break;
      d.setDate(d.getDate() - 1);
    }
    return streak;
  },

  // ─── Weight ───
  getWeightLog: (): WeightEntry[] => get<WeightEntry[]>(KEYS.WEIGHT_LOG, []),
  addWeightEntry: (entry: WeightEntry) => {
    const log = StorageService.getWeightLog();
    set(KEYS.WEIGHT_LOG, [...log, entry]);
  },

  // ─── Hydration ───
  getHydration: (): { glasses: number; date: string } => {
    const today = new Date().toDateString();
    const stored = get<{ glasses: number; date: string }>(KEYS.HYDRATION, { glasses: 0, date: today });
    if (stored.date !== today) {
      set(KEYS.HYDRATION, { glasses: 0, date: today });
      return { glasses: 0, date: today };
    }
    return stored;
  },
  setHydration: (glasses: number) => set(KEYS.HYDRATION, { glasses, date: new Date().toDateString() }),

  // ─── Utility ───
  clearAll: () => {
    Object.values(KEYS).forEach(key => localStorage.removeItem(key));
  },
};

export default StorageService;
