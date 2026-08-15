import pytest

from eve.attempt import ExecutionAttempt
from eve.task import Task
from eve.local_queue import QueuedExecution
from eve.worker import execute_queued_execution
from eve.outcome import TaskError, OutcomeStatus


def helper(workload: str, payload: object) -> QueuedExecution:
    task = Task(
        task_id = 'task-001',
        workload = workload,
        payload = payload
    )
    attempt = ExecutionAttempt(
        attempt_id = 'attempt-001',
        task_id = 'task-001',
        attempt_number = 1
    )
    queued = QueuedExecution(
        task = task,
        attempt = attempt
    )
    return queued

def test_succesful_sum_range() -> None:
    test = helper(
        workload = 'sum-range',
        payload = {'start' : 1, 'stop' : 10}
    )
    result = execute_queued_execution(test)

    assert result.task_id == 'task-001'
    assert result.status is OutcomeStatus.SUCCESS
    assert result.value == 45
    assert result.error is None

def test_invalid_payload_becomes_failure() -> None:
    test = helper(
        workload = 'sum-range',
        payload = {'start' : 'one', 'stop' : 10}
    )
    result = execute_queued_execution(test)

    assert result.status is OutcomeStatus.FAILURE
    assert result.value is None
    assert type(result.error) is TaskError
    assert result.error.error_type == "TypeError"
    assert result.error.message

def test_unknown_workload_becomes_failure() -> None:
    test = helper(
            workload = 'unknown-workload',
            payload = {'start' : 1, 'stop' : 10}
        )
    result = execute_queued_execution(test)

    assert result.status is OutcomeStatus.FAILURE
    assert result.error.error_type == "ValueError"

@pytest.mark.parametrize('invalid_input', [
    None,
    123,
    Task(
        task_id = 'task-001',
        workload = 'echo',
        payload = None
    ),
    ExecutionAttempt(
        attempt_id = 'attempt-001',
        task_id = 'task-001',
        attempt_number = 1
    )
])
def test_invalid_worker_input(invalid_input: object) -> None:
    with pytest.raises(TypeError):
        execute_queued_execution(invalid_input)

def test_none_type_succesful_echo() -> None:
    test = helper(
        workload = 'echo',
        payload = None
    )
    result = execute_queued_execution(test)

    assert result.status is OutcomeStatus.SUCCESS
    assert result.value is None
    assert result.error is None

@pytest.mark.parametrize("payload", [None, 123, {'start' : 1, 'stop' : 10}])
def test_objects_succesful_echo(payload: object) -> None:
    test = helper(
        workload = 'echo',
        payload = payload
    )
    result = execute_queued_execution(test)

    assert result.status is OutcomeStatus.SUCCESS
    assert result.value is payload
    assert result.error is None






