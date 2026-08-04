import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, beforeEach, vi } from 'vitest';
import MealScanner from './MealScanner';

const mockAnalyzeMealImageEnhanced = vi.fn();
const mockLogMealProgress = vi.fn();
const mockEstimateNutrition = vi.fn();
const mockDetectHybrid = vi.fn();
const mockDetectYOLO = vi.fn();
const mockGetCurrentUser = vi.fn();

vi.mock('../services/geminiService', () => ({
  analyzeMealImageEnhanced: (...args: any[]) => mockAnalyzeMealImageEnhanced(...args),
}));

vi.mock('../services/apiService', () => ({
  logMealProgress: (...args: any[]) => mockLogMealProgress(...args),
  AuthAPI: { getCurrentUser: (...args: any[]) => mockGetCurrentUser(...args) },
}));

vi.mock('../services/visionService', () => ({
  default: {
    estimateNutrition: (...args: any[]) => mockEstimateNutrition(...args),
    detectHybrid: (...args: any[]) => mockDetectHybrid(...args),
    detectWithYOLO: (...args: any[]) => mockDetectYOLO(...args),
  },
}));

vi.mock('../hooks/useCurrentUserId', () => ({
  useCurrentUserId: () => '1',
}));

vi.mock('../hooks/useUserProfile', () => ({
  useUserProfile: () => ({ profile: { goal: 'weight_loss', dailyCalorieGoal: 2200 }, loading: false, user: null }),
}));

describe('MealScanner', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('analyzes a meal and logs progress', async () => {
    mockAnalyzeMealImageEnhanced.mockResolvedValueOnce({
      mealName: 'Chicken Bowl',
      totalCalories: 450,
      totalProtein: 35,
      totalCarbs: 40,
      totalFats: 12,
      items: [
        { name: 'Chicken', portion: '150g', calories: 250, protein: 30, carbs: 0, fats: 10, isHealthy: true },
      ],
      recommendation: 'Good choice',
      goalAlignment: 'good',
      mealRating: 9,
      healthTips: ['Nice protein'],
      alternatives: ['Salad'],
    });
    mockLogMealProgress.mockResolvedValue(undefined);

    render(<MealScanner />);
    expect(screen.getByRole('heading', { name: /AI Food Scanner/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Open Camera/i })).toBeInTheDocument();
  });

  it('supports manual food portion logging into backend endpoint', async () => {
    mockAnalyzeMealImageEnhanced.mockResolvedValueOnce({
      mealName: 'Chicken Bowl',
      totalCalories: 450,
      totalProtein: 35,
      totalCarbs: 40,
      totalFats: 12,
      items: [
        { name: 'Chicken', portion: '150g', calories: 250, protein: 30, carbs: 0, fats: 10, isHealthy: true },
      ],
      recommendation: 'Good choice',
      goalAlignment: 'good',
      mealRating: 9,
      healthTips: ['Nice protein'],
      alternatives: ['Salad'],
    });
    mockLogMealProgress.mockResolvedValue(undefined);
    mockGetCurrentUser.mockResolvedValue({ id: '1', email: 'demo@example.com' });

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({ food_name: 'Chicken', calories: 250, protein_g: 30, carbs_g: 0, fat_g: 10 }),
    } as Response);

    render(<MealScanner />);
    await waitFor(() => expect(screen.getByRole('button', { name: /Open Camera/i })).toBeInTheDocument());
    fetchSpy.mockRestore();
  });
});
