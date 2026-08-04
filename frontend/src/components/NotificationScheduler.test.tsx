import { render } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import NotificationScheduler from './NotificationScheduler';
import * as notificationService from '../services/notificationService';

vi.mock('../services/notificationService', () => ({
  getReminders: vi.fn(() => []),
  startNotificationLoop: vi.fn(() => vi.fn()),
  hasNotificationPermission: vi.fn(() => false),
}));

describe('NotificationScheduler Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does nothing if notification permission is not granted', () => {
    vi.mocked(notificationService.hasNotificationPermission).mockReturnValue(false);

    render(<NotificationScheduler />);

    expect(notificationService.hasNotificationPermission).toHaveBeenCalledTimes(1);
    expect(notificationService.getReminders).not.toHaveBeenCalled();
    expect(notificationService.startNotificationLoop).not.toHaveBeenCalled();
  });

  it('starts the loop if notification permission is granted', () => {
    vi.mocked(notificationService.hasNotificationPermission).mockReturnValue(true);
    const mockStopLoop = vi.fn();
    vi.mocked(notificationService.startNotificationLoop).mockReturnValue(mockStopLoop);
    const mockReminders = [{ id: '1', label: 'Test', description: 'Desc', time: '12:00', days: [1], enabled: true, icon: '🔔' }];
    vi.mocked(notificationService.getReminders).mockReturnValue(mockReminders);

    const { unmount } = render(<NotificationScheduler />);

    expect(notificationService.hasNotificationPermission).toHaveBeenCalledTimes(1);
    expect(notificationService.getReminders).toHaveBeenCalledTimes(1);
    expect(notificationService.startNotificationLoop).toHaveBeenCalledWith(mockReminders);

    unmount();
    expect(mockStopLoop).toHaveBeenCalledTimes(1);
  });
});
