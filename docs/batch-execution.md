# Local Batch Execution

## Purpose

- Batch execution allows the `LocalCoordinator` to run one `Job` containing multiple Tasks. The current sequential runner executes each Task one at a time through `run_next()`; concurrent execution belongs to the future parallel runner.
- Eve accepts a `Job` instead of requiring callers to submit individual Tasks. This makes it practical to submit multiple workload types together and later execute them through a parallel runner.
- The sequential implementation serves as a correctness baseline for parallel execution. Both runners receive equivalent Jobs and should produce equivalent logical results; only their execution strategy and timing should differ.

## Inputs
- A validated `Job` is the primary input and represents the batch.
- Worker count is relevant to the future parallel runner, where it will limit how many Tasks may execute simultaneously.
- The runner accepts a frozen `Job` whose Tasks are stored in a tuple.
- Each task result must distinguish between workload execution and execution infrastructure. A successful task and a workload failure both contain a ProcessExecutionResult, because the worker successfully completed the execution protocol and returned an outcome. An infrastructure failure contains no ProcessExecutionResult, because Eve was unable to complete that protocol, and instead records structured infrastructure failure information. Every task must have exactly one of these outcome paths so no task can disappear without explanation.

## Outputs
- The runner returns a tuple containing one `BatchTaskResult` per Task.
- Each `BatchTaskResult` is immutable and contains a task ID, attempt ID, execution state, optional process result, and optional infrastructure failure.
- Successful workloads and workload failures contain a `ProcessExecutionResult`. Infrastructure failures contain an `InfrastructureFailure` instead.
- Workload and infrastructure failures are returned as structured results.


## Attempt Creation
- An `ExecutionAttempt` is created by the runner for each Task.
- The first attempt number should be one.
- A unique attempt ID is generated for each Task using `uuid4()` and stored as a string.
- The attempt's task ID must match the Task contained in its `QueuedExecution`.


## Submission Flow

Receive Job
→ iterate through tasks
→ create attempt for each task
→ create QueuedExecution
→ submit to coordinator
→ execute until no pending work remains
→ collect results

- All `ExecutionAttempt` and `QueuedExecution` objects are prepared before coordinator submission. This validates the prepared objects before execution begins.
- The current runner does not provide atomic submission or rollback. If submission fails partway through, some executions may already be queued; handling that case is outside the current milestone.
 
## Result Ordering
- The returned result order always matches the order of `Job.tasks`, including when Tasks fail.
- Predictable ordering allows callers to match each result to its original Task, display results, compare test runs, and debug failures. Callers do not need to account for a different result order each time the Job runs.
- Parallel Execution may complete certain `Tasks` sooner than others, but Eve should rearrange the collected results into the original Job order before returning them.

## Failure Behavior
- A workload failure occurs when Eve's worker completes the execution protocol but the requested workload raises an error, such as an invalid payload or unknown workload.
- A workload failure contains a `ProcessExecutionResult` because the worker returned a failed `TaskOutcome`.
- An infrastructure failure occurs when Eve's execution machinery fails before a worker can return a valid `ProcessExecutionResult`. An example would be a worker process crashing.
- `process_result` is set to `None` for an infrastructure failure because no valid process result was returned. The `infrastructure_failure` field records the error instead.
- The design of the batch runner allows for other Tasks to be executed while a failed Task's error is recorded, so one failure does not terminate the entire batch.
- If an infrastructure exception contains a blank message, the runner records `"infrastructure failure occurred"` as a nonblank fallback message.

## Empty and Partial Batches
- An empty `Job` cannot reach the runner because `Job` validation rejects an empty Tasks tuple.
- `ExecutionAttempt` and `QueuedExecution` objects are prepared before submission so their order and Task relationships are established before execution.
- If a Task fails during execution, its error is recorded and the runner continues processing the remaining Tasks.
- Every executed Task has an associated `BatchTaskResult` containing either a process result or an infrastructure failure.

## Sequential Baseline

- The sequential runner prepares and submits every execution, then processes one queued Task at a time through `LocalCoordinator.run_next()`.
- It provides a predictable reference implementation for validating the logical results and ordering of the future parallel runner.

## Future Parallel Execution

- During parallel execution, multiple Tasks may run simultaneously and finish in a different order from `Job.tasks`. Eve should collect those results and return them in the original Job order.
- The parallel runner should accept the same validated `Job` input and return one `BatchTaskResult` for every Task, using the same workload-failure and infrastructure-failure rules as the sequential runner.
- A worker-count limit controls the maximum number of Tasks that can execute at the same time. When every worker is occupied, the remaining Tasks wait until a worker becomes available.
- A failure in one Task should still be recorded without preventing unrelated Tasks from completing.
- The sequential runner provides a correctness baseline. The same Job can be executed using both runners and their Task IDs, states, outcome values, errors, and result ordering can be compared.

## Current Non-Goals

- Remote-node execution, automatic retries, timeouts, cancellation, persistent result storage, hardware-aware scheduling, and atomic submission rollback are outside the current milestone.

## Open Questions

- What should the default parallel worker count be?
- Should infrastructure failures eventually be retried?
- Should Eve support fail-fast batch execution?
- Should partially submitted batches be rolled back?
