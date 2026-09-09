import pytest
from dataclasses import FrozenInstanceError
import os 

from eve.outcome import TaskError, TaskOutcome, OutcomeStatus
from eve.process_executor import ProcessExecutionResult
from eve.state import ExecutionState
from eve.batch_result import InfrastructureFailure, BatchTaskResult

def test_valid_values_are_preserved():
    failure = InfrastructureFailure(
        error_type= "BrokenProcessPool",
        message= "worker process terminated"
    )

    assert failure.error_type == 'BrokenProcessPool'
    assert failure.message == 'worker process terminated'

@pytest.mark.parametrize(
    ('error', 'message'),
    [
        ("", "worker process terminated"),
        ("   ", "worker process terminated"),
        ("BrokenProcessPool", ""),
        ("BrokenProcessPool", "   ")
    ]
)
def test_blank_fields_are_rejected(error: str, message: str):
    with pytest.raises(ValueError):
        failure = InfrastructureFailure(
            error_type= error,
            message= message
        )

@pytest.mark.parametrize(
    ('error', 'message'),
    [
        (None, "worker process terminated"),
        (123, "worker process terminated"),
        ([], "worker process terminated"),
        ("BrokenProcessPool", None),
        ("BrokenProcessPool", 123),
        ("BrokenProcessPool", []),
    ]
)
def test_non_string_are_rejected(error: object, message: object):
    with pytest.raises(TypeError):
        failure = InfrastructureFailure(
            error_type= error,
            message= message
        )

@pytest.mark.parametrize(
    ('error', 'message'),
    [
        (" BrokenProcessPool", "worker process terminated"),
        ("BrokenProcessPool ", "worker process terminated"),
        (" BrokenProcessPool ", "worker process terminated"),
        ("BrokenProcessPool", " worker process terminated"),
        ("BrokenProcessPool", "worker process terminated "),
        ("BrokenProcessPool", " worker process terminated "),
    ]
)
def test_whitespace_is_rejected(error: str, message: str):
    with pytest.raises(ValueError):
        failure = InfrastructureFailure(
            error_type= error,
            message= message
        )

def test_model_is_frozen():
    failure = InfrastructureFailure(
        error_type= 'BrokenProcessPool',
        message= 'worker process terminated'
    )
    with pytest.raises(FrozenInstanceError):
        failure.message = 'worker proces functional'

def test_succesful_workload_record():
    outcome = TaskOutcome(
        task_id= 'task-001',
        status= OutcomeStatus.SUCCESS,
        value= 'hello',
        error= None
    )
    result = ProcessExecutionResult(
        attempt_id= 'attempt-001',
        worker_pid= os.getpid(),
        outcome= outcome
    )
    batch = BatchTaskResult(
        task_id= outcome.task_id,
        attempt_id= result.attempt_id,
        state= ExecutionState.SUCCEEDED,
        process_result= result,
        infrastructure_failure= None
    )

    assert batch.task_id == outcome.task_id
    assert batch.attempt_id == result.attempt_id
    assert batch.process_result == result
    assert batch.infrastructure_failure is None

def test_failed_workload_record():
    error = TaskError(
        error_type= 'Workload Error',
        message= 'Invalid workload type entered'
    )
    outcome = TaskOutcome(
        task_id= 'task-001',
        status= OutcomeStatus.FAILURE,
        value= None,
        error= error
    )
    result = ProcessExecutionResult(
        attempt_id= "attempt-001",
        worker_pid= os.getpid(),
        outcome= outcome
    )
    batch = BatchTaskResult(
        task_id= outcome.task_id,
        attempt_id= result.attempt_id,
        state= ExecutionState.FAILED,
        process_result= result,
        infrastructure_failure= None,
    )

    assert batch.task_id == outcome.task_id
    assert batch.attempt_id == result.attempt_id
    assert batch.state is ExecutionState.FAILED
    assert batch.process_result == result
    assert batch.infrastructure_failure is None


def test_infrastructure_failure_record() -> None:
    failure = InfrastructureFailure(
        error_type= "BrokenProcessPool",
        message= "worker process terminated",
    )

    batch = BatchTaskResult(
        task_id= 'task-001',
        attempt_id= 'attempt-001',
        state= ExecutionState.FAILED,
        process_result= None,
        infrastructure_failure= failure,
    )

    assert batch.state is ExecutionState.FAILED
    assert batch.process_result is None
    assert batch.infrastructure_failure == failure


def test_both_result_paths_are_rejected():
    outcome = TaskOutcome(
        task_id= 'task-001',
        status= OutcomeStatus.SUCCESS,
        value= 'hello',
        error = None
    )
    result = ProcessExecutionResult(
        attempt_id= 'attempt-001',
        worker_pid= os.getpid(),
        outcome= outcome,
    )
    failure = InfrastructureFailure(
        error_type= 'BrokenProcessPool',
        message= 'worker process terminated',
    )

    with pytest.raises(ValueError):
        batch = BatchTaskResult(
            task_id= outcome.task_id,
            attempt_id= result.attempt_id,
            state= ExecutionState.FAILED,
            process_result= result,
            infrastructure_failure= failure
        )

