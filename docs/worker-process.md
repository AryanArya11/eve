# Worker Process Boundary

## Purpose

Workers will execute the registered workloads outside the Coordinator's space.

## Security Boundary

The security boundary is created to ensure that workload strings will select known functions. Workers refer to a private dict, that holds Callable handler functions for executing a payload. Eve does not use eval or execute arbitrary Python strings. 

## Workload Registry


The registry creates an allowlist: only workload names explicitly mapped to
known handlers can execute. The leading underscore communicates that the
dictionary is an internal implementation detail.

A Private dictionary (`_WORKLOAD_HANDLERS`) is established holding known workload strings as keys to access callable handler function values.
* An execute_workload function takes the workload {`str`} and payload {`object`} as parameters, the function will determine if the workload is executable based off of whether it is a known function in the priv. `dict`. --> If so, it will call the desired workload function through a `handler` which outputs the result of the inputted `payload`.



Example mapping:

Eve uses a registry to map a Task's workload name to a predefined Python function. The workload name is treated as an identifier, not as Python code.

For example, the registry may contain:

```python
_WORKLOAD_HANDLERS = {
    "sum-range": sum_range,
}
```

A Task can request the registered workload:

```python
Task(
    task_id="task-001",
    workload="sum-range",
    payload={
        "start": 1,
        "stop": 10,
    },
)
```

Eve uses the string `"sum-range"` to select the `sum_range` function and passes the Task payload to it:

```text
"sum-range"
    -> sum_range({"start": 1, "stop": 10})
    -> 45
```

Only names present in the registry are accepted. For example, `"unknown-workload"` is rejected with a `ValueError`.

The registry acts as an allowlist. Eve does not evaluate the workload string as Python code and does not dynamically execute arbitrary functions supplied by a Task.

## Sum Range Contract

- payload structure
    * The `payload` is expected as a `dict`
    * Runs through verifications to process request
    * The payload does not contain both `start` and `stop`
    * Outputs summed integer of all values between `start` (included) and `stop` (excluded)

- start-inclusive behavior
    * `start` is always included in the `sum-range` function.

- stop-exclusive behavior
    * `stop` is always excluded in the `sum-range` function.

- return value
    * Returns `int`

- accepted and rejected types
    * Accepts:
        - `dict` as input
        - `int` as `payload['start']` and `payload['stop']` values
    * Rejects:
        - All other datatypes

## Validation

- Payload Errors
    TypeError:
    * payload is not a `dict`
    * `start` and `stop` are not `int`
    * `start` or `stop` is a Boolean.
    
    ValueError:
    * start cannot be greater than stop

- Workload Errors
    TypeError:
    * workload is not a `str`

    ValueError:
    * workload is not member of `_WORKLOAD_HANDLERS`

## Future Worker Flow

Task workload and payload
-> registered handler
-> returned value or exception
-> TaskOutcome

## Concurrency

Workload functions must be module-level so they can later be serialized for windows spawned worker processes.