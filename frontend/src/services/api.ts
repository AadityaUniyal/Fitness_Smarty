import { UserStats, BiometricPoint, WorkoutPlan } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');

// Helper to get auth token
const getAuthHeaders = async (getToken: () => Promise<string | null>) => {
  const token = await getToken();
  if (token) {
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }
  return { 'Content-Type': 'application/json' };
};

export const fetchUserStats = async (userId: string, getToken: () => Promise<string | null> = async () => null): Promise<UserStats> => {
  try {
    const headers = await getAuthHeaders(getToken);
    const res = await fetch(`${API_BASE}/api/users/me`, { headers });
    if (!res.ok) throw new Error('Uplink failed');
    return await res.json();
  } catch (e) {
    return {
      id: userId,
      name: 'Operator Alex',
      level: 'Elite Tier 4',
      xp: 12450,
      daily_calories: 2450,
      daily_steps: 12402,
      active_minutes: 84,
      weight: 80.2,
      heart_rate: 72
    };
  }
};

export const fetchAnalytics = async (
  userId: string,
  metric: string = 'steps',
  range: number = 7,
  getToken: () => Promise<string | null> = async () => null
): Promise<BiometricPoint[]> => {
  try {
    const headers = await getAuthHeaders(getToken);
    // Pass metric and range as query params
    const res = await fetch(`${API_BASE}/analytics/${userId}?metric=${metric}&range=${range}`, { headers });
    if (!res.ok) throw new Error('Neural sync lost');
    return await res.json();
  } catch (e) {
    return Array.from({ length: range || 7 }, (_, i) => ({
      timestamp: new Date(Date.now() - ((range || 7) - i) * 24 * 60 * 60 * 1000).toISOString(),
      value: 68 + Math.random() * 8, // Default value field for generic chart
      category: metric as any
    }));
  }
};

export const fetchRecoveryScore = async (getToken: () => Promise<string | null> = async () => null): Promise<any> => {
  try {
    const headers = await getAuthHeaders(getToken);
    const res = await fetch(`${API_BASE}/api/analytics/recovery-score`, { headers });
    if (!res.ok) throw new Error('Recovery sync failed');
    return await res.json();
  } catch (e) {
    return { score: 85, breakdown: { strain_recovery: 80, nutritional_status: 90, system_stability: 85 }, status: "EMERALD" };
  }
}

export const fetchNeuralIntegrity = async (getToken: () => Promise<string | null> = async () => null): Promise<any> => {
  try {
    const headers = await getAuthHeaders(getToken);
    const res = await fetch(`${API_BASE}/api/analytics/daily-budget/demo`, { headers });
    if (!res.ok) throw new Error('Integrity check failed');
    return await res.json();
  } catch (e) {
    return {
      integrity_score: 98,
      precision_index: 'HIGH',
      focus_area: 'Posterior Chain'
    };
  }
}

export const fetchMissionBriefing = async (getToken: () => Promise<string | null> = async () => null): Promise<any> => {
  try {
    const headers = await getAuthHeaders(getToken);
    const res = await fetch(`${API_BASE}/health`, { headers });
    if (!res.ok) throw new Error('Briefing uplink failed');
    return await res.json();
  } catch (e) {
    return {
      directive: "System nominal. Objective: Maintain kinetic precision and follow high-protein fuel protocols.",
      timestamp: new Date().toISOString()
    };
  }
}

export const fetchDailyCoach = async (payload?: any, getToken: () => Promise<string | null> = async () => null): Promise<any> => {
  let actualGetToken = getToken;
  if (typeof payload === 'function') {
    actualGetToken = payload;
  }
  try {
    const headers = await getAuthHeaders(actualGetToken);
    const res = await fetch(`${API_BASE}/api/coach/daily`, {
      method: 'GET',
      headers,
    });
    if (!res.ok) throw new Error('AI coach sync failed');
    return await res.json();
  } catch (e) {
    return {
      coach_summary: 'Your day is ready to steer. Start with one logged action, then let SMARTY adjust the next move.',
      gender_mode: 'male',
      today_focus: { training: 'Lighter movement block', nutrition: 'Daily consistency' },
      workout_recommendation: { type: 'rest', exercises: [], reasoning: 'Rest day recommended.' },
      meal_recommendation: { next_meal: 'Balanced Meal', foods: [], macro_gap: {} },
      next_action: {
        title: 'Start a focused workout',
        detail: 'A short movement block will anchor today.',
        route: '/dashboard/quick',
        priority: 'High',
      },
      daily_tasks: [],
    };
  }
}

export const logWorkout = async (userId: string, workout: WorkoutPlan, getToken: () => Promise<string | null> = async () => null): Promise<void> => {
  try {
    const headers = await getAuthHeaders(getToken);
    const res = await fetch(`${API_BASE}/api/exercises/log`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ userId, workout })
    });
    if (!res.ok) throw new Error('Log transmission failed');
  } catch (e) {
    console.error('Workout log failed:', e);
  }
};

// --- NEW: ML Training API Functions ---

