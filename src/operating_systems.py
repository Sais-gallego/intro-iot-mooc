"""
IoT Operating Systems & Real-Time Scheduling (RTOS).
Models Task Control Blocks (TCB), Preemptive & Cooperative Schedulers,
and Priority Inheritance Protocol (PIP) for Priority Inversion Mitigation.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Callable
import heapq


class TaskState(Enum):
    READY = "READY"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    SUSPENDED = "SUSPENDED"


class Task:
    """Task Control Block (TCB) for an embedded RTOS thread."""

    def __init__(
        self,
        task_id: str,
        name: str,
        base_priority: int,  # Higher number = higher priority
        workload_ticks: int = 5,
        period_ticks: Optional[int] = None
    ):
        self.task_id = task_id
        self.name = name
        self.base_priority = base_priority
        self.current_priority = base_priority
        self.workload_ticks = workload_ticks
        self.remaining_ticks = workload_ticks
        self.period_ticks = period_ticks
        self.state = TaskState.READY
        self.accumulated_cpu_ticks = 0

    def reset(self):
        self.remaining_ticks = self.workload_ticks
        self.current_priority = self.base_priority
        self.state = TaskState.READY


class Mutex:
    """Embedded Mutex supporting Priority Inheritance Protocol (PIP)."""

    def __init__(self, mutex_id: str):
        self.mutex_id = mutex_id
        self.owner: Optional[Task] = None
        self.waiting_queue: List[Task] = []

    def acquire(self, task: Task) -> bool:
        if self.owner is None:
            self.owner = task
            return True

        if self.owner == task:
            return True

        # Mutex is locked: check priority inheritance
        self.waiting_queue.append(task)
        task.state = TaskState.BLOCKED

        # Elevate owner priority to waiting task's priority if higher (Priority Inheritance)
        if task.current_priority > self.owner.current_priority:
            self.owner.current_priority = task.current_priority

        return False

    def release(self, task: Task) -> Optional[Task]:
        if self.owner != task:
            return None

        # Restore owner's base priority
        task.current_priority = task.base_priority
        self.owner = None

        if self.waiting_queue:
            # Wake up highest priority waiting task
            self.waiting_queue.sort(key=lambda t: t.current_priority, reverse=True)
            next_task = self.waiting_queue.pop(0)
            self.owner = next_task
            next_task.state = TaskState.READY
            return next_task

        return None


class RtosScheduler:
    """
    Simulates an embedded preemptive priority-based RTOS scheduler (e.g. FreeRTOS / Zephyr).
    Executes tasks tick-by-tick and logs execution traces.
    """

    def __init__(self, is_preemptive: bool = True):
        self.is_preemptive = is_preemptive
        self.tasks: Dict[str, Task] = {}
        self.running_task: Optional[Task] = None
        self.current_tick = 0
        self.execution_trace: List[Dict[str, Any]] = []

    def add_task(self, task: Task):
        self.tasks[task.task_id] = task

    def get_ready_tasks(self) -> List[Task]:
        return [t for t in self.tasks.values() if t.state == TaskState.READY and t.remaining_ticks > 0]

    def schedule_next(self) -> Optional[Task]:
        ready = self.get_ready_tasks()
        if not ready:
            return None
        # Select task with highest current_priority; tie-break by task_id
        ready.sort(key=lambda t: (t.current_priority, -ord(t.task_id[0] if t.task_id else 'A')), reverse=True)
        return ready[0]

    def step_tick(self) -> Optional[str]:
        """Advances scheduler by 1 system tick."""
        self.current_tick += 1

        # Check if running task finished or needs preemption
        if self.is_preemptive or self.running_task is None or self.running_task.remaining_ticks <= 0:
            if self.running_task and self.running_task.remaining_ticks > 0:
                self.running_task.state = TaskState.READY

            candidate = self.schedule_next()
            self.running_task = candidate
            if self.running_task:
                self.running_task.state = TaskState.RUNNING

        if self.running_task:
            self.running_task.remaining_ticks -= 1
            self.running_task.accumulated_cpu_ticks += 1
            active_name = self.running_task.name
            if self.running_task.remaining_ticks <= 0:
                self.running_task.state = TaskState.SUSPENDED
        else:
            active_name = "IDLE_TASK"

        self.execution_trace.append({
            "tick": self.current_tick,
            "running": active_name
        })
        return active_name

    def run_simulation(self, total_ticks: int) -> List[Dict[str, Any]]:
        for _ in range(total_ticks):
            self.step_tick()
        return self.execution_trace
