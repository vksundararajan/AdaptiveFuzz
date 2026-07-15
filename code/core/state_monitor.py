from typing import Dict, Any

class StateMonitor:
    """
    Monitors state, constraints, limits (e.g., token limits, max iterations),
    and triggers done state when tasks are complete.
    """
    def __init__(self, max_iterations: int = 10):
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.completed_tasks = 0
        self.total_tasks = 0
        self.done = False

    def check_constraints(self) -> bool:
        """Check if limits have been reached."""
        if self.current_iteration >= self.max_iterations:
            print("[!] MON  : Maximum iterations reached.")
            self.done = True
            return False
        return True

    def increment_iteration(self):
        self.current_iteration += 1

    def register_tasks(self, count: int):
        self.total_tasks += count

    def complete_task(self):
        self.completed_tasks += 1
        if self.completed_tasks >= self.total_tasks and self.total_tasks > 0:
            print("[+] MON  : All tasks completed.")
            self.done = True
