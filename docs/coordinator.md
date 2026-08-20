# Local Coordinator

## Purpose

`LocalCoordinator` is responsible for connecting:

- The local execution queue
- Execution state transitions
- Worker-process execution
- Process results

It coordinates one queued execution at a time (sequentially) for v0.1A.

## Responsibilities

The `LocalCoordinator` tracks attempt states while coordinating execution and error handling.

It does so by accepting validated `QueuedExecution` objects and rejecting duplicate attempt IDs. An attempt ID remains unique for the lifetime of a coordinator, even after that attempt has finished.

It retrieves work from the queue, updates the attempt's execution state, and sends the work across the process boundary.

Failures are handled differently depending on where they occur:

- If it is a workload failure, the worker will return a `ProcessExecutionResult` with an outcome status `FAILURE`.
    * The state will become `FAILED` and the result is stored.

- If it is an infrastructure failure, the executor raises an exception.
    * The state will become `FAILED`, the exception is propagated, and no result is stored because the worker never returned one.

## What the Coordinator Owns

The `Coordinator` owns three internal collections:

- `_queue`: executions waiting to run
- `_states`: mapping of attempt IDs to execution states
- `_results`: mapping of attempt IDs to process results

The attempt ID is used as the key to reference the specific state or result of that execution attempt.

## Public Interface

### `submit(execution)`

The `submit(execution)` method takes in a `QueuedExecution` object.

- Validation checks whether execution is a `QueuedExecution` and raises `TypeError` if it is not.
- The attempt ID is retrieved from the execution object. The `LocalCoordinator` raises `ValueError` if that attempt ID has already been submitted.
- `SUBMITTED` is the conceptual starting state; the execution object does not store this state itself. The coordinator validates the transition from `SUBMITTED` to `QUEUED`.
- `LocalCoordinator` stores the execution in its local queue using the `enqueue()` method.
- `LocalCoordinator` records `QUEUED` in its `_states` dictionary using the attempt ID as the key.

### `run_next()`

The `run_next()` method returns a `ProcessExecutionResult` when the process executor returns normally. It raises `IndexError` if the queue is empty and propagates infrastructure exceptions if process execution fails.

- A local variable `next_execution` is created which stores the first `QueuedExecution` in the Coordinator's queue using the `dequeue()` method.
- Attempt ID is stored in local variable by grabbing `next_execution`'s attempt ID.
- Using private `_transition(self, attempt_id, target)`, the `LocalCoordinator` changes the attempt's state to `ASSIGNED` and then to `RUNNING` (all of these changes are updated in `_states`).
- Exception Handling is carried out with try-except block:
    * Try: A local variable `ran` stores the result of `next_execution` through the `execute_in_process()` function.
    * Except: `_transition` changes the attempt's state from `RUNNING` to `FAILED`, and the infrastructure exception is raised again. No result is stored.
- If-else block runs to check `OutcomeStatus`:
    * If `SUCCESS`, then `_transition` changes the attempt's execution state from `RUNNING` to `SUCCEEDED`.
    * If `FAILURE`, then `_transition` changes the attempt's execution state from `RUNNING` to `FAILED`.
- The Coordinator's `_results` dictionary stores `ran` for its corresponding `attempt_id`.
- `ran` is returned as a `ProcessExecutionResult`.

### `pending_count()`

- The `pending_count()` method returns the number of executions still waiting in the Coordinator's queue. Dequeued, running, and completed executions are not included.

### `has_pending_work()`

- The `has_pending_work()` method returns whether the queue contains any waiting executions.

### `state_for(attempt_id)`

- The `state_for()` method accepts an attempt ID and returns the execution state stored in the `_states` dictionary.
- A `KeyError` is raised if the attempt ID is not in the `_states` dictionary, with an error message stating `Unknown ID (attempt_id)`.

### `result_for(attempt_id)`

- The `result_for()` method accepts an attempt ID and returns the corresponding `ProcessExecutionResult` stored in the `_results` dictionary. A result exists only when the process executor returned one.
- A `KeyError` is raised if the attempt ID is not in the `_results` dictionary. This occurs before an attempt finishes and after an infrastructure failure in which the worker returned no result.

## Execution Flow

```text
SUBMITTED
    ↓
QUEUED
    ↓
ASSIGNED
    ↓
RUNNING
    ├── SUCCESS outcome → SUCCEEDED
    ├── FAILURE outcome → FAILED
    └── Infrastructure exception → FAILED
```

A `SUCCESS` or `FAILURE` outcome produces a stored `ProcessExecutionResult`. An infrastructure exception produces no stored result because execution did not return normally.

## Current Limitations

For v0.1A, the `LocalCoordinator`:

- Runs one queued execution per `run_next()` call.
- Coordinates work sequentially and blocks until the worker process returns or raises.
- Creates a new process executor for each execution rather than reusing a persistent worker pool.
- Does not automatically retry failed attempts.
- Does not aggregate complete jobs or batches.
- Stores state and results only in memory.
- Is not designed for concurrent calls from multiple threads.
