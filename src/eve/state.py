from enum import Enum


class ExecutionState(Enum):
    SUBMITTED = "submitted"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_STATES = frozenset(
    {
        ExecutionState.SUCCEEDED,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
    }
)

LEGAL_TRANSITIONS = {
    ExecutionState.SUBMITTED: frozenset(
        {ExecutionState.QUEUED, ExecutionState.CANCELLED}
    ),
    ExecutionState.QUEUED: frozenset(
        {ExecutionState.ASSIGNED, ExecutionState.CANCELLED}
    ),
    ExecutionState.ASSIGNED: frozenset(
        {
            ExecutionState.RUNNING,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
        }
    ),
    ExecutionState.RUNNING: TERMINAL_STATES,
    ExecutionState.SUCCEEDED: frozenset(),
    ExecutionState.FAILED: frozenset(),
    ExecutionState.CANCELLED: frozenset(),
}


def is_terminal(state: object) -> bool:
    if not isinstance(state, ExecutionState):
        raise TypeError("state must be an ExecutionState")

    return state in TERMINAL_STATES


def can_transition(current: object, target: object) -> bool:
    if not isinstance(current, ExecutionState):
        raise TypeError("current must be an ExecutionState")

    if not isinstance(target, ExecutionState):
        raise TypeError("target must be an ExecutionState")

    return target in LEGAL_TRANSITIONS[current]


def validate_transition(current: object, target: object) -> None:
    if not can_transition(current, target):
        raise ValueError(f"cannot transition from {current.value} to {target.value}")
