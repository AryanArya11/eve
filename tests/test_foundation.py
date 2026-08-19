"""0.1A foundation skeleton.

This is not a finished Eve coordinator. It is a teaching test that connects
the pieces already in the repo, in the order a coordinator would later use:

    Job
      -> Tasks
      -> ExecutionAttempts
      -> local FIFO queue
      -> legal state moves
      -> worker (same computer, same process)
      -> TaskOutcomes

Read this file top to bottom. Each step is commented in beginner language.
"""

# --- imports: the Eve pieces this test glues together -------------------

from eve.attempt import ExecutionAttempt
from eve.job import Job
from eve.local_queue import LocalExecutionQueue, QueuedExecution
from eve.outcome import OutcomeStatus
from eve.state import ExecutionState, is_terminal, validate_transition
from eve.task import Task
from eve.worker import execute_queued_execution


def test_one_job_walks_through_queue_states_and_outcomes() -> None:
    """Prove one batch can keep its IDs while work waits, runs, and finishes."""

    # ------------------------------------------------------------------
    # 1. A Job is one submitted batch. It only lists the requested work.
    #    It does not remember "running" or store answers.
    #
    #    Two Tasks:
    #    - a legal sum-range  -> should succeed with value 45
    #    - an illegal range   -> worker should return FAILURE, not crash Eve
    # ------------------------------------------------------------------
    successful_task = Task(
        task_id="task-sum",
        workload="sum-range",
        payload={"start": 1, "stop": 10},
    )
    failing_task = Task(
        task_id="task-bad",
        workload="sum-range",
        payload={"start": 10, "stop": 1},
    )
    job = Job(
        job_id="job-001",
        tasks=(successful_task, failing_task),
    )

    assert job.job_id == "job-001"
    assert len(job.tasks) == 2

    # ------------------------------------------------------------------
    # 2. An ExecutionAttempt is one try at a Task.
    #    Later, a retry would be attempt 2 of the SAME task_id.
    #    Today we only create attempt 1 for each Task.
    # ------------------------------------------------------------------
    first_attempts = []
    for task in job.tasks:
        attempt = ExecutionAttempt(
            attempt_id=f"attempt-{task.task_id}",
            task_id=task.task_id,
            attempt_number=1,
        )
        first_attempts.append(attempt)

    # ------------------------------------------------------------------
    # 3. This dict is stand-in coordinator memory.
    #    Eve has a state RULEBOOK (validate_transition) but no coordinator
    #    object yet, so the test stores "where each attempt is."
    # ------------------------------------------------------------------
    attempt_state: dict[str, ExecutionState] = {}
    for attempt in first_attempts:
        attempt_state[attempt.attempt_id] = ExecutionState.SUBMITTED

    # ------------------------------------------------------------------
    # 4. Glue Task + Attempt together. Mismatched IDs are rejected here
    #    so Eve cannot run Task A and record the result on Task B.
    # ------------------------------------------------------------------
    queued_items = []
    for task, attempt in zip(job.tasks, first_attempts, strict=True):
        queued_items.append(QueuedExecution(task=task, attempt=attempt))

    # ------------------------------------------------------------------
    # 5. Legal move: SUBMITTED -> QUEUED, then stand in line.
    #    The queue itself does not change state. We do that first.
    # ------------------------------------------------------------------
    queue = LocalExecutionQueue()
    for item in queued_items:
        current = attempt_state[item.attempt.attempt_id]
        validate_transition(current, ExecutionState.QUEUED)
        attempt_state[item.attempt.attempt_id] = ExecutionState.QUEUED
        queue.enqueue(item)

    assert queue.length() == 2
    assert queue.peek().task.task_id == "task-sum"

    # ------------------------------------------------------------------
    # 6. Dequeue oldest first (FIFO). Then ASSIGNED -> RUNNING.
    #    After RUNNING, call the existing worker. That function already
    #    converts a return value into SUCCESS or an exception into FAILURE.
    # ------------------------------------------------------------------
    recorded_outcomes = {}

    while not queue.is_empty():
        item = queue.dequeue()
        attempt_id = item.attempt.attempt_id

        validate_transition(attempt_state[attempt_id], ExecutionState.ASSIGNED)
        attempt_state[attempt_id] = ExecutionState.ASSIGNED

        validate_transition(attempt_state[attempt_id], ExecutionState.RUNNING)
        attempt_state[attempt_id] = ExecutionState.RUNNING

        outcome = execute_queued_execution(item)

        # The result must still name the same Task we dequeued.
        assert outcome.task_id == item.task.task_id

        if outcome.status is OutcomeStatus.SUCCESS:
            next_state = ExecutionState.SUCCEEDED
        else:
            next_state = ExecutionState.FAILED

        validate_transition(attempt_state[attempt_id], next_state)
        attempt_state[attempt_id] = next_state
        recorded_outcomes[attempt_id] = outcome

    # ------------------------------------------------------------------
    # 7. Aggregate checks: every ID survived, both attempts finished,
    #    success and failure stayed explicit, and the Job was not mutated.
    # ------------------------------------------------------------------
    assert queue.is_empty()

    sum_outcome = recorded_outcomes["attempt-task-sum"]
    assert sum_outcome.status is OutcomeStatus.SUCCESS
    assert sum_outcome.value == 45
    assert sum_outcome.error is None
    assert attempt_state["attempt-task-sum"] is ExecutionState.SUCCEEDED
    assert is_terminal(attempt_state["attempt-task-sum"]) is True

    bad_outcome = recorded_outcomes["attempt-task-bad"]
    assert bad_outcome.status is OutcomeStatus.FAILURE
    assert bad_outcome.value is None
    assert bad_outcome.error is not None
    assert bad_outcome.error.error_type == "ValueError"
    assert attempt_state["attempt-task-bad"] is ExecutionState.FAILED
    assert is_terminal(attempt_state["attempt-task-bad"]) is True

    assert job.tasks[0].task_id == "task-sum"
    assert job.tasks[1].task_id == "task-bad"
