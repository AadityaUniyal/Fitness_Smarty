/**
 * API Service Layer for Backend Communication
 * Provides type-safe methods for all backend API endpoints
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Helper function for API requests
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  
  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const config: RequestInit = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

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
    return apiRequest<UserGoal>(`/api/goals/${goalId}`, {
      method: 'PUT',
      body: JSON.stringify(goalData),
    });
  },

  async validateGoal(goalId: string): Promise<GoalValidation> {
    return apiRequest<GoalValidation>(`/api/goals/${goalId}/validate`);
  },

  async getProgress(userId: string): Promise<ProgressMetrics> {
    return apiRequest<ProgressMetrics>(`/api/users/${userId}/progress`);
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
    return apiRequest(`/api/recommendations/${recommendationId}/read`, {
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
    return apiRequest<Exercise[]>('/exercises/search', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  async getExerciseById(exerciseId: string): Promise<Exercise> {
    return apiRequest<Exercise>(`/exercises/${exerciseId}`);
  },

  async getByDifficulty(difficulty: string): Promise<Exercise[]> {
    return apiRequest<Exercise[]>(`/exercises/difficulty/${difficulty}`);
  },

  async getByMuscleGroup(muscleGroup: string): Promise<Exercise[]> {
    return apiRequest<Exercise[]>(`/exercises/muscle-group/${muscleGroup}`);
  },

  async recommendExercises(params: {
    user_experience_level: string;
    target_muscle_groups?: string[];
    available_equipment?: string[];
    limit?: number;
  }): Promise<Exercise[]> {
    return apiRequest<Exercise[]>('/exercises/recommend', {
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
    return apiRequest<FoodItem[]>(`/nutrition/search${queryString ? `?${queryString}` : ''}`);
  },

  async getFoodLibrary(): Promise<FoodCategory[]> {
    return apiRequest<FoodCategory[]>('/nutrition/library');
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
};
