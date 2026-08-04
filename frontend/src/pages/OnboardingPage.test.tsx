import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, beforeEach, vi } from 'vitest';
import OnboardingPage from './OnboardingPage';

const mockNavigate = vi.fn();
const mockUpdateProfile = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { full_name: 'Alex', name: 'Alex' },
    updateProfile: (...args: any[]) => mockUpdateProfile(...args),
  }),
}));

describe('OnboardingPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('walks through setup and saves profile data', async () => {
    render(<OnboardingPage />);

    expect(screen.getByRole('heading', { name: /Set the System Up Right/i })).toBeInTheDocument();
    fireEvent.change(screen.getByPlaceholderText(/Alex/i), { target: { value: 'Alex Morgan' } });
    fireEvent.change(screen.getByPlaceholderText(/25/i), { target: { value: '29' } });
    fireEvent.change(screen.getAllByRole('combobox')[0], { target: { value: 'Female' } });
    fireEvent.change(screen.getByPlaceholderText(/70/i), { target: { value: '68' } });
    fireEvent.change(screen.getByPlaceholderText(/175/i), { target: { value: '172' } });

    fireEvent.click(screen.getByRole('button', { name: /Continue/i }));
    fireEvent.click(screen.getByRole('button', { name: /Continue/i }));
    fireEvent.click(screen.getByRole('button', { name: /Continue/i }));

    fireEvent.click(screen.getByRole('button', { name: /Launch Smarty AI/i }));

    await waitFor(() => expect(mockUpdateProfile).toHaveBeenCalled());
    expect(localStorage.getItem('smarty_profile')).toContain('Alex Morgan');
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });
});
