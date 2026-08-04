import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, expect, it, beforeEach, vi } from 'vitest';
import MealPlanner from './MealPlanner';

const mockGenerateWeeklyMealPlan = vi.fn();

vi.mock('../services/apiService', () => ({
  FoodAPI: {
    getFoodLibrary: vi.fn().mockResolvedValue([]),
  },
}));

vi.mock('../services/geminiService', () => ({
  generateWeeklyMealPlan: (...args: any[]) => mockGenerateWeeklyMealPlan(...args),
}));

vi.mock('../hooks/useUserProfile', () => ({
  useUserProfile: () => ({
    profile: {
      dailyCalorieTarget: 2200,
      goal: 'muscle_gain',
      dietaryPreferences: [],
      allergies: [],
    },
  }),
}));

describe('MealPlanner', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    localStorage.setItem('smarty_access_token', 'token-1');
  });

  it('generates a weekly meal plan from backend AI output', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        entries: [
          { day_of_week: 0, meal_slot: 'breakfast', food_name: 'Protein Oats', serving_size: '1 bowl', calories: 400, protein: 30, carbs: 45, fats: 12 },
          { day_of_week: 0, meal_slot: 'lunch', food_name: 'Chicken Bowl', serving_size: '1 plate', calories: 550, protein: 42, carbs: 50, fats: 18 },
        ],
      }),
    } as Response);
    vi.stubGlobal('fetch', mockFetch);

    render(<MealPlanner />);
    fireEvent.click(screen.getByRole('button', { name: /Generate with AI/i }));

    await waitFor(() => expect(mockFetch).toHaveBeenCalled());
    fireEvent.click(screen.getByRole('button', { name: /^Mon$/i }));
    await waitFor(() => expect(screen.getByText(/Protein Oats/i)).toBeInTheDocument());
    expect(screen.getByText(/950 kcal/i)).toBeInTheDocument();
    expect(mockGenerateWeeklyMealPlan).not.toHaveBeenCalled();
  });

  it('falls back to local AI generation when backend has no plan', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'no plan' }),
    } as Response);
    vi.stubGlobal('fetch', mockFetch);
    mockGenerateWeeklyMealPlan.mockResolvedValue([
      { day_of_week: 0, meal_slot: 'breakfast', food_name: 'Fallback Oats', serving_size: '1 bowl', calories: 300, protein: 15, carbs: 40, fats: 8 },
      { day_of_week: 1, meal_slot: 'lunch', food_name: 'Fallback Chicken', serving_size: '1 plate', calories: 500, protein: 35, carbs: 45, fats: 14 },
      { day_of_week: 2, meal_slot: 'dinner', food_name: 'Fallback Rice', serving_size: '1 bowl', calories: 420, protein: 22, carbs: 48, fats: 10 },
      { day_of_week: 3, meal_slot: 'snack', food_name: 'Fallback Yogurt', serving_size: '1 cup', calories: 180, protein: 12, carbs: 18, fats: 4 },
      { day_of_week: 4, meal_slot: 'breakfast', food_name: 'Fallback Eggs', serving_size: '2 eggs', calories: 250, protein: 18, carbs: 2, fats: 16 },
      { day_of_week: 5, meal_slot: 'lunch', food_name: 'Fallback Salmon', serving_size: '1 fillet', calories: 520, protein: 38, carbs: 20, fats: 24 },
      { day_of_week: 6, meal_slot: 'dinner', food_name: 'Fallback Steak', serving_size: '1 plate', calories: 600, protein: 45, carbs: 10, fats: 30 },
      { day_of_week: 6, meal_slot: 'snack', food_name: 'Fallback Fruit', serving_size: '1 bowl', calories: 100, protein: 1, carbs: 25, fats: 0 },
      { day_of_week: 0, meal_slot: 'snack', food_name: 'Extra 1', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 1, meal_slot: 'breakfast', food_name: 'Extra 2', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 2, meal_slot: 'lunch', food_name: 'Extra 3', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 3, meal_slot: 'dinner', food_name: 'Extra 4', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 4, meal_slot: 'snack', food_name: 'Extra 5', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 5, meal_slot: 'breakfast', food_name: 'Extra 6', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 6, meal_slot: 'lunch', food_name: 'Extra 7', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 0, meal_slot: 'dinner', food_name: 'Extra 8', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 1, meal_slot: 'snack', food_name: 'Extra 9', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 2, meal_slot: 'breakfast', food_name: 'Extra 10', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 3, meal_slot: 'lunch', food_name: 'Extra 11', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 4, meal_slot: 'dinner', food_name: 'Extra 12', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 5, meal_slot: 'snack', food_name: 'Extra 13', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 6, meal_slot: 'breakfast', food_name: 'Extra 14', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 0, meal_slot: 'lunch', food_name: 'Extra 15', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 1, meal_slot: 'dinner', food_name: 'Extra 16', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 2, meal_slot: 'snack', food_name: 'Extra 17', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 3, meal_slot: 'breakfast', food_name: 'Extra 18', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 4, meal_slot: 'lunch', food_name: 'Extra 19', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 5, meal_slot: 'dinner', food_name: 'Extra 20', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 6, meal_slot: 'snack', food_name: 'Extra 21', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 1, meal_slot: 'breakfast', food_name: 'Extra 22', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 2, meal_slot: 'lunch', food_name: 'Extra 23', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 3, meal_slot: 'dinner', food_name: 'Extra 24', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 4, meal_slot: 'snack', food_name: 'Extra 25', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 5, meal_slot: 'breakfast', food_name: 'Extra 26', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 6, meal_slot: 'lunch', food_name: 'Extra 27', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
      { day_of_week: 0, meal_slot: 'dinner', food_name: 'Extra 28', serving_size: '1', calories: 50, protein: 2, carbs: 5, fats: 1 },
    ]);

    render(<MealPlanner />);
    fireEvent.click(screen.getByRole('button', { name: /Generate with AI/i }));

    await waitFor(() => expect(mockGenerateWeeklyMealPlan).toHaveBeenCalled());
    fireEvent.click(screen.getByRole('button', { name: /^Mon$/i }));
    expect(screen.getByText(/Fallback Oats/i)).toBeInTheDocument();
  });
});