export const submitFoodCorrection = async (
  mealLogId: string,
  imageUrl: string,
  originalDetections: any[],
  correctedLabels: any[],
  getToken: () => Promise<string | null> = async () => null
) => {
  try {
    const headers = await getAuthHeaders(getToken);
    const res = await fetch(`${API_BASE}/api/training/corrections/food`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        meal_log_id: mealLogId,
        image_url: imageUrl,
        original_detections: originalDetections,
        corrected_labels: correctedLabels
      })
    });
    return await res.json();
  } catch { return { success: false }; }
};

export const submitHealthFeedback = async (
  mealLogId: string,
  userProfile: any,
  mealComposition: any,
  feedback: 'good_for_me' | 'not_good_for_me',
  reason: string | null,
  getToken: () => Promise<string | null> = async () => null
) => {
  try {
    const headers = await getAuthHeaders(getToken);
    const res = await fetch(`${API_BASE}/api/training/feedback/health`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        meal_log_id: mealLogId,
        user_profile: userProfile,
        meal_composition: mealComposition,
        user_feedback: feedback,
        reason
      })
    });
    return await res.json();
  } catch { return { success: false }; }
};

export const predictMealHealth = async (
  userProfile: any,
  mealComposition: any,
  getToken: () => Promise<string | null> = async () => null
) => {
  try {
    const headers = await getAuthHeaders(getToken);
    const res = await fetch(`${API_BASE}/api/training/predict/health`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        user_profile: userProfile,
        meal_composition: mealComposition
      })
    });
    return await res.json();
  } catch { return { success: false }; }
};

export const logBiomechanicalFault = async (fault: any, getToken: () => Promise<string | null> = async () => null) => {
  const headers = await getAuthHeaders(getToken);
  try {
    const res = await fetch(`${API_BASE}/api/feedback/`, {
      method: 'POST',
      headers,
      body: JSON.stringify(fault)
    });
    if (!res.ok) throw new Error('Fault log failed');
    return await res.json();
  } catch (e) {
    return { success: true };
  }
};

export const getDatasetStats = async (getToken: () => Promise<string | null> = async () => null) => {
  try {
    const headers = await getAuthHeaders(getToken);
    const res = await fetch(`${API_BASE}/api/training/dataset/stats`, { headers });
    return await res.json();
  } catch { return null; }
};

export const fetchFemmeCareAdvice = async (userId: string, getToken: () => Promise<string | null> = async () => null) => {
  try {
    const headers = await getAuthHeaders(getToken);
    const res = await fetch(`${API_BASE}/api/female/cycle-phase/${userId}`, { headers });
    if (!res.ok) throw new Error('FemmeCare sync failed');
    return await res.json();
  } catch (e) {
    return {
      phase: "Follicular",
      advice: {
        training: "Energy is rising. Best time for progressive overload and building muscle.",
        nutrition: "Support rising estrogen with fermented foods and complex carbs for stamina.",
        focus: "Strength & Growth",
        intensity_limit: "High",
        bio_context: "Estrogen is climbing, increasing insulin sensitivity and strength capacity."
      },
      recommended_exercises: [],
      learned_cycle_length: 28,
      anomaly_warning: "",
      cycle_history_stats: null,
      user_profile: { menopause_mode: false, pregnancy_mode: false, local_only: false }
    };
  }
};

export const logPeriod = async (userId: string, logData: any, getToken: () => Promise<string | null> = async () => null) => {
  try {
    const headers = await getAuthHeaders(getToken);
    // logData has: start_date, symptoms, mood, flow_intensity, notes, cycle_length_days
    const params = new URLSearchParams({
      start_date: logData.start_date,
      mood: logData.mood || '',
      flow_intensity: logData.flow_intensity || '',
      notes: logData.notes || '',
      cycle_length_days: String(logData.cycle_length_days || 28)
    });
    // Add symptoms as query/body list
    if (logData.symptoms) {
      logData.symptoms.forEach((s: string) => params.append('symptoms', s));
    }
    const res = await fetch(`${API_BASE}/api/female/log-period/${userId}?${params.toString()}`, {
      method: 'POST',
      headers
    });
    return await res.json();
  } catch { return { success: false }; }
};

export const updateFemmeCareSettings = async (
  userId: string, 
  settings: { femmecare_enabled?: boolean; menopause_mode?: boolean; pregnancy_mode?: boolean; local_only?: boolean },
  getToken: () => Promise<string | null> = async () => null
) => {
  try {
    const headers = await getAuthHeaders(getToken);
    const params = new URLSearchParams();
    if (settings.femmecare_enabled !== undefined) params.append('femmecare_enabled', String(settings.femmecare_enabled));
    if (settings.menopause_mode !== undefined) params.append('menopause_mode', String(settings.menopause_mode));
    if (settings.pregnancy_mode !== undefined) params.append('pregnancy_mode', String(settings.pregnancy_mode));
    if (settings.local_only !== undefined) params.append('local_only', String(settings.local_only));

    const res = await fetch(`${API_BASE}/api/female/update-settings/${userId}?${params.toString()}`, {
      method: 'POST',
      headers
    });
    return await res.json();
  } catch { return { success: false }; }
};

