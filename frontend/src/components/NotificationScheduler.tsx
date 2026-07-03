import { useEffect } from 'react';
import { getReminders, startNotificationLoop, hasNotificationPermission } from '../services/notificationService';

const NotificationScheduler: React.FC = () => {
  useEffect(() => {
    if (!hasNotificationPermission()) return;
    const reminders = getReminders();
    const stop = startNotificationLoop(reminders);
    return stop;
  }, []);

  return null;
};

export default NotificationScheduler;
