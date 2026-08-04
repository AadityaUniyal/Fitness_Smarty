import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import WeeklyReview from './WeeklyReview';

const mockFetchWeeklyProgress = vi.fn();
const mockUserId = vi.fn(() => '42');

vi.mock('../services/apiService', () => ({
  fetchWeeklyProgress: (...args: any[]) => mockFetchWeeklyProgress(...args),
}));

vi.mock('../hooks/useCurrentUserId', () => ({
  useCurrentUserId: () => mockUserId(),
}));

describe('WeeklyReview', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    localStorage.setItem('smarty_workout_logs', JSON.stringify([
      { timestamp: new Date().toISOString(), duration: 30, caloriesBurned: 200 },
    ]));
    localStorage.setItem('smarty_meal_logs', JSON.stringify([
      { timestamp: new Date().toISOString(), totalCalories: 500, totalProtein: 35 },
    ]));
  });

  it('uses backend rollup data when available', async () => {
    mockFetchWeeklyProgress.mockResolvedValueOnce({
      summary: { avg_daily_calories: 1800, avg_daily_burn: 260, avg_daily_protein: 120 },
      daily: [
        { calories_consumed: 1500, protein_consumed: 110, sets_completed: 4 },
        { calories_consumed: 1600, protein_consumed: 115, sets_completed: 3 },
      ],
    });

    render(<WeeklyReview />);

    await waitFor(() => expect(mockFetchWeeklyProgress).toHaveBeenCalledWith('42', 7));
    expect(screen.getByText(/Weekly Review/i)).toBeInTheDocument();
    expect(screen.getByText(/Daily Calories/i)).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Nutrition/i })).toBeInTheDocument();
  });

  it('switches the report window and refetches backend progress', async () => {
    mockFetchWeeklyProgress.mockResolvedValue({
      summary: { avg_daily_calories: 1800, avg_daily_burn: 260, avg_daily_protein: 120 },
      daily: [],
    });

    render(<WeeklyReview />);

    await waitFor(() => expect(mockFetchWeeklyProgress).toHaveBeenCalledWith('42', 7));

    fireEvent.click(screen.getByRole('button', { name: /14d/i }));

    await waitFor(() => expect(mockFetchWeeklyProgress).toHaveBeenCalledWith('42', 14));
  });
});
