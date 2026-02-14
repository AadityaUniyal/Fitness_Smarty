
export interface BioProfile {
  age?: number;
  gender?: string;
  weight?: number; // Frontend uses 'weight', maps to 'weight_kg' in backend
  height?: number; // Frontend uses 'height', maps to 'height_cm' in backend
  bodyFat?: number;
  activityLevel?: string; // Frontend uses 'activityLevel', maps to 'activity_level' in backend
  goal?: string; // Frontend uses 'goal', maps to 'primary_goal' in backend
  dietary_restrictions?: string[];
  allergies?: string[];
}

export interface DailyTask {
  id: string;
  type: 'hydration' | 'nutrition' | 'activity' | 'recovery';
  label: string;
  time: string;
  completed: boolean;
  priority: 'High' | 'Medium' | 'Low';
}

export interface UserStats {
  id: string;
  name: string;
  level: string;
  xp: number;
  daily_calories: number;
  daily_steps: number;
  active_minutes: number;
  weight: number;
  heart_rate: number;
  bio_profile?: BioProfile;
}

export interface BiometricPoint {
  timestamp: string;
  value: number;
  category: 'weight' | 'heart_rate' | 'sleep' | 'steps';
}

export interface WorkoutPlan {
  title: string;
  exercises: {
    name: string;
    sets: number;
    reps: string;
    description: string;
    targeted_muscle: string;
    difficulty: string;
    equipment: string;
    video_url?: string;
  }[];
  duration: string;
  intensity: 'Low' | 'Medium' | 'High';
}

export interface MealAnalysis {
  meal_log_id: string;
  foodName: string;
  calories: number;
  protein: number;
  carbs: number;
  fats: number;
  recommendation: string;
  detected_foods?: Array<{
    food_id: string;
    name: string;
    estimated_quantity_g: number;
    confidence_score: number;
  }>;
  analysis_confidence?: number;
}

export interface BodyTypeAdvice {
  title: string;
  description: string;
  recommendedMacros: {
    protein: string;
    carbs: string;
    fats: string;
  };
  foodsToFocus: string[];
  foodsToAvoid: string[];
}

export enum NavigationTab {
  DASHBOARD = 'dashboard',
  BIO_PROFILE = 'bio_profile',
  WORKOUTS = 'workouts',
  NUTRITION = 'nutrition',
  LIVE_COACH = 'live_coach',
  CHAT = 'chat'
}

export enum BodyGoal {
  SLIM = 'Slim/Weight Loss',
  ATHLETIC = 'Athletic/Tone',
  BULK = 'Bulking/Mass',
  MAINTAIN = 'Maintenance'
}
