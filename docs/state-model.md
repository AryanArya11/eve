# Execution State

## Purpose

Defines the lifecycle states and legal state transitions of one ExecutionAttempt.

## States

- `SUBMITTED` - the Coordinator has accepted and recorded the attempt.
- `QUEUED` - the attempt is waiting for an elegible Worker.
- `ASSIGNED` - a Worker has been selected
- `RUNNING` - the Worker has started executing it
- `SUCCEEDED` - the attempt completed successfully
- `FAILED` - the attempt ended unsuccessfully
- `CANCELLED` - the attempt was intentionally stopped

## Validation

- `is_terminal`: Means that particular attempt cannot move to another state --> `FAILED`, `SUCCEEDED`, `CANCELLED`

- `can_transition`: tells whether a requested state change is legal --> `SUBMITTED` -> `QUEUED` -> `ASSIGNED` -> `RUNNING`

- `validate_transition`: Checks if the state to state movement is allowed like, otherwise raises an error.

## Requests

The Coordinator will own, authorize, and request any transitions between state to state, waiting until a state has been executed.

## Rules

Execution State validates and approves for state-to-state movement.
