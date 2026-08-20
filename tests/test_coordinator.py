import pytest

from eve.coordinator import LocalCoordinator
from eve.local_queue import QueuedExecution
from eve.task import Task
from eve.attempt import ExecutionAttempt
from eve.state import ExecutionState
from eve.outcome import OutcomeStatus

def test_valid_coordinator() -> None:
    coordinator = LocalCoordinator()

    assert coordinator.pending_count() == 0
    assert coordinator.has_pending_work() is False

def test_valid_submission_to_coordinator() -> None:
    queued = QueuedExecution(
        task = Task(
            task_id= 'task-001',
            workload= 'echo',
            payload= 'hello'
        ),
        attempt = ExecutionAttempt(
            attempt_id= 'attempt-001',
            task_id= 'task-001',
            attempt_number= 1
        )
    )
    coordinator = LocalCoordinator()

    coordinator.submit(queued)

    attempt_id = queued.attempt.attempt_id

    assert coordinator.pending_count() == 1
    assert coordinator.has_pending_work() is True
    assert coordinator.state_for(attempt_id) is ExecutionState.QUEUED

    with pytest.raises(KeyError):
        coordinator.result_for(attempt_id)

def test_duplicate_submission_to_coordinator() -> None:
    first = QueuedExecution(
            task = Task(
                task_id= 'task-001',
                workload= 'echo',
                payload= 'hello'
            ),
            attempt = ExecutionAttempt(
                attempt_id= 'attempt-001',
                task_id= 'task-001',
                attempt_number= 1
            )
        )
    
    second = QueuedExecution(
        task = Task(
            task_id= 'task-002',
            workload= 'echo',
            payload= 'hello'
        ),
        attempt = ExecutionAttempt(
            attempt_id= 'attempt-001',
            task_id= 'task-002',
            attempt_number= 1
        )
    )

    coordinator = LocalCoordinator()
    coordinator.submit(first)

    with pytest.raises(ValueError):
        coordinator.submit(second)

    assert coordinator.pending_count() == 1
    assert coordinator.state_for('attempt-001') is ExecutionState.QUEUED

@pytest.mark.parametrize('submission', [
    None,
    123,
    Task(
        task_id= 'task-001',
        workload= 'echo',
        payload= 'hello'
    ),
    ExecutionAttempt(
        attempt_id= 'attempt-001',
        task_id= 'task-001',
        attempt_number= 1
    )
])
def test_invalid_submission_to_coordinator(submission: object) -> None:
    coordinator = LocalCoordinator()

    with pytest.raises(TypeError):
        coordinator.submit(submission)


def test_successful_execution_to_coordinator() -> None:
    execution = QueuedExecution(
        task = Task(
            task_id= 'task-001',
            workload= 'echo',
            payload= 'hello'
        ),
        attempt = ExecutionAttempt(
            attempt_id= 'attempt-001',
            task_id= 'task-001',
            attempt_number= 1
        )
    )
    saved_attempt_id = execution.attempt.attempt_id
    saved_payload = execution.task.payload

    coordinator = LocalCoordinator()

    coordinator.submit(execution)
    result = coordinator.run_next()

    assert result.attempt_id == saved_attempt_id
    assert result.outcome.status is OutcomeStatus.SUCCESS
    assert result.outcome.value == saved_payload
    assert coordinator.state_for(saved_attempt_id) is ExecutionState.SUCCEEDED
    assert coordinator.result_for(saved_attempt_id).outcome.value == result.outcome.value
    assert coordinator.has_pending_work() is False
    assert coordinator.pending_count() == 0

@pytest.mark.parametrize(('payload', 'expected_error_type'), [
    ({"start": 10, "stop": 1}, "ValueError"),
    ({"stop": 10}, "ValueError"),
    ({}, "ValueError"),
    (None, "TypeError"),
])
def test_workload_failure_to_coordinator(payload: object, expected_error_type: str) -> None:
    execution = QueuedExecution(
        task = Task(
            task_id= 'task-001',
            workload= 'sum-range',
            payload= payload
        ),
        attempt = ExecutionAttempt(
            attempt_id= 'attempt-001',
            task_id= 'task-001',
            attempt_number= 1
        )
    )
    saved_attempt_id = execution.attempt.attempt_id

    coordinator = LocalCoordinator()

    coordinator.submit(execution)
    result = coordinator.run_next()

    assert result.outcome.status is OutcomeStatus.FAILURE
    assert result.outcome.value is None
    assert result.outcome.error is not None
    assert result.outcome.error.error_type == expected_error_type
    assert coordinator.state_for(saved_attempt_id) is ExecutionState.FAILED
    assert coordinator.result_for(saved_attempt_id) == result
    assert coordinator.has_pending_work() is False


def test_empty_execution_to_coordinator() -> None:
    coordinator = LocalCoordinator()
    with pytest.raises(IndexError):
        coordinator.run_next()

    assert coordinator.pending_count() == 0
    assert coordinator.has_pending_work() is False


def test_infrastructure_failure_to_coordinator(monkeypatch) -> None:
    coordinator = LocalCoordinator()
    execution = QueuedExecution(
        task = Task(
            task_id= 'task-001',
            workload= 'echo',
            payload= 'hello'
        ),
        attempt = ExecutionAttempt(
            attempt_id= 'attempt-001',
            task_id= 'task-001',
            attempt_number= 1
        )
    )

    attempt_id = execution.attempt.attempt_id
    coordinator.submit(execution)

    def fake_execute_in_process(received_execution):
        assert received_execution is execution
        assert coordinator.state_for(attempt_id) is ExecutionState.RUNNING
        raise RuntimeError('simulated process failure')

    monkeypatch.setattr(
        "eve.coordinator.execute_in_process",
        fake_execute_in_process
    )

    with pytest.raises(RuntimeError, match = 'simulated process failure'):
        coordinator.run_next()

    with pytest.raises(KeyError):   
        coordinator.result_for(attempt_id)

    assert coordinator.state_for(attempt_id) is ExecutionState.FAILED
    assert coordinator.pending_count() == 0 
    assert coordinator.has_pending_work() is False