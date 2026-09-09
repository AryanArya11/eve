import uuid

from eve.attempt import ExecutionAttempt
from eve.state import ExecutionState
from eve.job import Job
from eve.local_queue import QueuedExecution
from eve.coordinator import LocalCoordinator
from eve.batch_result import BatchTaskResult, InfrastructureFailure

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

