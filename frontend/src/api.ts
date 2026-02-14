import { UserStats, BiometricPoint, WorkoutPlan } from '../types';

const API_BASE = 'http://localhost:8000';

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

export const fetchUserStats = async (userId: string, getToken: () => Promise<string | null>): Promise<UserStats> => {
  try {
    const headers = await getAuthHeaders(getToken);
    const res = await fetch(`${API_BASE}/users/me`, { headers });
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

export const fetchAnalytics = async (userId: string, getToken: () => Promise<string | null>): Promise<BiometricPoint[]> => {
  try {
    const headers = await getAuthHeaders(getToken);
    const res = await fetch(`${API_BASE}/analytics/${userId}`, { headers });
    if (!res.ok) throw new Error('Neural sync lost');
    return await res.json();
  } catch (e) {
    return Array.from({ length: 7 }, (_, i) => ({
      timestamp: new Date(Date.now() - (6 - i) * 24 * 60 * 60 * 1000).toISOString(),
      heart_rate: 68 + Math.random() * 8,
      calories_burned: 2200 + Math.random() * 300,
      steps: 8000 + Math.random() * 4000,
      sleep_hours: 6.5 + Math.random() * 2
    }));
  }
};

export const logWorkout = async (userId: string, workout: WorkoutPlan, getToken: () => Promise<string | null>): Promise<void> => {
  try {
    const headers = await getAuthHeaders(getToken);
    const res = await fetch(`${API_BASE}/workouts`, {
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
  getToken: () => Promise<string | null>
) => {
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
};

export const submitHealthFeedback = async (
  mealLogId: string,
  userProfile: any,
  mealComposition: any,
  feedback: 'good_for_me' | 'not_good_for_me',
  reason: string | null,
  getToken: () => Promise<string | null>
) => {
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
};

export const predictMealHealth = async (
  userProfile: any,
  mealComposition: any,
  getToken: () => Promise<string | null>
) => {
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
};

export const getDatasetStats = async (getToken: () => Promise<string | null>) => {
  const headers = await getAuthHeaders(getToken);
  const res = await fetch(`${API_BASE}/api/training/dataset/stats`, { headers });
  return await res.json();
};