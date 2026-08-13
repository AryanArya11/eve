# Local Queue

## Purpose

A FIFO Queue to allow the oldest Execution to leave first.

## States

- `Task`: Class containing Workload and Payload (Task)
- `ExecutionAttempt`: Identifying the particular try (ExecutionAttempt)

## Validation

Workers expect a Task and ExecutionAttempt, so...

- `task.task_id == attempt.task_id`: immutable

This tiny wrapper will prevent Eve from executing a Task while recording the result against another.

## Queue Flow

1. Coordinator creates an ExecutionAttempt

2. Pairs Task + Attempt as QueuedExecution

3. Validates Submitted --> QUEUED

4. LocalExecutionQueue.enqueue(item)

5. Item waits in FIFO order

6. LocalExecutionQueue.dequeue()

7. Coordinator validates QUEUED --> ASSIGNED

8. Worker receives Task and Attempt

** Queue will not change ExecutionState, the future Coordinator will combined queue operations with state changes.

## Components

- `QueuedExecution`: An immutable value object containing id information on Task and ExecutionAttmept.
    * `task`: Task object
    * `attempt`: ExecutionAttempt object
        * Corresponding `task_id` must match

- `LocalExecutionQueue`: A mutable FIFO collection of `QueuedExecution` objects
    * `peek`: peek returns the next item without removing it
        * items leave in inserted order
    * `attempt_id`: cannot appear twice simulataneously

** The coordinator exclusively owns and modifies the queue. Workers receive dequeued executions but do not directly access the queue.