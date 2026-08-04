import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, beforeEach, vi } from 'vitest';
import Dashboard from './Dashboard';

const mockNavigate = vi.fn();
const mockFetchRecoveryScore = vi.fn();
const mockFetchNeuralIntegrity = vi.fn();
const mockFetchMissionBriefing = vi.fn();
const mockFetchDailyCoach = vi.fn();
const mockFetchExplainableCoach = vi.fn();
const mockFetchCoachHistory = vi.fn();
const mockFetchDailyProgress = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('../hooks/useUserProfile', () => ({
  useUserProfile: () => ({
    user: { id: '1', user_id: '1' },
    profile: {
      gender: 'Female',
      femmecareEnabled: true,
      dailyCalorieGoal: 2200,
      proteinGoal: 120,
      workoutGoalMins: 45,
      age: 29,
      height: 170,
      weight: 65,
      goal: 'muscle_gain',
      activityLevel: 'moderate',
    },
  }),
}));

vi.mock('../services/apiService', () => ({
  fetchRecoveryScore: (...args: any[]) => mockFetchRecoveryScore(...args),
  fetchNeuralIntegrity: (...args: any[]) => mockFetchNeuralIntegrity(...args),
  fetchMissionBriefing: (...args: any[]) => mockFetchMissionBriefing(...args),
  fetchDailyCoach: (...args: any[]) => mockFetchDailyCoach(...args),
  fetchExplainableCoach: (...args: any[]) => mockFetchExplainableCoach(...args),
  fetchCoachHistory: (...args: any[]) => mockFetchCoachHistory(...args),
  fetchDailyProgress: (...args: any[]) => mockFetchDailyProgress(...args),
}));

vi.mock('../components/DailyChecklist', () => ({
  default: () => <div>Daily Checklist Mock</div>,
}));

vi.mock('../components/SmartNextMove', () => ({
  default: () => <div>Smart Next Move Mock</div>,
}));

vi.mock('../components/Reveal', () => ({
  Reveal: ({ children }: any) => <div>{children}</div>,
}));

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    localStorage.setItem('smarty_workout_logs', JSON.stringify([
      { name: 'Session', duration: 30, caloriesBurned: 250, exercisesCompleted: 3, exercisesTotal: 4, timestamp: new Date().toISOString(), goal: 'muscle_gain' },
    ]));
    localStorage.setItem('smarty_meal_logs', JSON.stringify([
      { mealName: 'Meal', totalCalories: 500, totalProtein: 35, totalCarbs: 40, totalFats: 12, mealType: 'lunch', timestamp: new Date().toISOString() },
    ]));
  });

  it('renders the main dashboard summary and femmecare sidebar', async () => {
    mockFetchRecoveryScore.mockResolvedValue({ score: 91 });
    mockFetchNeuralIntegrity.mockResolvedValue({ focus_area: 'Recovery', score: 88 });
    mockFetchMissionBriefing.mockResolvedValue({ directive: 'Stay consistent today.' });
    mockFetchDailyCoach.mockResolvedValue({
      daily_tasks: [],
      next_action: { title: 'Hydrate', detail: 'Drink water', route: '/dashboard/hydration' },
      workout_recommendation: { exercises: [] },
      meal_recommendation: { foods: [] },
      gender_mode: 'femmecare',
    });
    mockFetchExplainableCoach.mockResolvedValue({
      recommendation: { title: 'Hydrate', detail: 'Drink water', route: '/dashboard/hydration' },
      confidence_score: 91,
      explanation: ['Energy is steady and hydration is the strongest lever today.'],
      factors: ['Current data supports a steady training day'],
      mode_note: 'FemmeCare is enabled, so cycle-aware nudges are active.',
    });
    mockFetchCoachHistory.mockResolvedValue({
      period_days: 7,
      trend_note: 'Training consistency is trending upward.',
      entries: [
        {
          date: '2026-08-03',
          title: 'Workout completed',
          detail: '4/5 sets logged with steady execution. Nutrition stayed near target.',
          confidence: 94,
          workout_status: 'done',
          progress_percent: 80,
          feedback_count: 1,
        },
      ],
    });
    mockFetchDailyProgress.mockResolvedValue({
      calories: { consumed: 500 },
      protein: { consumed: 35 },
      workout: { sets_completed: 3, sets_planned: 5 },
      check_in: { energy_level: 4, soreness_level: 2 },
    });

    render(<Dashboard />);

    await waitFor(() => expect(mockFetchDailyCoach).toHaveBeenCalled());
    expect(screen.getByRole('heading', { name: /Mission Control/i })).toBeInTheDocument();
    expect(screen.getByText(/Core Synced/i)).toBeInTheDocument();
    expect(screen.getByText(/Daily Checklist Mock/i)).toBeInTheDocument();
    expect(screen.getByText(/Smart Next Move Mock/i)).toBeInTheDocument();
    expect(screen.getByText(/Explainable Coach/i)).toBeInTheDocument();
    expect(screen.getByText(/91% confidence/i)).toBeInTheDocument();
    expect(screen.getByText(/Coach Timeline/i)).toBeInTheDocument();
    expect(screen.getByText(/Training consistency is trending upward/i)).toBeInTheDocument();
    expect(screen.getByText(/Calories Eaten/i)).toBeInTheDocument();
    expect(screen.getByText(/Recent Workouts/i)).toBeInTheDocument();
  });
});
