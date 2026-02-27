
import { GoogleGenAI, Type, Modality } from "@google/genai";
import { MealAnalysis, WorkoutPlan, BodyTypeAdvice, BodyGoal, BioProfile, DailyTask } from "./types";

export const generateDailyTasks = async (profile: BioProfile): Promise<DailyTask[]> => {
  const apiKey = import.meta.env.VITE_GEMINI_API_KEY || '';
  const ai = new GoogleGenAI({ apiKey });
  const response = await ai.models.generateContent({
    model: 'gemini-2.0-flash',
    contents: `Based on this Bio-Profile: Age ${profile.age}, ${profile.gender}, Weight ${profile.weight}kg, Height ${profile.height}cm, Goal ${profile.goal}.
    Generate a 5-item daily "Operational Checklist" for fitness success. Include specific times and priorities.`,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.ARRAY,
        items: {
          type: Type.OBJECT,
          properties: {
            id: { type: Type.STRING },
            type: { type: Type.STRING, enum: ['hydration', 'nutrition', 'activity', 'recovery'] },
            label: { type: Type.STRING },
            time: { type: Type.STRING },
            priority: { type: Type.STRING, enum: ['High', 'Medium', 'Low'] },
            completed: { type: Type.BOOLEAN }
          },
          required: ["id", "type", "label", "time", "priority", "completed"]
        }
      }
    }
  });

  try {
    return JSON.parse(response.text || '[]');
  } catch (e) {
    return [];
  }
};

export const generateWorkoutPlan = async (goal: string, level: string, duration: number): Promise<WorkoutPlan> => {
  const apiKey = import.meta.env.VITE_GEMINI_API_KEY || '';

  // Dev fallback if no API key is provided
  if (!apiKey) {
    console.warn("No Gemini API key found. Using mock workout plan for development.");
    return new Promise(resolve => setTimeout(() => resolve({
      title: `${goal} Protocol Beta`,
      duration: `${duration} mins`,
      intensity: 'Medium',
      exercises: [
        {
          name: "Holographic Squats",
          sets: 4,
          reps: "10-12",
          description: "Engage your neural core while performing a full range of motion squat.",
          targeted_muscle: "Quadriceps & Glutes",
          difficulty: "Intermediate",
          equipment: "Bodyweight or Dumbbells"
        },
        {
          name: "Kinetic Push-ups",
          sets: 3,
          reps: "To Failure",
          description: "Maintain core tension and explode upwards.",
          targeted_muscle: "Chest & Triceps",
          difficulty: "Intermediate",
          equipment: "Bodyweight"
        }
      ],
      nutrition_advice: {
        pre_workout: "1/2 banana with almond butter 45 mins prior.",
        post_workout: "Protein shake with 30g whey and a handful of berries.",
        recommended_foods: ["Lean Chicken Breast", "Sweet Potato", "Greek Yogurt", "Spinach"],
        hydration_tip: "Drink 16oz of water 2 hours before, and 8oz every 15 mins during the session."
      }
    }), 1500));
  }

  const ai = new GoogleGenAI({ apiKey });
  const response = await ai.models.generateContent({
    model: 'gemini-2.0-flash',
    contents: `Generate a training protocol and paired nutrition advice. Goal: ${goal}. Profile: ${level}. Time: ${duration}min.
    Include specific pre-workout fuel, post-workout recovery food, a list of general recommended foods for this goal, and a hydration tip.`,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          title: { type: Type.STRING },
          duration: { type: Type.STRING },
          intensity: { type: Type.STRING },
          exercises: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                name: { type: Type.STRING },
                sets: { type: Type.NUMBER },
                reps: { type: Type.STRING },
                description: { type: Type.STRING },
                targeted_muscle: { type: Type.STRING },
                difficulty: { type: Type.STRING },
                equipment: { type: Type.STRING },
                video_url: { type: Type.STRING }
              },
              required: ["name", "sets", "reps", "description", "targeted_muscle", "difficulty", "equipment"]
            }
          },
          nutrition_advice: {
            type: Type.OBJECT,
            properties: {
              pre_workout: { type: Type.STRING },
              post_workout: { type: Type.STRING },
              recommended_foods: { type: Type.ARRAY, items: { type: Type.STRING } },
              hydration_tip: { type: Type.STRING }
            },
            required: ["pre_workout", "post_workout", "recommended_foods", "hydration_tip"]
          }
        },
        required: ["title", "exercises", "duration", "intensity", "nutrition_advice"]
      }
    }
  });

  return JSON.parse(response.text || '{}');
};

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
  goalAlignment: string; // 'good' | 'over' | 'under'
  mealRating: number; // 1-10
  healthTips: string[];
  alternatives: string[];
}

