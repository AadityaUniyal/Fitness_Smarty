import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, beforeEach, vi } from 'vitest';
import WorkoutAssistant from './WorkoutAssistant';

const mockGenerateWorkoutPlan = vi.fn();
const mockFetchDailyCoach = vi.fn();
const mockLogWorkoutSetProgress = vi.fn();

vi.mock('../services/geminiService', () => ({
  generateWorkoutPlan: (...args: any[]) => mockGenerateWorkoutPlan(...args),
}));

vi.mock('../services/apiService', () => ({
  logWorkoutSetProgress: (...args: any[]) => mockLogWorkoutSetProgress(...args),
}));

vi.mock('../hooks/useCurrentUserId', () => ({
  useCurrentUserId: () => '1',
}));

vi.mock('../hooks/useUserProfile', () => ({
  useUserProfile: () => ({ profile: { primary_goal: 'muscle_gain', activity_level: 'moderate' }, loading: false, user: null }),
}));

vi.mock('../services/api', () => ({
  fetchDailyCoach: (...args: any[]) => mockFetchDailyCoach(...args),
}));

describe('WorkoutAssistant', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('generates a workout plan from the AI service', async () => {
    mockFetchDailyCoach.mockResolvedValueOnce({ workout_recommendation: { exercises: [] } });
    mockGenerateWorkoutPlan.mockResolvedValueOnce({
      title: 'Hybrid Session',
      duration: '45 mins',
      intensity: 'Medium',
      exercises: [
        { name: 'Squat', sets: 3, reps: '10', description: 'desc', targeted_muscle: 'Legs', difficulty: 'Intermediate', equipment: 'Barbell' },
      ],
    });

    render(<WorkoutAssistant />);
    fireEvent.click(screen.getByRole('button', { name: /Generate Hybrid Session/i }));

    await waitFor(() => expect(mockGenerateWorkoutPlan).toHaveBeenCalled());
    expect(screen.getByText(/Neural Trainer/i)).toBeInTheDocument();
  });

  it('logs a workout session through the backend sync path', async () => {
    mockFetchDailyCoach.mockResolvedValueOnce({
      workout_recommendation: {
        type: 'single',
        exercises: [
          { name: 'Squat', sets: 3, reps: '10', reasoning: 'Work hard', targeted_muscle: 'Legs', difficulty: 'Intermediate', equipment: 'Barbell' },
        ],
      },
    });
    mockGenerateWorkoutPlan.mockResolvedValueOnce({
      title: 'Hybrid Session',
      duration: '45 mins',
      intensity: 'Medium',
      exercises: [
        { name: 'Squat', sets: 3, reps: '10', description: 'desc', targeted_muscle: 'Legs', difficulty: 'Intermediate', equipment: 'Barbell' },
      ],
    });
    mockLogWorkoutSetProgress.mockResolvedValue(undefined);
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({}),
    } as Response);

    render(<WorkoutAssistant />);
    fireEvent.click(screen.getByRole('button', { name: /Generate Hybrid Session/i }));
    await waitFor(() => expect(mockGenerateWorkoutPlan).toHaveBeenCalled());

    fetchSpy.mockRestore();
  });
});
