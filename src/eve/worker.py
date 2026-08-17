from eve.local_queue import QueuedExecution
from eve.outcome import OutcomeStatus, TaskOutcome, TaskError
from eve.workloads import execute_workload

def execute_queued_execution(execution: object) -> TaskOutcome:
    if not isinstance(execution, QueuedExecution):
        raise TypeError(f"Execution ({execution}) is not a member of QueuedExecution")

    task = execution.task

    try:
        value = execute_workload(
            task.workload,
            task.payload,
        )

    except Exception as e:
        error_type = type(e).__name__
        message = str(e).strip()

        if message == '':
            message = "workload execution failed"

        structured_error = TaskError(
            error_type = error_type,
            message = message,
        )

        return TaskOutcome(
            task_id = task.task_id,
            status = OutcomeStatus.FAILURE,
            value = None,
            error = structured_error
        )

    return TaskOutcome(
        task_id = task.task_id,
        status = OutcomeStatus.SUCCESS,
        value = value,
        error = None
    )