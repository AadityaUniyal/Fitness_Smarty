export interface SyncItem {
  id: string;
  url: string;
  method: 'POST' | 'PUT' | 'DELETE';
  body: any;
  timestamp: number;
}

const STORAGE_KEY = 'smarty_sync_queue';

export const syncQueue = {
  getQueue(): SyncItem[] {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    } catch {
      return [];
    }
  },

  saveQueue(queue: SyncItem[]) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(queue));
  },

  enqueue(url: string, method: 'POST' | 'PUT' | 'DELETE', body: any) {
    const queue = this.getQueue();
    const item: SyncItem = {
      id: Math.random().toString(36).substring(2, 9),
      url,
      method,
      body,
      timestamp: Date.now()
    };
    queue.push(item);
    this.saveQueue(queue);
    console.log('[SyncQueue] Enqueued offline write action:', item);
  },

  async processQueue() {
    if (!navigator.onLine) return;
    const queue = this.getQueue();
    if (queue.length === 0) return;

    console.log(`[SyncQueue] Processing ${queue.length} offline cached actions...`);
    const remaining: SyncItem[] = [];

    for (const item of queue) {
      try {
        const res = await fetch(item.url, {
          method: item.method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(item.body)
        });
        if (!res.ok) {
          throw new Error('Sync request failed');
        }
        console.log('[SyncQueue] Successfully synchronized item:', item.id);
      } catch (err) {
        console.error('[SyncQueue] Sync failed for item:', item.id, err);
        remaining.push(item); // Keep item in queue to retry later (last-write-wins fallback)
      }
    }

    this.saveQueue(remaining);
  }
};

// Auto-sync process when navigator triggers online transition
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    syncQueue.processQueue().catch(() => {});
  });
}
