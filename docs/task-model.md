# Task Model

## Purpose

A task describes one logical unit of work. It doesn't describe a particular execution attempt.

## Inputs

- `task_id`: A stable, caller-supplied string.
- `workload`: The name of the supported workload.
- `payload`: The workload input

## Validation

- Task IDs must be strings
- Task IDs cannot be blank
- Task IDs cannot contain leading or trailing whitespace
- Workload names follow the same rules
- Payload picklability is checked at the process boundary, not during task construction.

## Mutability

Task definitions are frozen after creation. This prevents fields from being
reassigned, but does not recursively freeze mutable payloads.

## Excluded responsibilities

A task does not contain:

- Execution state
- Attempt number
- Worker identity
- Results
- Errors
- Timing information

Those concepts will be modeled separately.
