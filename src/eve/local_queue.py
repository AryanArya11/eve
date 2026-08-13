from collections import deque
from dataclasses import dataclass

from eve.attempt import ExecutionAttempt
from eve.task import Task


@dataclass(frozen=True)
class QueuedExecution:
    task: Task
    attempt: ExecutionAttempt

    def __post_init__(self) -> None:
        self._validate_task_type('task', self.task)
        self._validate_attempt_type('attempt', self.attempt)
        self._validate_matching_ids(self.task, self.attempt)

    @staticmethod
    def _validate_task_type(task_name: str, value: object) -> None:
        if not isinstance(value, Task):
            raise TypeError(f"{task_name} should belong to Task")

    @staticmethod
    def _validate_attempt_type(attempt_name: str, value: object) -> None:
        if not isinstance(value, ExecutionAttempt):
            raise TypeError(f"{attempt_name} should belong to ExecutionAttempt")

    @staticmethod
    def _validate_matching_ids(task: Task, attempt: ExecutionAttempt):
        if not task.task_id == attempt.task_id:
            raise ValueError(
                f"Both Task and ExecutionAttempt must have the same task_id"
            )

class LocalExecutionQueue:
    def __init__(self):
        self.items = deque()
        self.queued_attempt_id = set()

    def enqueue(self, item) -> None:
        if not isinstance(item, QueuedExecution):
            raise TypeError(f"{item} must be a member of QueuedExecution")

        attempt_id = item.attempt.attempt_id

        if attempt_id in self.queued_attempt_id:
            raise ValueError(f"Duplicates Attempts are not allowed")

        self.items.append(item)
        self.queued_attempt_id.add(attempt_id)

    def dequeue(self) -> QueuedExecution:
        if not self.items:
            raise IndexError(f"Must be at least one item to dequeue")

        item = self.items.popleft()
        self.queued_attempt_id.remove(item.attempt.attempt_id)

        return item

    def peek(self) -> QueuedExecution:
        if not self.items:
            raise IndexError("queue must contain an item to peek")
        return self.items[0]

    def is_empty(self) -> bool:
        if not self.items:
            return True
        return False

    def length(self) -> int:
        return len(self.items)


                                