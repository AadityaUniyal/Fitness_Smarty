/**
 * Offline Sync Queue with Retry, Backoff, and Dead-Letter Support
 *
 * Queues write operations (POST/PUT/DELETE) when offline and replays them
 * when connectivity is restored.  Items that fail permanently are moved to
 * a dead-letter queue with a user-visible "sync failed" indicator.
 */

export interface SyncItem {
  id: string;
  url: string;
  method: 'POST' | 'PUT' | 'DELETE';
  body: any;
  timestamp: number;
  retryCount: number;
  status: 'pending' | 'retrying' | 'failed';
  lastError?: string;
}

const STORAGE_KEY = 'smarty_sync_queue';
const DEAD_LETTER_KEY = 'smarty_sync_failed';
const MAX_RETRIES = 5;
const BASE_BACKOFF_MS = 1000; // 1 second

export const syncQueue = {
  getQueue(): SyncItem[] {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    } catch {
      return [];
    }
  },

  getDeadLetterQueue(): SyncItem[] {
    try {
      return JSON.parse(localStorage.getItem(DEAD_LETTER_KEY) || '[]');
    } catch {
      return [];
    }
  },

  saveQueue(queue: SyncItem[]) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(queue));
  },

  saveDeadLetterQueue(queue: SyncItem[]) {
    localStorage.setItem(DEAD_LETTER_KEY, JSON.stringify(queue));
  },

  enqueue(url: string, method: 'POST' | 'PUT' | 'DELETE', body: any) {
    const queue = this.getQueue();
    const item: SyncItem = {
      id: Math.random().toString(36).substring(2, 9),
      url,
      method,
      body,
      timestamp: Date.now(),
      retryCount: 0,
      status: 'pending',
    };
    queue.push(item);
    this.saveQueue(queue);
    console.log('[SyncQueue] Enqueued offline write action:', item.id);
  },

  /** Move an item to the dead-letter queue after max retries. */
  moveToDead(item: SyncItem, error: string) {
    item.status = 'failed';
    item.lastError = error;
    const dead = this.getDeadLetterQueue();
    dead.push(item);
    this.saveDeadLetterQueue(dead);
    console.warn('[SyncQueue] Moved to dead-letter queue:', item.id, error);
  },

  /** Retry all items in the dead-letter queue (user-triggered). */
  async retryDeadLetterQueue(): Promise<number> {
    const dead = this.getDeadLetterQueue();
    if (dead.length === 0) return 0;

    // Reset retry counts and move back to main queue
    const queue = this.getQueue();
    for (const item of dead) {
      item.retryCount = 0;
      item.status = 'pending';
      queue.push(item);
    }
    this.saveQueue(queue);
    this.saveDeadLetterQueue([]);

    // Trigger processing
    await this.processQueue();
    return dead.length;
  },

  async processQueue() {
    if (!navigator.onLine) return;
    const queue = this.getQueue();
    if (queue.length === 0) return;

    console.log(`[SyncQueue] Processing ${queue.length} offline cached actions...`);
    const remaining: SyncItem[] = [];

    for (const item of queue) {
      try {
        const token = localStorage.getItem('smarty_access_token');
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        };
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }

        const res = await fetch(item.url, {
          method: item.method,
          headers,
          body: JSON.stringify(item.body),
        });

        if (res.ok) {
          console.log('[SyncQueue] Synchronized:', item.id);
          continue; // Success — don't add back to queue
        }

        // 4xx errors are permanent failures (bad data) — don't retry
        if (res.status >= 400 && res.status < 500) {
          this.moveToDead(item, `HTTP ${res.status}: ${res.statusText}`);
          continue;
        }

        throw new Error(`HTTP ${res.status}`);
      } catch (err: any) {
        item.retryCount += 1;
        item.status = 'retrying';

        if (item.retryCount >= MAX_RETRIES) {
          this.moveToDead(item, err?.message || 'Unknown error');
        } else {
          // Exponential backoff — delay will be applied on next processQueue
          remaining.push(item);
          console.warn(
            `[SyncQueue] Retry ${item.retryCount}/${MAX_RETRIES} for:`,
            item.id,
          );
        }
      }
    }

    this.saveQueue(remaining);

    // If there are items remaining, schedule a retry with exponential backoff
    if (remaining.length > 0) {
      const maxRetry = Math.max(...remaining.map((i) => i.retryCount));
      const delay = Math.min(BASE_BACKOFF_MS * 2 ** maxRetry, 60_000);
      console.log(`[SyncQueue] Scheduling retry in ${delay}ms`);
      setTimeout(() => this.processQueue(), delay);
    }
  },

  /** Get counts for UI display. */
  getCounts(): { pending: number; failed: number } {
    return {
      pending: this.getQueue().length,
      failed: this.getDeadLetterQueue().length,
    };
  },
};

// Auto-sync when navigator transitions to online
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    syncQueue.processQueue().catch(() => {});
  });
}
