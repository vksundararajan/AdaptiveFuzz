import json
import asyncio
from typing import Dict, Any
from huey import SqliteHuey
import os
from paths import DATA_DIR

class TaskQueue:
    """
    A Task Queue backed by Huey and SQLite for persistence.
    No external server is required, data is saved locally to a sqlite file.
    """
    def __init__(self, filename: str = None):
        if filename is None:
            filename = os.path.join(DATA_DIR, "tasks_queue.sqlite3")
        self.filename = filename
        self.huey = SqliteHuey(filename=self.filename)

    async def add_task(self, task: Dict[str, Any]):
        """Add a task to the queue."""
        task_data = json.dumps(task).encode('utf-8')
        self.huey.storage.enqueue(task_data)

    async def get_task(self, poll_interval: float = 0.5) -> Dict[str, Any]:
        """
        Get the next task from the queue. Blocks (asynchronously) until a task is available.
        Since Huey's raw dequeue is non-blocking if empty, we poll asynchronously.
        """
        while True:
            task_data = self.huey.storage.dequeue()
            if task_data is not None:
                return json.loads(task_data.decode('utf-8'))
            await asyncio.sleep(poll_interval)

    def task_done(self):
        """Mark a task as done."""
        pass

    async def close(self):
        """Close the SQLite connection."""
        pass