export const analyzeMealImageEnhanced = async (
  base64Image: string,
  userGoal?: string,
  dailyCaloriesRemaining?: number
): Promise<EnhancedMealAnalysis> => {
  const apiKey = import.meta.env.VITE_GEMINI_API_KEY || '';
  if (!apiKey) throw new Error('No Gemini API key configured');
  const ai = new GoogleGenAI({ apiKey });

  const goalContext = userGoal
    ? `The user's fitness goal is: ${userGoal}. ${dailyCaloriesRemaining ? `They have ${dailyCaloriesRemaining} calories remaining today.` : ''}`
    : '';

  const response = await ai.models.generateContent({
    model: 'gemini-2.0-flash',
    contents: {
      parts: [
        { inlineData: { mimeType: 'image/jpeg', data: base64Image } },
        {
          text: `You are an expert nutritionist AI. Analyze this meal image in detail. ${goalContext}

Identify every food item visible, estimate portion sizes, and calculate nutritional info.
Then give a personalized recommendation based on the user's goal.

Respond in JSON matching this exact schema.` }
      ]
    },
    config: {
      responseMimeType: 'application/json',
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          mealName: { type: Type.STRING },
          totalCalories: { type: Type.NUMBER },
          totalProtein: { type: Type.NUMBER },
          totalCarbs: { type: Type.NUMBER },
          totalFats: { type: Type.NUMBER },
          items: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                name: { type: Type.STRING },
                portion: { type: Type.STRING },
                calories: { type: Type.NUMBER },
                protein: { type: Type.NUMBER },
                carbs: { type: Type.NUMBER },
                fats: { type: Type.NUMBER },
                isHealthy: { type: Type.BOOLEAN }
              },
              required: ['name', 'portion', 'calories', 'protein', 'carbs', 'fats', 'isHealthy']
            }
          },
          recommendation: { type: Type.STRING },
          goalAlignment: { type: Type.STRING },
          mealRating: { type: Type.NUMBER },
          healthTips: { type: Type.ARRAY, items: { type: Type.STRING } },
          alternatives: { type: Type.ARRAY, items: { type: Type.STRING } },
        },
        required: ['mealName', 'totalCalories', 'totalProtein', 'totalCarbs', 'totalFats', 'items', 'recommendation', 'goalAlignment', 'mealRating', 'healthTips', 'alternatives']
      }
    }
  });

  return JSON.parse(response.text || '{}');
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
  const apiKey = import.meta.env.VITE_GEMINI_API_KEY || '';
  const ai = new GoogleGenAI({ apiKey });
  const response = await ai.models.generateContent({
    model: 'gemini-2.0-flash',
    contents: `Compute optimal biofuel for: ${goal}.`,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          title: { type: Type.STRING },
          description: { type: Type.STRING },
          recommendedMacros: {
            type: Type.OBJECT,
            properties: {
              protein: { type: Type.STRING },
              carbs: { type: Type.STRING },
              fats: { type: Type.STRING }
            }
          },
          foodsToFocus: { type: Type.ARRAY, items: { type: Type.STRING } },
          foodsToAvoid: { type: Type.ARRAY, items: { type: Type.STRING } }
        }
      }
    }
  });
  return JSON.parse(response.text || '{}');
};

export const createChat = () => {
  const apiKey = import.meta.env.VITE_GEMINI_API_KEY || '';
  const ai = new GoogleGenAI({ apiKey });
  return ai.chats.create({
    model: 'gemini-2.0-flash',
    config: {
      systemInstruction: `You are the SMARTY AI Neural Oracle. Expert in biomechanics and nutrition.`,
    },
  });
};
