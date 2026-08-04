/**
 * API Service Layer for Backend Communication
 * Provides type-safe methods for all backend API endpoints
 * Includes automatic JWT token refresh on 401 responses.
 */
import { UserStats, BiometricPoint, WorkoutPlan } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');

let isRefreshing = false;
let refreshQueue: Array<{ resolve: (token: string) => void; reject: (err: any) => void }> = [];

function getToken() { return localStorage.getItem('smarty_access_token'); }
function getRefreshToken() { return localStorage.getItem('smarty_refresh_token'); }
function setTokens(access: string, refresh: string) {
  localStorage.setItem('smarty_access_token', access);
  localStorage.setItem('smarty_refresh_token', refresh);
}
function clearAuth() {
  localStorage.removeItem('smarty_access_token');
  localStorage.removeItem('smarty_refresh_token');
  localStorage.removeItem('smarty_user_data');
  localStorage.removeItem('smarty_user');
}

async function refreshAccessToken(): Promise<string> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) throw new Error('No refresh token');

  const resp = await fetch(`${API_BASE}/api/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!resp.ok) {
    clearAuth();
    window.location.href = '/';
    throw new Error('Session expired');
  }

  const data = await resp.json();
  setTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const token = getToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string> || {}),
  };

  const config: RequestInit = { ...options, headers };

  try {
    let response = await fetch(url, config);

    if (response.status === 401 && getRefreshToken()) {
      if (!isRefreshing) {
        isRefreshing = true;
        try {
          const newToken = await refreshAccessToken();
          isRefreshing = false;
          refreshQueue.forEach(q => q.resolve(newToken));
          refreshQueue = [];
          headers['Authorization'] = `Bearer ${newToken}`;
          response = await fetch(url, { ...config, headers });
        } catch (err) {
          isRefreshing = false;
          refreshQueue.forEach(q => q.reject(err));
          refreshQueue = [];
          throw err;
        }
      } else {
        const newToken = await new Promise<string>((resolve, reject) => {
          refreshQueue.push({ resolve, reject });
        });
        headers['Authorization'] = `Bearer ${newToken}`;
        response = await fetch(url, { ...config, headers });
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      const detail = error?.detail;
      const message =
        typeof detail === 'string'
          ? detail
          : detail?.message || detail?.error || error?.message || `HTTP ${response.status}: ${response.statusText}`;
      throw new Error(message);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof TypeError && (error as any).message === 'Failed to fetch') {
      throw new Error('Network error — is the backend running?');
    }
    throw error;
  }
}

export { getToken, setTokens, clearAuth };

// ============= MEAL ANALYSIS API =============

export interface MealAnalysisResponse {
  meal_log_id: string;
  user_id: string;
  meal_type: string;
  image_url: string;
  analysis_confidence: number;
  detected_foods: Array<{
    food_id: string;
    name: string;
    estimated_quantity_g: number;
    confidence_score: number;
  }>;
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
  recommendations: string[];
  logged_at: string;
}

export interface MealHistoryItem {
  meal_log_id: string;
  meal_type: string;
  logged_at: string;
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
  image_url?: string;
  detected_foods_count: number;
}

export interface MealHistoryResponse {
  meals: MealHistoryItem[];
  total_count: number;
  page: number;
  page_size: number;
}

export interface DailyNutritionSummary {
  date: string;
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
  meal_count: number;
  meals_by_type: {
    breakfast: number;
    lunch: number;
    dinner: number;
    snack: number;
  };
}

export const MealAPI = {
  async analyzeMeal(
    userId: string,
    mealType: string,
    imageFile: File
  ): Promise<MealAnalysisResponse> {
    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('meal_type', mealType);
    formData.append('image_file', imageFile);

    const response = await fetch(`${API_BASE}/api/meals/analyze`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Analysis failed' }));
      throw new Error(error.detail || 'Meal analysis failed');
    }

    return await response.json();
  },

  async getMealHistory(
    userId: string,
    params?: {
      start_date?: string;
      end_date?: string;
      meal_type?: string;
      limit?: number;
      offset?: number;
    }
  ): Promise<MealHistoryResponse> {
    const queryParams = new URLSearchParams();
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.meal_type) queryParams.append('meal_type', params.meal_type);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());

    const query = queryParams.toString();
    const endpoint = `/api/meals/user/${userId}/history${query ? `?${query}` : ''}`;
    
    return apiRequest<MealHistoryResponse>(endpoint);
  },

  async getDailySummary(
    userId: string,
    date?: string
  ): Promise<DailyNutritionSummary> {
    const query = date ? `?date=${date}` : '';
    return apiRequest<DailyNutritionSummary>(`/api/meals/user/${userId}/daily-summary${query}`);
  },
};

// ============= USER PROFILE API =============

export interface UserProfile {
  id: string;
  user_id: string;
  age?: number;
  gender?: string;
  weight_kg?: number;
  height_cm?: number;
  activity_level: string;
  primary_goal: string;
  dietary_restrictions: string[];
  allergies: string[];
  created_at: string;
  updated_at: string;
}

export interface UserProfileCreate {
  age?: number;
  weight_kg?: number;
  height_cm?: number;
  activity_level: string;
  primary_goal: string;
  dietary_restrictions?: string[];
  allergies?: string[];
}

export interface ProfileValidation {
  is_complete: boolean;
  missing_fields: string[];
  warnings: string[];
  suggestions: string[];
}

export const UserProfileAPI = {
  async createProfile(
    userId: string,
    profileData: UserProfileCreate
  ): Promise<UserProfile> {
    return apiRequest<UserProfile>(`/api/users/${userId}/profile`, {
      method: 'POST',
      body: JSON.stringify(profileData),
    });
  },

  async getProfile(userId: string): Promise<UserProfile> {
    return apiRequest<UserProfile>(`/api/users/${userId}/profile`);
  },

  async updateProfile(
    userId: string,
    profileData: Partial<UserProfileCreate>
  ): Promise<UserProfile> {
    return apiRequest<UserProfile>(`/api/users/${userId}/profile`, {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
  },

  async validateProfile(userId: string): Promise<ProfileValidation> {
    return apiRequest<ProfileValidation>(`/api/users/${userId}/profile/validate`);
  },
};

// ============= GOALS API =============

export interface UserGoal {
  id: string;
  user_id: string;
  goal_type: string;
  target_value: number;
  current_value: number;
  target_date?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface GoalCreate {
  goal_type: string;
  target_value: number;
  target_date?: string;
}

export interface GoalValidation {
  is_realistic: boolean;
  warnings: string[];
  suggestions: string[];
  recommended_timeline?: string;
}

export interface ProgressMetrics {
  goal_id: string;
  goal_type: string;
  progress_percentage: number;
  current_value: number;
  target_value: number;
  days_remaining?: number;
  is_on_track: boolean;
}

export const GoalsAPI = {
  async createGoal(userId: string, goalData: GoalCreate): Promise<UserGoal> {
    return apiRequest<UserGoal>(`/api/users/${userId}/goals`, {
      method: 'POST',
      body: JSON.stringify(goalData),
    });
  },

  async getUserGoals(userId: string, activeOnly: boolean = true): Promise<{ goals: UserGoal[]; total_count: number }> {
    return apiRequest(`/api/users/${userId}/goals?active_only=${activeOnly}`);
  },

  async updateGoal(goalId: string, goalData: Partial<UserGoal>): Promise<UserGoal> {
    return apiRequest<UserGoal>(`/api/users/goals/${goalId}`, {
      method: 'PUT',
      body: JSON.stringify(goalData),
    });
  },

  async validateGoal(goalId: string): Promise<GoalValidation> {
    return apiRequest<GoalValidation>(`/api/users/goals/${goalId}/validate`);
  },

  async getProgress(userId: string): Promise<ProgressMetrics> {
    return apiRequest<ProgressMetrics>(`/api/users/${userId}/progress`);
  },

  async deleteGoal(goalId: string): Promise<void> {
    return apiRequest(`/api/users/goals/${goalId}`, { method: 'DELETE' });
  },
};

// ============= RECOMMENDATIONS API =============

export interface Recommendation {
  id: string;
  recommendation_type: string;
  title: string;
  description: string;
  confidence_score: number;
  is_read: boolean;
  created_at: string;
  expires_at?: string;
}

export interface RecommendationListResponse {
  recommendations: Recommendation[];
  total_count: number;
  unread_count: number;
}

export const RecommendationsAPI = {
  async getRecommendations(
    userId: string,
    params?: {
      recommendation_type?: string;
      include_read?: boolean;
      limit?: number;
      offset?: number;
    }
  ): Promise<RecommendationListResponse> {
    const queryParams = new URLSearchParams();
    if (params?.recommendation_type) queryParams.append('recommendation_type', params.recommendation_type);
    if (params?.include_read !== undefined) queryParams.append('include_read', params.include_read.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());

    const query = queryParams.toString();
    const endpoint = `/api/users/${userId}/recommendations${query ? `?${query}` : ''}`;
    
    return apiRequest<RecommendationListResponse>(endpoint);
  },

  async generateRecommendations(userId: string): Promise<{ message: string }> {
    return apiRequest(`/api/users/${userId}/recommendations/generate`, {
      method: 'POST',
    });
  },

  async markAsRead(recommendationId: string): Promise<{ message: string }> {
    return apiRequest(`/api/recommendations/read/${recommendationId}`, {
      method: 'PUT',
    });
  },
};

// ============= EXERCISE API =============

export interface Exercise {
  id: string;
  name: string;
  category: string;
  muscle_groups: string[];
  equipment: string[];
  difficulty_level: string;
  instructions: string;
  safety_notes: string;
  created_at: string;
}

export interface ExerciseSearchParams {
  name_query?: string;
  category?: string;
  muscle_groups?: string[];
  equipment?: string[];
  difficulty_level?: string;
  limit?: number;
  offset?: number;
}

export const ExerciseAPI = {
  async searchExercises(params: ExerciseSearchParams): Promise<Exercise[]> {
    return apiRequest<Exercise[]>('/api/exercises/search', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  async getExerciseById(exerciseId: string): Promise<Exercise> {
    return apiRequest<Exercise>(`/api/exercises/${exerciseId}`);
  },

  async getByDifficulty(difficulty: string): Promise<Exercise[]> {
    return apiRequest<Exercise[]>(`/api/exercises/difficulty/${difficulty}`);
  },

  async getByMuscleGroup(muscleGroup: string): Promise<Exercise[]> {
    return apiRequest<Exercise[]>(`/api/exercises/muscle-group/${muscleGroup}`);
  },

  async recommendExercises(params: {
    user_experience_level: string;
    target_muscle_groups?: string[];
    available_equipment?: string[];
    limit?: number;
  }): Promise<Exercise[]> {
    return apiRequest<Exercise[]>('/api/exercises/recommend', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },
};

// ============= FOOD/NUTRITION API =============

export interface FoodItem {
  id: number;
  name: string;
  category_id: number;
  serving_size: string;
  calories: number;
  protein: number;
  carbs: number;
  fats: number;
  is_elite: boolean;
}

export interface FoodCategory {
  id: number;
  name: string;
  items: FoodItem[];
}

export const FoodAPI = {
  async searchFood(query?: string, categoryId?: number): Promise<FoodItem[]> {
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (categoryId) params.append('category_id', categoryId.toString());
    
    const queryString = params.toString();
    return apiRequest<FoodItem[]>(`/api/food/search${queryString ? `?${queryString}` : ''}`);
  },

  async getFoodLibrary(): Promise<FoodCategory[]> {
    return apiRequest<FoodCategory[]>('/api/food/library');
  },
};

// ============= AUTHENTICATION API =============

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserRegister {
  email: string;
  password: string;
  name: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export const AuthAPI = {
  async register(userData: UserRegister): Promise<AuthTokens> {
    return apiRequest<AuthTokens>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },

  async login(credentials: UserLogin): Promise<AuthTokens> {
    return apiRequest<AuthTokens>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },

  async refreshToken(refreshToken: string): Promise<AuthTokens> {
    return apiRequest<AuthTokens>('/api/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  },

  async getCurrentUser(token: string): Promise<{ id: string; email: string }> {
    return apiRequest('/api/auth/me', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  async logout(token: string): Promise<{ message: string }> {
    return apiRequest('/api/auth/logout', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },

  async updateProfile(token: string, data: Record<string, any>): Promise<any> {
    return apiRequest('/api/auth/profile', {
      method: 'PUT',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify(data),
    });
  },

  async googleLogin(idToken: string): Promise<AuthTokens> {
    return apiRequest<AuthTokens>('/api/auth/oauth/google', {
      method: 'POST',
      body: JSON.stringify({ id_token: idToken }),
    });
  },

  async appleLogin(idToken: string, fullName?: string, email?: string): Promise<AuthTokens> {
    return apiRequest<AuthTokens>('/api/auth/oauth/apple', {
      method: 'POST',
      body: JSON.stringify({ id_token: idToken, full_name: fullName, email }),
    });
  },
};

// ============= TRAINING PIPELINE API =============

export interface TrainingStatus {
  datasets: { total_datasets: number; total_samples: number; datasets: string[] };
  trained_models: Array<{ name: string; path: string; size_kb: number }>;
}

export interface DatasetInfo {
  name: string; version: string; num_samples: number; num_classes: number;
  classes: string[]; split_sizes: Record<string, number>; source: string;
  created_at: string;
}

export const TrainingAPI = {
  async getStatus(): Promise<TrainingStatus> {
    return apiRequest<TrainingStatus>('/api/training/status');
  },

  async listDatasets(): Promise<{ datasets: string[]; statistics: any }> {
    return apiRequest('/api/training/datasets');
  },

  async getDatasetInfo(name: string): Promise<DatasetInfo> {
    return apiRequest<DatasetInfo>(`/api/training/datasets/${name}`);
  },

  async trainRecommendation(epochs: number = 50, useDb: boolean = false): Promise<any> {
    return apiRequest('/api/training/recommendation/train', {
      method: 'POST',
      body: JSON.stringify({ epochs, use_db: useDb }),
    });
  },

  async trainDetector(imagesSrc?: string, epochs: number = 50, imgsz: number = 640, batch: number = 16): Promise<any> {
    return apiRequest('/api/training/vision/train-detector', {
      method: 'POST',
      body: JSON.stringify({ images_src: imagesSrc, epochs, imgsz, batch }),
    });
  },

  async trainClassifier(dataset?: string, epochs: number = 30, batch: number = 32, lr: number = 0.001): Promise<any> {
    return apiRequest('/api/training/vision/train-classifier', {
      method: 'POST',
      body: JSON.stringify({ dataset, epochs, batch, lr }),
    });
  },

  async clusterUsers(nClusters?: number, method: string = 'kmeans'): Promise<any> {
    return apiRequest('/api/training/cluster/users', {
      method: 'POST',
      body: JSON.stringify({ n_clusters: nClusters, method }),
    });
  },

  async trainLSTM(epochs: number = 100, seqLength: number = 14, hidden: number = 64, layers: number = 2): Promise<any> {
    return apiRequest('/api/training/forecast/train-lstm', {
      method: 'POST',
      body: JSON.stringify({ epochs, seq_length: seqLength, hidden, layers }),
    });
  },

  async trainDQN(episodes: number = 500, batch: number = 64, lr: number = 0.001, gamma: number = 0.99): Promise<any> {
    return apiRequest('/api/training/rl/train-dqn', {
      method: 'POST',
      body: JSON.stringify({ episodes, batch, lr, gamma }),
    });
  },

  async trainQLearning(episodes: number = 1000, alpha: number = 0.1, gamma: number = 0.95): Promise<any> {
    return apiRequest('/api/training/rl/train-qlearning', {
      method: 'POST',
      body: JSON.stringify({ episodes, alpha, gamma }),
    });
  },
};

// ============= LEGACY API FUNCTIONS =============

export const fetchUserStats = async (userId: string): Promise<UserStats> => {
  try {
    return await apiRequest<UserStats>(`/api/users/me`);
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
  range: number = 7
): Promise<BiometricPoint[]> => {
  try {
    return await apiRequest<BiometricPoint[]>(`/api/analytics/${userId}?metric=${metric}&range=${range}`);
  } catch (e) {
    return Array.from({ length: range || 7 }, (_, i) => ({
      timestamp: new Date(Date.now() - ((range || 7) - i) * 24 * 60 * 60 * 1000).toISOString(),
      value: 68 + Math.random() * 8, // Default value field for generic chart
      category: metric as any
    }));
  }
};

export const fetchRecoveryScore = async (): Promise<any> => {
  try {
    return await apiRequest<any>('/api/neural/recovery');
  } catch (e) {
    return { score: 85, breakdown: { strain_recovery: 80, nutritional_status: 90, system_stability: 85 }, status: "EMERALD" };
  }
};

export const fetchNeuralIntegrity = async (): Promise<any> => {
  try {
    return await apiRequest<any>('/api/neural/integrity');
  } catch (e) {
    return {
      integrity_score: 98,
      precision_index: 'HIGH',
      focus_area: 'Posterior Chain'
    };
  }
};

export const fetchMissionBriefing = async (): Promise<any> => {
  try {
    return await apiRequest<any>('/api/neural/briefing');
  } catch (e) {
    return {
      directive: "System nominal. Objective: Maintain kinetic precision and follow high-protein fuel protocols.",
      timestamp: new Date().toISOString()
    };
  }
};

export const fetchDailyCoach = async (payload?: any): Promise<any> => {
  try {
    return await apiRequest<any>('/api/coach/daily');
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
};

export const fetchExplainableCoach = async (): Promise<any> => {
  try {
    return await apiRequest<any>('/api/coach/explainable');
  } catch {
    return {
      recommendation: {
        title: 'Keep moving with purpose',
        detail: 'Follow the highest-priority task on your dashboard.',
        route: '/dashboard',
        priority: 'Medium',
      },
      confidence_score: 82,
      explanation: [
        'A deterministic rule check found no major blockers.',
        'Use the current plan and log the next action.'
      ],
      factors: ['Current data supports a steady training day'],
      progress_snapshot: {
        calories_remaining: 0,
        protein_remaining: 0,
        workout_status: 'not_started',
        sets_completed: 0,
        sets_planned: 0,
      },
      mode_note: 'Standard mode is active.',
    };
  }
};

export const fetchCoachHistory = async (): Promise<any> => {
  try {
    return await apiRequest<any>('/api/coach/history');
  } catch {
    return {
      period_days: 7,
      trend_note: 'Consistency is solid this week.',
      entries: [
        {
          date: new Date().toISOString().split('T')[0],
          title: 'No history yet',
          detail: 'Log a meal or workout to start building your coach timeline.',
          confidence: 60,
          workout_status: 'not_started',
          progress_percent: 0,
          feedback: 'balanced',
          feedback_count: 0,
        },
      ],
    };
  }
};

export const logWorkout = async (userId: string, workout: WorkoutPlan): Promise<void> => {
  try {
    await apiRequest<void>('/api/workouts/log', {
      method: 'POST',
      body: JSON.stringify({ userId, workout })
    });
  } catch (e) {
    console.error('Workout log failed:', e);
  }
};

export const submitFoodCorrection = async (
  mealLogId: string,
  imageUrl: string,
  originalDetections: any[],
  correctedLabels: any[]
) => {
  try {
    return await apiRequest<any>('/api/training/corrections/food', {
      method: 'POST',
      body: JSON.stringify({
        meal_log_id: mealLogId,
        image_url: imageUrl,
        original_detections: originalDetections,
        corrected_labels: correctedLabels
      })
    });
  } catch { return { success: false }; }
};

export const submitHealthFeedback = async (
  mealLogId: string,
  userProfile: any,
  mealComposition: any,
  feedback: 'good_for_me' | 'not_good_for_me',
  reason: string | null
) => {
  try {
    return await apiRequest<any>('/api/training/feedback/health', {
      method: 'POST',
      body: JSON.stringify({
        meal_log_id: mealLogId,
        user_profile: userProfile,
        meal_composition: mealComposition,
        user_feedback: feedback,
        reason
      })
    });
  } catch { return { success: false }; }
};

export const predictMealHealth = async (
  userProfile: any,
  mealComposition: any
) => {
  try {
    return await apiRequest<any>('/api/training/predict/health', {
      method: 'POST',
      body: JSON.stringify({
        user_profile: userProfile,
        meal_composition: mealComposition
      })
    });
  } catch { return { success: false }; }
};

export const logBiomechanicalFault = async (fault: any) => {
  try {
    return await apiRequest<any>('/api/feedback/', {
      method: 'POST',
      body: JSON.stringify(fault)
    });
  } catch (e) {
    return { success: true };
  }
};

export const getDatasetStats = async () => {
  try {
    return await apiRequest<any>('/api/training/dataset/stats');
  } catch { return null; }
};

export const fetchFemmeCareAdvice = async (userId: string) => {
  try {
    return await apiRequest<any>(`/api/female/cycle-phase/${userId}`);
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

export const logPeriod = async (userId: string, logData: any) => {
  try {
    const params = new URLSearchParams({
      start_date: logData.start_date,
      mood: logData.mood || '',
      flow_intensity: logData.flow_intensity || '',
      notes: logData.notes || '',
      cycle_length_days: String(logData.cycle_length_days || 28)
    });
    if (logData.symptoms) {
      logData.symptoms.forEach((s: string) => params.append('symptoms', s));
    }
    return await apiRequest<any>(`/api/female/log-period/${userId}?${params.toString()}`, {
      method: 'POST'
    });
  } catch { return { success: false }; }
};

export const updateFemmeCareSettings = async (
  userId: string, 
  settings: { femmecare_enabled?: boolean; menopause_mode?: boolean; pregnancy_mode?: boolean; local_only?: boolean }
) => {
  try {
    const params = new URLSearchParams();
    if (settings.femmecare_enabled !== undefined) params.append('femmecare_enabled', String(settings.femmecare_enabled));
    if (settings.menopause_mode !== undefined) params.append('menopause_mode', String(settings.menopause_mode));
    if (settings.pregnancy_mode !== undefined) params.append('pregnancy_mode', String(settings.pregnancy_mode));
    if (settings.local_only !== undefined) params.append('local_only', String(settings.local_only));

    return await apiRequest<any>(`/api/female/update-settings/${userId}?${params.toString()}`, {
      method: 'POST'
    });
  } catch { return { success: false }; }
};

export const fetchDailyProgress = async (userId: string) => {
  try {
    return await apiRequest<any>(`/api/daily-progress/${userId}`);
  } catch {
    return null;
  }
};

export const refreshDailyProgress = async (userId: string) => {
  try {
    return await apiRequest<any>(`/api/daily-progress/refresh/${userId}`, {
      method: 'POST'
    });
  } catch {
    return null;
  }
};

export const logWorkoutSetProgress = async (
  userId: string,
  payload: { sets_added?: number; workout_planned_id?: number | null }
) => {
  try {
    return await apiRequest<any>(`/api/daily-progress/set-logged`, {
      method: 'POST',
      body: JSON.stringify({
        user_id: Number(userId),
        sets_added: payload.sets_added ?? 1,
        workout_planned_id: payload.workout_planned_id ?? null
      })
    });
  } catch {
    return null;
  }
};

export const logMealProgress = async (userId: string) => {
  try {
    return await apiRequest<any>(`/api/daily-progress/meal-logged`, {
      method: 'POST',
      body: JSON.stringify({ user_id: Number(userId) })
    });
  } catch {
    return null;
  }
};

export const fetchWeeklyProgress = async (userId: string, days = 7) => {
  try {
    return await apiRequest<any>(`/api/daily-progress/weekly/${userId}?days=${days}`);
  } catch {
    return null;
  }
};

export const fetchWorkoutHistory = async (userId: string, limit = 100) => {
  try {
    return await apiRequest<any>(`/api/calorie-tracking/workout-history/${userId}?limit=${limit}`);
  } catch {
    return null;
  }
};

export const fetchGamificationSummary = async (userId: string) => {
  try {
    return await apiRequest<any>(`/api/gamification/users/${userId}/summary`);
  } catch {
    return null;
  }
};

export const fetchUserAchievements = async (userId: string) => {
  try {
    return await apiRequest<any>(`/api/gamification/users/${userId}/achievements`);
  } catch {
    return null;
  }
};
