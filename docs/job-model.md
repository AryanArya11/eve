# Job Model

## Purpose

Group tasks that belong to one submitted batch.

## Inputs

- `job_id`: Identity of Job (str)
- `tasks`: Number of Unique Tasks (objects)

## Validation

- Job IDs must be strings
- Job IDs cannot be blank
- Job IDs cannot have leading or trailing whitespace
- tasks follow the same rules
- tasks must contain Task instances
- A job should contain at least one task
- Task IDs must be unique
- tasks should be immutable

##  State

Jobs are meant to contain only the identity and tasks. Runtime state should be designed seperately.

## Implications

The Job model does not run concurrently. Since its structure is immutable, the job will allow the Coordinator to safely inspect the same job while task execution state is tracked seperately.
