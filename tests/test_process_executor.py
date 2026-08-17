from dataclasses import FrozenInstanceError
from os import getpid
import pytest
import pickle

from eve.local_queue import QueuedExecution
from eve.outcome import TaskOutcome, OutcomeStatus
from eve.worker import execute_queued_execution
from eve.task import Task
from eve.attempt import ExecutionAttempt
from eve.process_executor import ProcessExecutionResult, execute_in_process

def helper() -> TaskOutcome:
    task = Task(
        task_id= 'task-001',
        workload= 'echo',
        payload= 'Hello'
    )
    attempt = ExecutionAttempt(
        attempt_id= 'attempt-001',
        task_id= task.task_id,
        attempt_number= 1
    )
    queued = QueuedExecution(
        task = task,
        attempt = attempt
    )
    exec = execute_queued_execution(queued)
    return exec

def make_execution(workload: str, payload: object) -> QueuedExecution:
    task = Task(
        task_id= 'task-001',
        workload= workload,
        payload= payload
    )
    attempt = ExecutionAttempt(
        attempt_id= 'attempt-001',
        task_id= task.task_id,
        attempt_number= 1
    )
    queued = QueuedExecution(
        task = task,
        attempt = attempt
    )
    return queued

def test_valid_fields_are_preserved() -> None:
    result = ProcessExecutionResult(
        attempt_id = 'attempt-001',
        worker_pid = getpid(),
        outcome = helper()
    )

    assert result.attempt_id == 'attempt-001'
    assert isinstance(result.worker_pid, int)
    assert isinstance(result.outcome, TaskOutcome)

@pytest.mark.parametrize('attempt_id', ['', "   "])
def test_blank_attempt_id_is_rejected(attempt_id: str) -> None:
    with pytest.raises(ValueError):
        result = ProcessExecutionResult(
            attempt_id= attempt_id,
            worker_pid= getpid(),
            outcome= helper()
        )

@pytest.mark.parametrize('attempt_id', [None, 123, {}])
def test_non_str_attempt_id_is_rejected(attempt_id: str) -> None:
    with pytest.raises(TypeError):
        result = ProcessExecutionResult(
            attempt_id= attempt_id,
            worker_pid= getpid(),
            outcome= helper()
        )

@pytest.mark.parametrize('attempt_id', [
    "  attempt-001",
    "attempt-001   ",
    "   attempt-001   "
])
def test_whitespace_attempt_id_is_rejected(attempt_id: str) -> None:
    with pytest.raises(ValueError):
        result = ProcessExecutionResult(
            attempt_id= attempt_id,
            worker_pid= getpid(),
            outcome= helper()
        )

@pytest.mark.parametrize('worker_pid', [True, False])
def test_bool_worker_pid_is_rejected(worker_pid: int) -> None:
    with pytest.raises(TypeError):
        result = ProcessExecutionResult(
            attempt_id= 'attempt-001',
            worker_pid= worker_pid,
            outcome= helper()
        )

@pytest.mark.parametrize('worker_pid', [None, 123.5, []])
def test_non_int_worker_pid_is_rejected(worker_pid: int) -> None:
    with pytest.raises(TypeError):
        result = ProcessExecutionResult(
            attempt_id= 'attempt-001',
            worker_pid= worker_pid,
            outcome= helper()
        )

@pytest.mark.parametrize("worker_pid", [-100, -10, 0, -getpid()])
def test_non_positive_worker_pid_is_rejected(worker_pid: int) -> None:
    with pytest.raises(ValueError):
        result = ProcessExecutionResult(
            attempt_id= 'attempt-001',
            worker_pid= worker_pid,
            outcome= helper()
        )

@pytest.mark.parametrize('outcome', [
    Task(
        task_id='task-001',
        workload='echo',
        payload='hello'
    ),
    ExecutionAttempt(
        attempt_id='attempt-001',
        task_id='task-001',
        attempt_number=1
    ),
    None,
    123,
    []
])
def test_non_task_outcome_is_rejected(outcome: TaskOutcome) -> None:
    with pytest.raises(TypeError):
        result = ProcessExecutionResult(
            attempt_id= 'attempt-001',
            worker_pid= getpid(),
            outcome= outcome
        )

def test_result_is_frozen() -> None:
    result = ProcessExecutionResult(
        attempt_id= 'attempt-001',
        worker_pid= getpid(),
        outcome= helper()
    )
    with pytest.raises(FrozenInstanceError):
        result.attempt_id = 'attempt-002'

def test_result_survives_pickle() -> None:
    original = ProcessExecutionResult(
        attempt_id= 'attempt-001',
        worker_pid= getpid(),
        outcome= helper()
    )

    serialized = pickle.dumps(original)
    restored = pickle.loads(serialized)

    assert original == restored


def test_valid_process_exec_result() -> None:
    parent_pid = getpid()
    execution = make_execution('sum-range', {'start':1, 'stop':10})
    result = execute_in_process(execution=execution)

    assert result.worker_pid != parent_pid
    assert result.attempt_id == 'attempt-001'
    assert result.outcome.status is OutcomeStatus.SUCCESS
    assert result.outcome.value == 45
    assert result.outcome.error is None

@pytest.mark.parametrize(
    ("payload", "expected_error_type"),
    [
        ({"start": 10, "stop": 1}, "ValueError"),
        ({"stop": 10}, "ValueError"),
        ({}, "ValueError"),
        (None, "TypeError"),
    ],
)
def test_invalid_sum_range_payload_becomes_failure(
    payload: object,
    expected_error_type: str,
) -> None:
    execution = make_execution(
        workload="sum-range",
        payload=payload,
    )

    result = execute_in_process(execution)

    assert result.outcome.status is OutcomeStatus.FAILURE
    assert result.outcome.value is None
    assert result.outcome.error is not None
    assert result.outcome.error.error_type == expected_error_type

def test_echo_exec_with_none() -> None:
    parent_pid = getpid()
    execution = make_execution(
        workload= 'echo',
        payload= None
    )

    result = execute_in_process(execution)

    assert result.worker_pid != parent_pid
    assert result.outcome.status is OutcomeStatus.SUCCESS
    assert result.outcome.value is None
    assert result.outcome.error is None

def test_echo_exec_with_valid_payload() -> None:
    payload = {'message':'hello'}

    execution = make_execution(
        workload= 'echo',
        payload= payload
    )

    result = execute_in_process(execution)

    assert result.outcome.status is OutcomeStatus.SUCCESS
    assert result.outcome.value == payload
    assert result.outcome.error is None

@pytest.mark.parametrize('invalid_input', [
    None,
    123,
    Task(
        task_id='task-001',
        workload='echo',
        payload={'message':2}
    ),
    ExecutionAttempt(
        attempt_id='attempt=001',
        task_id='task-001',
        attempt_number=1
    )
])
def test_invalid_public_inputs_for_process(invalid_input: QueuedExecution) -> None:
    with pytest.raises(TypeError):
        execute_in_process(invalid_input)