def test_missing_result_paths_are_rejected() -> None:
    with pytest.raises(ValueError):
        batch = BatchTaskResult(
            task_id= 'task-001',
            attempt_id= 'attempt-001',
            state= ExecutionState.SUCCEEDED
        )

def test_mismatched_task_ids_is_rejected() -> None:
    outcome = TaskOutcome(
            task_id= 'task-001',
            status= OutcomeStatus.SUCCESS,
            value= 'hello',
            error = None
        )
    result = ProcessExecutionResult(
        attempt_id= 'attempt-001',
        worker_pid= os.getpid(),
        outcome= outcome,
    )

    with pytest.raises(ValueError):
        batch = BatchTaskResult(
            task_id= 'task-002',
            attempt_id= result.attempt_id,
            state= ExecutionState.SUCCEEDED,
            process_result= result,
            infrastructure_failure= None,
        )

def test_mismatched_attempt_ids_is_rejected() -> None:
    outcome = TaskOutcome(
            task_id= 'task-001',
            status= OutcomeStatus.SUCCESS,
            value= 'hello',
            error = None
        )
    result = ProcessExecutionResult(
        attempt_id= 'attempt-001',
        worker_pid= os.getpid(),
        outcome= outcome,
    )

    with pytest.raises(ValueError):
        batch = BatchTaskResult(
            task_id= outcome.task_id,
            attempt_id= 'attempt-002',
            state= ExecutionState.SUCCEEDED,
            process_result= result,
            infrastructure_failure= None,
        )

def test_success_with_failed_state_is_rejected() -> None:
    outcome = TaskOutcome(
        task_id= 'task-001',
        status= OutcomeStatus.SUCCESS,
        value= 'hello',
        error = None
    )
    result = ProcessExecutionResult(
        attempt_id= 'attempt-001',
        worker_pid= os.getpid(),
        outcome= outcome,
    )

    with pytest.raises(ValueError):
        batch = BatchTaskResult(
            task_id= outcome.task_id,
            attempt_id= result.attempt_id,
            state= ExecutionState.FAILED,
            process_result= result,
            infrastructure_failure= None,
        )

def test_infrastructure_failure_with_succeeded_state_is_rejected():
    failure = InfrastructureFailure(
        error_type= 'BrokenProcessPool',
        message= 'worker process terminated',
    )
    with pytest.raises(ValueError):
        batch = BatchTaskResult(
            task_id= 'task-001',
            attempt_id= 'attempt-001',
            state= ExecutionState.SUCCEEDED,
            process_result= None,
            infrastructure_failure= failure
        )

def test_non_enum_state_is_rejected():
    failure = InfrastructureFailure(
        error_type= 'BrokenProcessPool',
        message= 'worker process terminated',
    )
    with pytest.raises(TypeError):
        batch = BatchTaskResult(
            task_id= 'task-001',
            attempt_id= 'attempt-001',
            state= 'succeeded',
            process_result= None,
            infrastructure_failure= failure
        )

def test_unsupported_state_is_rejected():
    failure = InfrastructureFailure(
        error_type= 'BrokenProcessPool',
        message= 'worker process terminated',
    )
    with pytest.raises(ValueError):
        batch = BatchTaskResult(
            task_id= 'task-001',
            attempt_id= 'attempt-001',
            state= ExecutionState.RUNNING,
            process_result= None,
            infrastructure_failure= failure
        )


@pytest.mark.parametrize('result', [[], 123, 'not a process result'])
def test_invalid_process_result_is_rejected(result):

    with pytest.raises(TypeError):
        batch = BatchTaskResult(
            task_id= 'task-001',
            attempt_id= 'attempt-001',
            state= ExecutionState.SUCCEEDED,
            process_result= result,
            infrastructure_failure= None
        )

def test_frozen_model_is_rejected():
    outcome = TaskOutcome(
        task_id= 'task-001',
        status= OutcomeStatus.SUCCESS,
        value= 'hello',
        error= None,
    )
    result = ProcessExecutionResult(
        attempt_id= 'attempt-001',
        worker_pid= os.getpid(),
        outcome= outcome,
    )
    batch = BatchTaskResult(
        task_id= outcome.task_id,
        attempt_id= result.attempt_id,
        state= ExecutionState.SUCCEEDED,
        process_result= result,
        infrastructure_failure= None,
    )
    with pytest.raises(FrozenInstanceError):
        batch.state = ExecutionState.FAILED

def test_failed_outcome_with_succeeded_state_is_rejected():
    error = TaskError(
        error_type= 'failure',
        message= 'general failure'
    )
    outcome = TaskOutcome(
        task_id= 'task-001',
        status= OutcomeStatus.FAILURE,
        value = None,
        error = error, 
    )
    result = ProcessExecutionResult(
        attempt_id= 'attempt-001',
        worker_pid= os.getpid(),
        outcome= outcome,
    )

    with pytest.raises(ValueError):
        batch = BatchTaskResult(
            task_id= outcome.task_id,
            attempt_id= result.attempt_id,
            state= ExecutionState.SUCCEEDED,
            process_result= result,
            infrastructure_failure= None,
        )
