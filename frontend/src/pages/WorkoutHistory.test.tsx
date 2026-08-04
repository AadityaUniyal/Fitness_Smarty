import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, beforeEach, vi } from 'vitest';
import WorkoutHistory from './WorkoutHistory';

const mockFetchWorkoutHistory = vi.fn();

vi.mock('../services/apiService', () => ({
  fetchWorkoutHistory: (...args: any[]) => mockFetchWorkoutHistory(...args),
}));

vi.mock('../hooks/useCurrentUserId', () => ({
  useCurrentUserId: () => '1',
}));

describe('WorkoutHistory', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('renders stored workout history and fetches backend history', async () => {
    const storedWorkout = {
      name: 'Test Session',
      duration: 30,
      caloriesBurned: 250,
      exercisesCompleted: 3,
      exercisesTotal: 4,
      timestamp: new Date().toISOString(),
      goal: 'muscle_gain',
    };
    localStorage.setItem('smarty_workout_logs', JSON.stringify([storedWorkout]));
    mockFetchWorkoutHistory.mockResolvedValueOnce({ workouts: [storedWorkout] });

    render(<WorkoutHistory />);

    await waitFor(() => expect(mockFetchWorkoutHistory).toHaveBeenCalledWith('1', 200));
    expect(screen.getByText(/Workout History/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Test Session/i).length).toBeGreaterThan(0);
  });
});
