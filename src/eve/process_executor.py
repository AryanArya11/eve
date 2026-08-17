from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from multiprocessing import get_context
from os import getpid

from eve.local_queue import QueuedExecution
from eve.outcome import TaskOutcome
from eve.worker import execute_queued_execution

@dataclass(frozen=True)
class ProcessExecutionResult:
    attempt_id: str
    worker_pid: int
    outcome: TaskOutcome

    def __post_init__(self) -> None:
        self._validate_text_field('attempt_id', self.attempt_id)
        self._validate_worker_pid_is_int(self.worker_pid)
        self._validate_outcome(self.outcome)

    @staticmethod
    def _validate_text_field(field_name: str, value: object) -> None:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")

        if not value.strip():
            raise ValueError(f"{field_name} cannot be blank")

        if value != value.strip():
            raise ValueError(f"{field_name} cannot have leading or trailing whitespace")

    @staticmethod
    def _validate_worker_pid_is_int(value: object) -> None:
        if isinstance(value, bool):
            raise TypeError(f"worker_pid cannot be boolean")

        if not isinstance(value, int):
            raise TypeError(f"worker_pid must be integer")

        if value < 0 or value == 0:
            raise ValueError(f"worker_pid ({value}) must be positive")

    @staticmethod
    def _validate_outcome(value: TaskOutcome) -> None:
        if not isinstance(value, TaskOutcome):
            raise TypeError(f"{value} must be a member of TaskOutcome")


def _execute_with_process_metadata(execution: QueuedExecution) -> ProcessExecutionResult:

    outcome = execute_queued_execution(execution=execution)

    return ProcessExecutionResult(
        attempt_id = execution.attempt.attempt_id,
        worker_pid = getpid(),
        outcome = outcome
    )

def execute_in_process(execution: object) -> ProcessExecutionResult:

    if not isinstance(execution, QueuedExecution):
        raise TypeError(f"execution ({execution}) must be a member of QueuedExecution")

    spawn_context = get_context("spawn")

    with ProcessPoolExecutor(
        max_workers=1,
        mp_context=spawn_context
    ) as executor:
        future = executor.submit(
            _execute_with_process_metadata,
            execution,
        )
        result = future.result()

    return result
