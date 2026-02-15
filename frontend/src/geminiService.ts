
import { GoogleGenAI, Type, Modality } from "@google/genai";
import { MealAnalysis, WorkoutPlan, BodyTypeAdvice, BodyGoal, BioProfile, DailyTask } from "./types";

export const generateDailyTasks = async (profile: BioProfile): Promise<DailyTask[]> => {
  const apiKey = process.env.API_KEY || ''; // Ensure string
  const ai = new GoogleGenAI({ apiKey });
  const response = await ai.models.generateContent({
    model: 'gemini-3-pro-preview',
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
  const apiKey = process.env.API_KEY || '';
  const ai = new GoogleGenAI({ apiKey });
  const response = await ai.models.generateContent({
    model: 'gemini-3-pro-preview',
    contents: `Generate a training protocol. Goal: ${goal}. Profile: ${level}. Time: ${duration}min.`,
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
          }
        },
        required: ["title", "exercises", "duration", "intensity"]
      }
    }
  });

  return JSON.parse(response.text || '{}');
};

export const analyzeMealImage = async (base64Image: string): Promise<MealAnalysis> => {
  const apiKey = process.env.API_KEY || '';
  const ai = new GoogleGenAI({ apiKey });
  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash-image',
    contents: {
      parts: [
        { inlineData: { mimeType: 'image/jpeg', data: base64Image } },
        { text: "Analyze this meal macros." }
      ]
    },
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          foodName: { type: Type.STRING },
          calories: { type: Type.NUMBER },
          protein: { type: Type.NUMBER },
          carbs: { type: Type.NUMBER },
          fats: { type: Type.NUMBER },
          recommendation: { type: Type.STRING }
        },
        required: ["foodName", "calories", "protein", "carbs", "fats", "recommendation"]
      }
    }
  });

  return JSON.parse(response.text || '{}');
};

export const getBodyTypeAdvice = async (goal: BodyGoal): Promise<BodyTypeAdvice> => {
  const apiKey = process.env.API_KEY || '';
  const ai = new GoogleGenAI({ apiKey });
  const response = await ai.models.generateContent({
    model: 'gemini-3-flash-preview',
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
  const apiKey = process.env.API_KEY || '';
  const ai = new GoogleGenAI({ apiKey });
  return ai.chats.create({
    model: 'gemini-3-pro-preview',
    config: {
      systemInstruction: `You are the SMARTY AI Neural Oracle. Expert in biomechanics and nutrition.`,
    },
  });
};
