from collections.abc import Callable

def sum_range(payload: object) -> int:

    if not isinstance(payload, dict):
        raise TypeError("Payload must be a dict")

    if 'start' not in payload or 'stop' not in payload:
        raise ValueError("check if payload has 'start' and 'stop'")

    start = payload['start']
    stop = payload['stop']

    if isinstance(start, bool) or isinstance(stop, bool):
        raise TypeError(f"payload 'start' or 'stop' values are booleans")
    
    if not isinstance(start, int):
        raise TypeError(f"check if payload 'start' value is an int")

    if not isinstance(stop, int):
        raise TypeError(f"check if payload 'stop' value is an int")

    if start > stop:
        raise ValueError(f"'start' range may not be larger than 'stop' range")


    count = 0

    for i in range(start, stop):
        count += i
    return count

_WORKLOAD_HANDLERS: dict[str, Callable[[object], object]] = {
    "sum-range": sum_range,
}

def execute_workload(workload: object, payload: object) -> object:
    if not isinstance(workload, str):
        raise TypeError("Workload must be string")

    if workload not in _WORKLOAD_HANDLERS:
        raise ValueError(f"Workload ({workload}) is unknown")

    handler = _WORKLOAD_HANDLERS[workload]
    result = handler(payload)

    return result





