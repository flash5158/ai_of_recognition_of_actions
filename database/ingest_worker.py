import threading
import time
from collections import deque


class IngestWorker:
    """
    Background worker that consumes a queue of insert tasks and writes to the VectorDB.
    Keeps the real-time processing loop responsive by offloading IO.
    """
    def __init__(self, db_client, max_retries=3, sleep_on_empty=0.1):
        self.db = db_client
        self.queue = deque()
        self.lock = threading.Lock()
        self.running = True
        self.max_retries = max_retries
        self.sleep_on_empty = sleep_on_empty
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def enqueue(self, item):
        with self.lock:
            self.queue.append(item)

    def stop(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)

    def _run(self):
        while self.running:
            item = None
            with self.lock:
                if self.queue:
                    item = self.queue.popleft()

            if not item:
                time.sleep(self.sleep_on_empty)
                continue

            retries = 0
            while retries < self.max_retries:
                try:
                    # expected fields: person_id, timestamp, vector, metadata
                    if getattr(self.db, 'active', False):
                        self.db.insert_behavior(
                            person_id=item.get('person_id'),
                            timestamp=item.get('timestamp'),
                            vector=item.get('vector'),
                            metadata=item.get('metadata')
                        )
                    break
                except Exception:
                    retries += 1
                    time.sleep(0.1 * retries)
            # continue to next item
