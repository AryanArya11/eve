# Execution Attempt Model

## Purpose

Represent one attempt to execute a task.

## Inputs
- `attempt_id`: Unique Identity of this attempt (str)
- `task_id`: Identity of the Task being attempted (str)
- `attempt_number`: One-based retry number (int)

## Validation

- IDs must be nonblank strings
- IDs cannot contain surrounding whitespace
- Attempt numbers must be integers
- Booleans are not valid attempt numbers
- Attempt numbers must be at least one
- Attempts are immutable and serializable

## State

ExecutionAttempt contains stable identity information only. Runtime lifecycle state and outcomes are tracked separately.

## Concurrency

The model does not perform concurrent work. Its immutability makes it safe to pass between the coordinator and worker processes.