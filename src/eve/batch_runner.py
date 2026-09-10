import uuid
from multiprocessing import get_context
from concurrent.futures import ProcessPoolExecutor, as_completed

from eve.attempt import ExecutionAttempt
from eve.state import ExecutionState
from eve.job import Job
from eve.local_queue import QueuedExecution
from eve.coordinator import LocalCoordinator
from eve.outcome import OutcomeStatus
from eve.batch_result import BatchTaskResult, InfrastructureFailure
from eve.process_executor import _execute_with_process_metadata

def _generate_attempt_id() -> str:
    attempt_id = uuid.uuid4()
    return str(attempt_id)

def _prepare_executions(job: Job) -> tuple[QueuedExecution, ...]:
    ready_executions = []
    for task in job.tasks:
        execution = ExecutionAttempt(
                attempt_id= _generate_attempt_id(),
                task_id= task.task_id,
                attempt_number= 1,
        )
        queued = QueuedExecution(
            task = task,
            attempt = execution,
        )
        ready_executions.append(queued)
    ready_executions = tuple(ready_executions)
    return ready_executions
        

def run_job_sequential(job: object) -> tuple[BatchTaskResult, ...]:
    if not isinstance(job, Job):
        raise TypeError('Must be a Job member')

    executions = _prepare_executions(job)

    coordinator = LocalCoordinator()

    for execution in executions:
        coordinator.submit(execution)

    results = []

    for execution in executions:
        attempt_id = execution.attempt.attempt_id

        try:
            process_result = coordinator.run_next()
        except Exception as error:
            state = coordinator.state_for(attempt_id)

            error_type = type(error).__name__
            message = str(error).strip()

            if not message.strip():
                message = "infrastructure failure occurred"

            failure = InfrastructureFailure(
                error_type= error_type,
                message= message,
            )

            batch = BatchTaskResult(
                task_id= execution.task.task_id,
                attempt_id= attempt_id,
                state= state,
                process_result= None,
                infrastructure_failure= failure,
            )

        else:
            state = coordinator.state_for(attempt_id)

            batch = BatchTaskResult(
                task_id= execution.task.task_id,
                attempt_id= attempt_id,
                state= state,
                process_result= process_result,
                infrastructure_failure= None,
            )
        results.append(batch)

    return tuple(results)

def run_job_parallel(job: object, max_workers: int) -> tuple[BatchTaskResult, ...]:
    if not isinstance(job, Job):
        raise TypeError("job parameter only accepts members of Job class")

    if isinstance(max_workers, bool) or not isinstance(max_workers, int):
        raise TypeError("Max Workers must be an integer value")

    if max_workers < 1:
        raise ValueError("Max Workers must be at least one")

    executions = _prepare_executions(job)

    # Mapping each execution's original position
    future_mapping = {}
    mapped_results_by_index = {}


    # Creating PoolProcessExecutor

    with ProcessPoolExecutor(
        max_workers= max_workers,
        mp_context= get_context('spawn'),
    ) as executor:
        for idx, execution in enumerate(executions):
            future = executor.submit(
                _execute_with_process_metadata,
                execution,
            )
            future_mapping[future] = (idx, execution)
        for completed_future in as_completed(future_mapping):
            index, execution = future_mapping[completed_future]

            try:
                process_result = completed_future.result()

            except Exception as error:
                message = str(error).strip()

                if not message:
                    message = "infrastructure failure occurred"

                infrastructure_failure = InfrastructureFailure(
                    error_type= type(error).__name__,
                    message= message,
                )
                batch_result = BatchTaskResult(
                    task_id= execution.task.task_id,
                    attempt_id= execution.attempt.attempt_id,
                    state= ExecutionState.FAILED,
                    process_result= None,
                    infrastructure_failure= infrastructure_failure,
                )

                mapped_results_by_index[index] = batch_result

            else:
                if process_result.outcome.status is OutcomeStatus.SUCCESS:
                    state = ExecutionState.SUCCEEDED
                else:
                    state = ExecutionState.FAILED

                batch_result = BatchTaskResult(
                    task_id= execution.task.task_id,
                    attempt_id= execution.attempt.attempt_id,
                    state = state,
                    process_result= process_result,
                    infrastructure_failure= None,
                )

                mapped_results_by_index[index] = batch_result

    return tuple(
        mapped_results_by_index[index]
        for index in range((len(executions)))
    )
