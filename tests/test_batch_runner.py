import pytest

from eve.batch_result import BatchTaskResult
from eve.batch_runner import run_job_sequential
from eve.job import Job
from eve.state import ExecutionState
from eve.task import Task
from eve.outcome import OutcomeStatus
import eve.coordinator as coordinator_module
from eve.batch_runner import _prepare_executions
from eve.local_queue import QueuedExecution


@pytest.mark.parametrize("invalid_job", [None, 123, []])
def test_non_job_is_rejected(invalid_job: object) -> None:
    with pytest.raises(TypeError):
        run_job_sequential(invalid_job)

def test_single_successful_task_returns_batch_result() -> None:
    task = Task(
        task_id = 'task-001',
        workload= 'echo',
        payload= 'hello',
    )
    job = Job(
        job_id= 'job-001',
        tasks=(task,),
    )

    results = run_job_sequential(job)

    assert isinstance(results, tuple)
    assert len(results) == 1

    result = results[0]

    assert isinstance(result, BatchTaskResult)
    assert result.task_id == task.task_id
    assert result.state is ExecutionState.SUCCEEDED
    assert result.process_result is not None
    assert result.infrastructure_failure is None
    assert result.process_result.outcome.value == 'hello'

def test_multiple_results_preserve_job_order() -> None:
    tasks = (
        Task("task-001", "echo", "first"),
        Task("task-002", "echo", "second"),
        Task("task-003", "echo", "third"),
    )
    job = Job(
        job_id="job-001",
        tasks=tasks,
    )

    results = run_job_sequential(job)

    assert len(results) == 3

    returned_task_ids = tuple(result.task_id for result in results)
    expected_task_ids = tuple(task.task_id for task in tasks)

    assert returned_task_ids == expected_task_ids

def test_workload_failure_is_recorded_and_batch_continues() -> None:
    tasks = (
        Task('task-001', 'sum-range', {'start':10, 'stop':1}),
        Task('task-002', 'echo', 'ran'),
    )
    job = Job(
        job_id= 'job-001',
        tasks= tasks,
    )

    results = run_job_sequential(job)

    assert len(results) == 2
    assert results[0].task_id == tasks[0].task_id
    assert results[0].state is ExecutionState.FAILED
    assert results[0].process_result is not None
    assert results[0].infrastructure_failure is None
    assert results[0].process_result.outcome.status is OutcomeStatus.FAILURE
    assert results[0].process_result.outcome.error is not None

    assert results[1].task_id == tasks[1].task_id
    assert results[1].state is ExecutionState.SUCCEEDED
    assert results[1].process_result is not None
    assert results[1].infrastructure_failure is None
    assert results[1].process_result.outcome.status is OutcomeStatus.SUCCESS
    assert results[1].process_result.outcome.value == tasks[1].payload

def test_unique_attempt_ids_are_successful() -> None:
    tasks = (
        Task('task-001', 'echo', 'first'),
        Task('task-002', 'echo', 'second'),
        Task('task-003', 'echo', 'third'),
    )
    job = Job(
        job_id= 'job-001',
        tasks= tasks,
    )
    results = run_job_sequential(job)
    attempt_ids = [result.attempt_id for result in results]
    unique_attempt_ids = set(attempt_ids)

    assert len(results) == len(tasks)
    assert all(
        isinstance(attempt_id, str) and attempt_id.strip()
        for attempt_id in attempt_ids
    )
    assert len(unique_attempt_ids) == len(attempt_ids)

def test_infrastructure_failure_is_recorded_and_batch_continues(monkeypatch,) -> None:
    real_execute_in_process = coordinator_module.execute_in_process
    call_count = 0

    def failing_once(execution):
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            raise RuntimeError("worker process crash occurred")

        return real_execute_in_process(execution)

    monkeypatch.setattr(
        coordinator_module,
        "execute_in_process",
        failing_once,
    )

    tasks = (
        Task('task-001', 'echo', 'first'),
        Task('task-002', 'echo', 'second'),
    )
    job = Job(
        job_id= 'job-001',
        tasks= tasks,
    )
    results = run_job_sequential(job)

    assert len(results) == 2

    failed_result = results[0]

    assert failed_result.task_id == 'task-001'
    assert failed_result.state is ExecutionState.FAILED
    assert failed_result.process_result is None
    assert failed_result.infrastructure_failure is not None
    assert failed_result.infrastructure_failure.error_type == 'RuntimeError'
    assert failed_result.infrastructure_failure.message == 'worker process crash occurred'

    succesful_result = results[1]

    assert succesful_result.task_id == 'task-002'
    assert succesful_result.state is ExecutionState.SUCCEEDED
    assert succesful_result.process_result is not None
    assert succesful_result.process_result.outcome.value == 'second'


def test_blank_message_execution_uses_fallback(monkeypatch,) -> None:
    real_execute_in_process = coordinator_module.execute_in_process
    call_count = 0    

    def fake_executor(execution):
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            raise RuntimeError()

    monkeypatch.setattr(
        coordinator_module,
        "execute_in_process",
        fake_executor,
    )

    tasks = (
        Task('task-001', 'echo', 'hello'),
    )
    job = Job(
        job_id= 'job-001',
        tasks= tasks,
    )

    result = run_job_sequential(job)

    first = result[0]

    assert len(result) == 1
    assert first.state is ExecutionState.FAILED
    assert first.process_result is None
    assert first.infrastructure_failure is not None
    assert first.infrastructure_failure.error_type == 'RuntimeError'
    assert first.infrastructure_failure.message == 'infrastructure failure occurred'

def test_preparation_helper() -> None:
    tasks = (
        Task('task-001', 'echo', 'first'),
        Task('task-002', 'echo', 'second'),
        Task('task-003', 'echo', 'third'),
    )
    job = Job(
        job_id= 'job-001',
        tasks= tasks,
    )
    executions = _prepare_executions(job)

    assert isinstance(executions, tuple)
    assert len(executions) == len(tasks)
    assert all(
        isinstance(execution, QueuedExecution)
        for execution in executions
    )
    assert all(
        execution.task.task_id == tasks[idx].task_id
        for idx, execution in enumerate(executions)
    )
    assert all(
        execution.attempt.task_id == execution.task.task_id
        for execution in executions
    )

    attempt_ids = [
        execution.attempt.attempt_id
        for execution in executions
    ]

    assert all(
        isinstance(attempt_id, str) and attempt_id.strip()
        for attempt_id in attempt_ids
    )

    assert len(set(attempt_ids)) == len(executions)

    assert all(
        execution.attempt.attempt_number == 1
        for execution in executions
    )
    