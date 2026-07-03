import { MealAnalysis, WorkoutPlan, BodyTypeAdvice, BodyGoal, BioProfile, DailyTask } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');

async function postAI<T>(endpoint: string, body: unknown): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}/api/ai/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'AI request failed' }));
      throw new Error(error.detail || 'AI request failed');
    }

    return response.json();
  } catch (e) {
    throw e;
  }
}

export interface FoodItem {
  name: string;
  portion: string;
  calories: number;
  protein: number;
  carbs: number;
  fats: number;
  isHealthy: boolean;
}

export interface EnhancedMealAnalysis {
  mealName: string;
  totalCalories: number;
  totalProtein: number;
  totalCarbs: number;
  totalFats: number;
  items: FoodItem[];
  recommendation: string;
  goalAlignment: string;
  mealRating: number;
  healthTips: string[];
  alternatives: string[];
}

export interface GeneratedMealEntry {
  day_of_week: number;
  meal_slot: string;
  food_name: string;
  serving_size: string;
  calories: number;
  protein: number;
  carbs: number;
  fats: number;
}

export const generateDailyTasks = async (profile: BioProfile): Promise<DailyTask[]> => {
  return postAI<DailyTask[]>('daily-tasks', profile);
};

export const generateWorkoutPlan = async (goal: string, level: string, duration: number): Promise<WorkoutPlan> => {
  return postAI<WorkoutPlan>('workout-plan', { goal, level, duration });
};

export const analyzeMealImageEnhanced = async (
  base64Image: string,
  userGoal?: string,
  dailyCaloriesRemaining?: number
): Promise<EnhancedMealAnalysis> => {
  return postAI<EnhancedMealAnalysis>('meal-image', {
    image_base64: base64Image,
    user_goal: userGoal,
    daily_calories_remaining: dailyCaloriesRemaining,
  });
};

export const analyzeMealImage = async (base64Image: string): Promise<MealAnalysis> => {
  const result = await analyzeMealImageEnhanced(base64Image);
  return {
    meal_log_id: Date.now().toString(),
    foodName: result.mealName,
    calories: result.totalCalories,
    protein: result.totalProtein,
    carbs: result.totalCarbs,
    fats: result.totalFats,
    recommendation: result.recommendation,
  };
};

export const getBodyTypeAdvice = async (goal: BodyGoal): Promise<BodyTypeAdvice> => {
  return postAI<BodyTypeAdvice>('body-advice', { goal });
};

export const generateWeeklyMealPlan = async (profile: {
  goal?: string;
  dailyCalories?: number;
  dietaryRestrictions?: string[];
  allergies?: string[];
}): Promise<GeneratedMealEntry[]> => {
  const entries = await postAI<GeneratedMealEntry[]>('weekly-meal-plan', {
    goal: profile.goal,
    dailyCalories: profile.dailyCalories,
    dietaryRestrictions: profile.dietaryRestrictions || [],
    allergies: profile.allergies || [],
  });

  return entries.length === 28 ? entries : generateMockMealPlan(profile);
};

export const sendCoachMessage = async (
  message: string,
  profile: Record<string, unknown> = {},
  history: Array<{ role: string; text: string }> = []
): Promise<string> => {
  const response = await postAI<{ text: string }>('chat', { message, profile, history });
  return response.text;
};

export const createChat = () => ({
  sendMessage: async ({ message }: { message: string }) => ({
    text: await sendCoachMessage(message),
  }),
});

const generateMockMealPlan = (profile: { goal?: string; dailyCalories?: number }): GeneratedMealEntry[] => {
  const mealsBySlot: Record<string, [string, string, number, number, number, number][]> = {
    breakfast: [
      ['Oatmeal with Berries', '1 bowl', 350, 12, 58, 6],
      ['Scrambled Eggs & Toast', '2 eggs + 2 slices', 420, 28, 30, 18],
      ['Greek Yogurt Parfait', '250g', 320, 20, 42, 8],
      ['Smoothie Bowl', '400ml', 380, 15, 60, 10],
      ['Protein Pancakes', '3 pancakes', 400, 30, 45, 12],
      ['Avocado Toast', '2 slices', 360, 12, 35, 20],
      ['Granola with Milk', '1 cup', 340, 14, 55, 9],
    ],
    lunch: [
      ['Grilled Chicken Salad', '400g', 450, 40, 15, 22],
      ['Turkey Wrap', '1 wrap', 480, 35, 40, 18],
      ['Quinoa Buddha Bowl', '500g', 420, 18, 55, 14],
      ['Tuna Sandwich', '1 sandwich', 440, 32, 45, 15],
      ['Lentil Soup', '500ml', 380, 22, 52, 10],
      ['Caesar Salad with Chicken', '450g', 460, 38, 18, 26],
      ['Beef Stir-fry', '400g', 490, 42, 35, 20],
    ],
    dinner: [
      ['Salmon with Rice', '200g + 1 cup', 520, 42, 50, 16],
      ['Chicken Pasta', '400g', 550, 38, 55, 18],
      ['Vegetable Curry', '500g', 420, 16, 60, 14],
      ['Beef Tacos', '3 tacos', 510, 36, 45, 22],
      ['Baked Cod & Potatoes', '300g + 200g', 470, 40, 40, 14],
      ['Stir-fry Tofu & Rice', '450g', 410, 22, 55, 12],
      ['Lean Steak & Veggies', '200g + 300g', 500, 48, 25, 22],
    ],
    snack: [
      ['Protein Shake', '1 scoop + milk', 180, 25, 12, 3],
      ['Apple with Almond Butter', '1 apple + 2 tbsp', 220, 6, 28, 10],
      ['Mixed Nuts', '1 handful', 170, 5, 6, 15],
      ['Cottage Cheese & Pineapple', '200g', 160, 22, 12, 4],
      ['Rice Cakes with Hummus', '3 cakes + 3 tbsp', 190, 7, 25, 8],
      ['Greek Yogurt', '200g', 140, 18, 8, 4],
      ['Protein Bar', '1 bar', 200, 20, 22, 6],
    ],
  };
  const entries: GeneratedMealEntry[] = [];
  for (let day = 0; day < 7; day++) {
    for (const slot of ['breakfast', 'lunch', 'dinner', 'snack'] as const) {
      const pool = mealsBySlot[slot];
      const [name, serving, cal, prot, carbs, fats] = pool[day % pool.length];
      entries.push({ day_of_week: day, meal_slot: slot, food_name: name, serving_size: serving, calories: cal, protein: prot, carbs, fats });
    }
  }
  return entries;
};
