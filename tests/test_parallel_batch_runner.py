import pytest

from eve.batch_runner import run_job_parallel
import eve.batch_runner as batch_runner_module
from eve.task import Task
from eve.job import Job
from eve.outcome import OutcomeStatus
from eve.state import ExecutionState
from eve.batch_result import BatchTaskResult

def helper() -> Job:
    tasks = (
        Task('task-001', 'echo', 'first',),
        Task('task-002', 'echo', 'second'),
        Task('task-003', 'echo', 'third'),
    )
    job = Job(
        job_id= 'job-001',
        tasks = tasks
    )

    return job


@pytest.mark.parametrize('job',[123, None, []])
def test_non_job_is_rejected(job: object) -> None:
    with pytest.raises(TypeError):
        result = run_job_parallel(
            job= job,
            max_workers= 2,
        )

@pytest.mark.parametrize('max_workers', [None, 'str', 123.5, True])
def test_invalid_worker_count_types(max_workers: object) -> None:
    with pytest.raises(TypeError):
        result = run_job_parallel(
            job= helper(),
            max_workers= max_workers,
        )

@pytest.mark.parametrize('max_workers', [-100, -10, -1, 0])
def test_invalid_worker_count_values(max_workers: object) -> None:
    with pytest.raises(ValueError):
        result = run_job_parallel(
            job= helper(),
            max_workers= max_workers,
        )

def test_successful_parallel_batch_execution() -> None:
    result = run_job_parallel(
        job= helper(),
        max_workers= 2,
    )

    assert len(result) == 3
    assert isinstance(result, tuple)
    assert all(
        task_result.process_result.outcome.status == OutcomeStatus.SUCCESS
        for task_result in result
    )

    for idx, task_result in enumerate(result):
        assert isinstance(task_result, BatchTaskResult)
        assert task_result.state == ExecutionState.SUCCEEDED
        assert task_result.process_result is not None
        assert task_result.infrastructure_failure is None
        assert task_result.process_result.outcome.status is OutcomeStatus.SUCCESS 
        assert task_result.task_id == helper().tasks[idx].task_id
        assert task_result.process_result.outcome.value == helper().tasks[idx].payload


def test_workload_failure_is_recorded_and_batch_continues() -> None:
    tasks = (
        Task('task-001', 'sum-range', {'start':10, 'stop':1}),
        Task('task-002', 'echo', 'hello'),
    )
    job = Job('job-001', tasks)

    results = run_job_parallel(
        job= job,
        max_workers= 2,
    )

    # Verify Task 1 result
    assert results[0].task_id == tasks[0].task_id
    assert results[0].state is ExecutionState.FAILED
    assert results[0].process_result is not None
    assert results[0].infrastructure_failure is None
    assert results[0].process_result.outcome.status == OutcomeStatus.FAILURE
    assert results[0].process_result.outcome.error is not None

    # Verify Task 2 result
    assert results[1].task_id == tasks[1].task_id
    assert results[1].state is ExecutionState.SUCCEEDED
    assert results[1].process_result is not None
    assert results[1].infrastructure_failure is None
    assert results[1].process_result.outcome.status == OutcomeStatus.SUCCESS
    assert results[1].process_result.outcome.value == tasks[1].payload

def test_worker_reuse_is_successful() -> None:
    results = run_job_parallel(
        job= helper(),
        max_workers= 1,
    )

    assert len(results) == len(helper().tasks)
    assert len(results) > 1

    for result in results:
        assert result.process_result is not None

    worker_pid_list = [result.process_result.worker_pid for result in results]

    # convert list into set to prove one worker can suffice
    worker_pid_list = set(worker_pid_list)

   
    assert len(worker_pid_list) == 1


def test_serialization_failure_is_recorded_and_batch_continues() -> None:
    tasks = (
        Task(
            task_id= 'task-001',
            workload= 'echo',
            payload= lambda x: x**2,
        ),
        Task('task-002', 'echo', 'successful str!'),
    )
    job = Job(
        job_id= 'job-001',
        tasks= tasks,
    )

    results = run_job_parallel(
        job= job,
        max_workers= 2,
    )

    assert len(results) == 2

    # Task 1 result information
    assert results[0].task_id == tasks[0].task_id
    assert results[0].state is ExecutionState.FAILED
    assert results[0].process_result is None
    assert results[0].infrastructure_failure is not None
    assert results[0].infrastructure_failure.error_type.strip()
    assert results[0].infrastructure_failure.message.strip()

    # Task 2 result information
    assert results[1].task_id == tasks[1].task_id
    assert results[1].state is ExecutionState.SUCCEEDED
    assert results[1].process_result is not None
    assert results[1].process_result.outcome.value == tasks[1].payload
    assert results[1].infrastructure_failure is None

def test_deterministic_ordering(monkeypatch,) -> None:
    
    def fake_completion(futures: list):
        final = list(futures)
        final.reverse()
        for future in final:
            yield future

    monkeypatch.setattr(
        batch_runner_module,
        'as_completed',
        fake_completion,
    )

    results = run_job_parallel(
        job= helper(),
        max_workers= 2,
    )

    for idx, result in enumerate(results):
        assert result.task_id == helper().tasks[idx].task_id
        assert result.process_result.outcome.value == helper().tasks[idx].payload

def test_bounded_worker_count() -> None:
    tasks = (
        Task('task-001', 'echo', 'first'),
        Task('task-002', 'echo', 'second'),
        Task('task-003', 'echo', 'third'),
        Task('task-004', 'sum-range', {'start':1, 'stop':10}),
        Task('task-005', 'sum-range', {'start':5, 'stop':15}),
        Task('task-006', 'sum-range', {'start':12, 'stop':32}),
    )
    job = Job(
        job_id= 'job-001',
        tasks= tasks,
    )

    results = run_job_parallel(
        job= job,
        max_workers= 3,
    )

    worker_pid_list = [result.process_result.worker_pid for result in results]
    worker_pid_list = set(worker_pid_list)

    for result in results:
        assert result.process_result.outcome.status == OutcomeStatus.SUCCESS
        assert result.process_result is not None

    assert len(worker_pid_list) >= 1
    assert len(worker_pid_list) <= 3