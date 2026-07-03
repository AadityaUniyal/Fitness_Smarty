const STORAGE_KEY = 'smarty_reminders';
const PERMISSION_KEY = 'smarty_notification_permission';

export interface Reminder {
  id: string;
  label: string;
  description: string;
  time: string;
  days: number[];
  enabled: boolean;
  icon: string;
}

const DEFAULT_REMINDERS: Reminder[] = [
  { id: 'morning_weigh_in', label: 'Morning Weigh-In', description: 'Log your weight for the day', time: '07:00', days: [0,1,2,3,4,5,6], enabled: false, icon: '⚖️' },
  { id: 'breakfast', label: 'Log Breakfast', description: 'Time to fuel up', time: '08:00', days: [0,1,2,3,4,5,6], enabled: true, icon: '🌅' },
  { id: 'water_morning', label: 'Morning Hydration', description: 'Drink a glass of water', time: '09:00', days: [0,1,2,3,4,5,6], enabled: true, icon: '💧' },
  { id: 'snack_am', label: 'Morning Snack', description: 'Log your mid-morning snack', time: '10:30', days: [0,1,2,3,4,5,6], enabled: false, icon: '🍎' },
  { id: 'lunch', label: 'Log Lunch', description: 'Log your lunch meal', time: '12:30', days: [0,1,2,3,4,5,6], enabled: true, icon: '☀️' },
  { id: 'afternoon_water', label: 'Afternoon Hydration', description: 'Refill your water bottle', time: '15:00', days: [0,1,2,3,4,5,6], enabled: true, icon: '💧' },
  { id: 'workout', label: 'Workout Reminder', description: 'Time to train', time: '17:00', days: [0,1,2,3,4,5,6], enabled: true, icon: '💪' },
  { id: 'dinner', label: 'Log Dinner', description: 'Log your dinner meal', time: '19:30', days: [0,1,2,3,4,5,6], enabled: true, icon: '🌙' },
  { id: 'sleep', label: 'Wind Down', description: 'Prepare for sleep', time: '22:00', days: [0,1,2,3,4,5,6], enabled: true, icon: '😴' },
  { id: 'weekly_review', label: 'Weekly Review', description: 'Check your weekly progress', time: '10:00', days: [0], enabled: false, icon: '📊' },
  { id: 'meal_plan', label: 'Plan Meals', description: 'Plan next week\'s meals', time: '18:00', days: [0], enabled: false, icon: '📋' },
];

export function getReminders(): Reminder[] {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) return JSON.parse(saved);
  } catch { }
  return DEFAULT_REMINDERS;
}

export function saveReminders(reminders: Reminder[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(reminders));
}

export function hasNotificationPermission(): boolean {
  if (!('Notification' in window)) return false;
  return Notification.permission === 'granted';
}

export async function requestNotificationPermission(): Promise<boolean> {
  if (!('Notification' in window)) return false;
  if (Notification.permission === 'granted') return true;
  if (Notification.permission === 'denied') return false;
  const result = await Notification.requestPermission();
  return result === 'granted';
}

export function sendNotification(title: string, body: string, icon?: string): void {
  if (!hasNotificationPermission()) return;
  try {
    new Notification(title, { body, icon: icon || '/favicon.ico', silent: false });
  } catch { }
}

export function scheduleCheck(reminders: Reminder[]): number[] {
  const now = new Date();
  const currentDay = now.getDay();
  const currentMinutes = now.getHours() * 60 + now.getMinutes();
  const fired: number[] = [];
  reminders.forEach((r, i) => {
    if (!r.enabled) return;
    if (!r.days.includes(currentDay)) return;
    const [h, m] = r.time.split(':').map(Number);
    const reminderMinutes = h * 60 + m;
    const minuteKey = Math.floor(now.getTime() / 60000);
    const lastKeyStr = localStorage.getItem(`smarty_notify_${r.id}`);
    const lastKey = lastKeyStr ? parseInt(lastKeyStr, 10) : -1;
    if (reminderMinutes <= currentMinutes && reminderMinutes > currentMinutes - 2 && minuteKey !== lastKey) {
      sendNotification(r.label, r.description, r.icon);
      localStorage.setItem(`smarty_notify_${r.id}`, minuteKey.toString());
      fired.push(i);
    }
  });
  return fired;
}

export function startNotificationLoop(reminders: Reminder[], onFire?: (indices: number[]) => void): () => void {
  const interval = setInterval(() => {
    const fired = scheduleCheck(reminders);
    if (fired.length > 0) onFire?.(fired);
  }, 30000);
  scheduleCheck(reminders);
  return () => clearInterval(interval);
}
