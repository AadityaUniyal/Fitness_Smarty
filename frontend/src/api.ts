import { UserStats, BiometricPoint, WorkoutPlan } from './types';

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

export const fetchUserStats = async (userId: string, getToken: () => Promise<string | null> = async () => null): Promise<UserStats> => {
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
    const res = await fetch(`${API_BASE}/neural/recovery`, { headers });
    if (!res.ok) throw new Error('Recovery sync failed');
    return await res.json();
  } catch (e) {
    return { score: 85, advice: "System nominal. Ready for heavy load." };
  }
}

export const fetchNeuralIntegrity = async (getToken: () => Promise<string | null> = async () => null): Promise<any> => {
  try {
    const headers = await getAuthHeaders(getToken);
    const res = await fetch(`${API_BASE}/neural/integrity`, { headers }); // Assuming endpoint exists
    if (!res.ok) throw new Error('Integrity check failed');
    return await res.json();
  } catch (e) {
    return {
      integrity_score: 98,
      status: 'STABLE',
      directive: 'No faults archived. Continue session.',
      focus_area: 'Posterior Chain'
    };
  }
}

export const logWorkout = async (userId: string, workout: WorkoutPlan, getToken: () => Promise<string | null> = async () => null): Promise<void> => {
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
  getToken: () => Promise<string | null> = async () => null
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
  getToken: () => Promise<string | null> = async () => null
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
  getToken: () => Promise<string | null> = async () => null
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

export const logBiomechanicalFault = async (fault: any, getToken: () => Promise<string | null> = async () => null) => {
  const headers = await getAuthHeaders(getToken);
  try {
    const res = await fetch(`${API_BASE}/neural/faults`, {
      method: 'POST',
      headers,
      body: JSON.stringify(fault)
    });
    if (!res.ok) throw new Error('Fault log failed');
    return await res.json();
  } catch (e) {
    console.log('Fault logged locally:', fault);
    return { success: true };
  }
};

export const getDatasetStats = async (getToken: () => Promise<string | null> = async () => null) => {
  const headers = await getAuthHeaders(getToken);
  const res = await fetch(`${API_BASE}/api/training/dataset/stats`, { headers });
  return await res.json();
};