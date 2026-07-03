import threading
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class LightweightScheduler:
    """A simple thread-based in-process scheduler for logging notifications and nudges."""
    def __init__(self):
        self._jobs = {}
        self._lock = threading.Lock()
        self._thread = None
        self._running = False

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            logger.info("Lightweight notification scheduler started.")

    def stop(self):
        with self._lock:
            self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            logger.info("Lightweight notification scheduler stopped.")

    def add_job(self, job_id: str, interval_seconds: int, func, *args, **kwargs):
        """Register a background job running at defined intervals."""
        with self._lock:
            self._jobs[job_id] = {
                "interval": interval_seconds,
                "func": func,
                "args": args,
                "kwargs": kwargs,
                "last_run": 0
            }
            logger.info(f"Registered background task: {job_id} every {interval_seconds}s")

    def remove_job(self, job_id: str):
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                logger.info(f"Removed background task: {job_id}")

    def _run_loop(self):
        while True:
            with self._lock:
                if not self._running:
                    break
                now = time.time()
                for job_id, job in list(self._jobs.items()):
                    if now - job["last_run"] >= job["interval"]:
                        try:
                            # Run job
                            job["func"](*job["args"], **job["kwargs"])
                        except Exception as e:
                            logger.error(f"Error running job {job_id}: {e}")
                        finally:
                            job["last_run"] = now
            time.sleep(1)

# Global instance
scheduler = LightweightScheduler()
scheduler.start()

# Example jobs
def send_hydration_reminder(user_id: str):
    logger.info(f"[NUDGE] Hydration alert sent to user {user_id}: Keep logging your water intake!")

def send_inactivity_alert(user_id: str):
    logger.info(f"[NUDGE] Inactivity alert sent to user {user_id}: You haven't logged in over 48 hours!")
