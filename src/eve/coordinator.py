from eve.local_queue import LocalExecutionQueue, QueuedExecution
from eve.outcome import OutcomeStatus
from eve.process_executor import ProcessExecutionResult, execute_in_process
from eve.state import ExecutionState, validate_transition


class LocalCoordinator:
    def __init__(self):
        self._queue: LocalExecutionQueue = LocalExecutionQueue()
        self._states: dict[str, ExecutionState] = {}
        self._results: dict[str, ProcessExecutionResult] = {}

    def _transition(self, attempt_id: str, target: ExecutionState) -> None:

        current = self._states[attempt_id]

        validate_transition(current, target)

        self._states[attempt_id] = target

    def submit(self, execution: object) -> None:
        if not isinstance(execution, QueuedExecution):
            raise TypeError(f"execution ({execution}) must be a member of QueuedExecution")

        attempt_id = execution.attempt.attempt_id

        if attempt_id in self._states:
            raise ValueError(f"attempt id ({attempt_id}) in states")

        validate_transition(ExecutionState.SUBMITTED, ExecutionState.QUEUED)

        self._queue.enqueue(execution)
        self._states[attempt_id] = ExecutionState.QUEUED


    def pending_count(self) -> int:
        return self._queue.length()

    def has_pending_work(self) -> bool:
        return not self._queue.is_empty()

    def state_for(self, attempt_id: str) -> ExecutionState:
        if attempt_id not in self._states:
            raise KeyError(f"Unknown ID ({attempt_id})")
        
        stored = self._states[attempt_id]
        return stored

    def result_for(self, attempt_id: str) -> ProcessExecutionResult:
        if attempt_id not in self._results:
            raise KeyError(f"Unknown ID ({attempt_id})")
        
        stored = self._results[attempt_id]
        return stored

    def run_next(self) -> ProcessExecutionResult:
        next_execution = self._queue.dequeue()
        attempt_id = next_execution.attempt.attempt_id


        self._transition(attempt_id, ExecutionState.ASSIGNED)
        self._transition(attempt_id, ExecutionState.RUNNING)

        try:
            ran = execute_in_process(next_execution)

        except Exception:
            self._transition(attempt_id, ExecutionState.FAILED)
            raise

        if ran.outcome.status is OutcomeStatus.SUCCESS:
            self._transition(attempt_id, ExecutionState.SUCCEEDED)
        else: 
            self._transition(attempt_id, ExecutionState.FAILED)

        self._results[attempt_id] = ran

        return ran


        

    


        
        