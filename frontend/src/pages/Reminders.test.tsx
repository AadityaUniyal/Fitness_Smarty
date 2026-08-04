import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, beforeEach, vi } from 'vitest';
import Reminders from './Reminders';

const mockGetReminders = vi.fn();
const mockSaveReminders = vi.fn();
const mockRequestPermission = vi.fn();
const mockHasPermission = vi.fn();

vi.mock('../services/notificationService', () => ({
  getReminders: (...args: any[]) => mockGetReminders(...args),
  saveReminders: (...args: any[]) => mockSaveReminders(...args),
  requestNotificationPermission: (...args: any[]) => mockRequestPermission(...args),
  hasNotificationPermission: (...args: any[]) => mockHasPermission(...args),
}));

describe('Reminders', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockGetReminders.mockReturnValue([
      {
        id: 'breakfast',
        label: 'Log Breakfast',
        description: 'Time to fuel up',
        time: '08:00',
        days: [1, 2, 3, 4, 5],
        enabled: true,
        icon: 'sun',
      },
    ]);
  });

  it('renders reminders and persists updates', async () => {
    mockHasPermission.mockReturnValue(false);

    render(<Reminders />);

    expect(screen.getByRole('heading', { name: /^Reminders$/i })).toBeInTheDocument();
    expect(screen.getByText(/Log Breakfast/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Enable$/i })).toBeInTheDocument();

    fireEvent.click(screen.getByText(/Tue/i));

    await waitFor(() => expect(mockSaveReminders).toHaveBeenCalled());
  });

  it('requests notification permission and enables test notifications', async () => {
    mockHasPermission.mockReturnValue(false);
    mockRequestPermission.mockResolvedValue(true);
    mockGetReminders.mockReturnValue([
      {
        id: 'breakfast',
        label: 'Log Breakfast',
        description: 'Time to fuel up',
        time: '08:00',
        days: [1, 2, 3, 4, 5],
        enabled: true,
        icon: 'sun',
      },
    ]);

    render(<Reminders />);
    fireEvent.click(screen.getByRole('button', { name: /^Enable$/i }));

    await waitFor(() => expect(mockRequestPermission).toHaveBeenCalled());
  });
});
