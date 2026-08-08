# Outcome Model

## Purpose

States what happens after the Task has ran.

## Inputs

TaskOutcome
- `task_id`: Executed task (str)
- `status`: Whether task returns (OutcomeStatus)
- `value`: Retrieved task return value (object)
- `error`: Structured failure information (TaskError)

TaskError
- `error_type`: Recorded Error (str)
- `message`: Description of Error (str)

## Validation

- `task_id` follows the same identity rules as the existing IDs.
- Status must be a recognized `OutcomeStatus`.
- A successful outcome may contain any value, including None.
- A successful outcome cannot contain an `TaskError`.
- A failed outcome must contain a structured error.
- A failed outcome cannot also contain a successful value.
- Errors and Outcomes should be immutable.
- Errors and Outcomes must survive serialization.

## State

Outcome model is designed to communicate the result of an executed Task. This occurs after Runtime state.



