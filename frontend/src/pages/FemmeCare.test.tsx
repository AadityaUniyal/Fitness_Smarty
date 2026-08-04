import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, expect, it, beforeEach, vi } from 'vitest';
import FemmeCare from './FemmeCare';

const mockFetchFemmeCareAdvice = vi.fn();
const mockLogPeriod = vi.fn();
const mockUpdateFemmeCareSettings = vi.fn();

vi.mock('../services/apiService', () => ({
  fetchFemmeCareAdvice: (...args: any[]) => mockFetchFemmeCareAdvice(...args),
  logPeriod: (...args: any[]) => mockLogPeriod(...args),
}));

vi.mock('../services/api', () => ({
  updateFemmeCareSettings: (...args: any[]) => mockUpdateFemmeCareSettings(...args),
}));

vi.mock('../hooks/useUserProfile', () => ({
  useUserProfile: () => ({
    user: { id: '77', email: 'femme@example.com' },
    profile: { femmecare_enabled: false },
    loading: false,
  }),
}));

describe('FemmeCare', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockFetchFemmeCareAdvice.mockResolvedValue({
      phase: 'Follicular',
      advice: {
        training: 'Go moderate today.',
        nutrition: 'Prioritize iron and magnesium.',
        intensity_limit: 'Moderate',
        bio_context: 'Follicular phase support.',
        focus: 'Build momentum.',
      },
      recommended_exercises: [
        { id: '1', name: 'Goblet Squat', calories_per_min: 8, muscle: 'Quads', difficulty: 'Beginner', equipment: 'Dumbbell', description: 'Controlled lower body work.' },
      ],
      user_profile: {
        femmecare_enabled: false,
        local_only: false,
        menopause_mode: false,
        pregnancy_mode: false,
      },
    });
    mockUpdateFemmeCareSettings.mockResolvedValue({});
    mockLogPeriod.mockResolvedValue({});
  });

  it('loads cycle guidance and shows recommendation cards', async () => {
    render(<FemmeCare />);

    await waitFor(() => expect(mockFetchFemmeCareAdvice).toHaveBeenCalledWith('77'));
    expect(screen.getByRole('heading', { name: /AURA PINK/i })).toBeInTheDocument();
    expect(screen.getByText(/Go moderate today\./i)).toBeInTheDocument();
    expect(screen.getByText(/Prioritize iron and magnesium\./i)).toBeInTheDocument();
    expect(screen.getByText(/Goblet Squat/i)).toBeInTheDocument();
  });

  it('syncs femme care settings and logs a cycle entry', async () => {
    render(<FemmeCare />);

    await waitFor(() => expect(mockFetchFemmeCareAdvice).toHaveBeenCalled());

    fireEvent.click(screen.getByLabelText(/Enable cycle support/i));
    await waitFor(() => expect(mockUpdateFemmeCareSettings).toHaveBeenCalled());

    fireEvent.click(screen.getByRole('button', { name: /Log New Cycle/i }));
    fireEvent.click(screen.getByRole('button', { name: /Save Entry/i }));

    await waitFor(() => expect(mockLogPeriod).toHaveBeenCalledWith(
      '77',
      expect.objectContaining({
        mood: 'Neutral',
        flow_intensity: 'Medium',
        symptoms: [],
      }),
    ));
  });
});
