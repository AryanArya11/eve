import pickle

import pytest

from eve.state import (
    ExecutionState,
    can_transition,
    is_terminal,
    validate_transition,
)


@pytest.mark.parametrize(
    ("state", "serialized_value"),
    [
        (ExecutionState.SUBMITTED, "submitted"),
        (ExecutionState.QUEUED, "queued"),
        (ExecutionState.ASSIGNED, "assigned"),
        (ExecutionState.RUNNING, "running"),
        (ExecutionState.SUCCEEDED, "succeeded"),
        (ExecutionState.FAILED, "failed"),
        (ExecutionState.CANCELLED, "cancelled"),
    ],
)
def test_state_preserves_serialized_value(
    state: ExecutionState,
    serialized_value: str,
) -> None:
    assert state.value == serialized_value


@pytest.mark.parametrize(
    "state",
    [
        ExecutionState.SUCCEEDED,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
    ],
)
def test_terminal_state_returns_true(state: ExecutionState) -> None:
    assert is_terminal(state) is True


@pytest.mark.parametrize(
    "state",
    [
        ExecutionState.SUBMITTED,
        ExecutionState.QUEUED,
        ExecutionState.ASSIGNED,
        ExecutionState.RUNNING,
    ],
)
def test_nonterminal_state_returns_false(state: ExecutionState) -> None:
    assert is_terminal(state) is False


@pytest.mark.parametrize("state", [None, "running", 123])
def test_terminal_check_rejects_invalid_type(state: object) -> None:
    with pytest.raises(TypeError):
        is_terminal(state)


LEGAL_CASES = [
    (ExecutionState.SUBMITTED, ExecutionState.QUEUED),
    (ExecutionState.SUBMITTED, ExecutionState.CANCELLED),
    (ExecutionState.QUEUED, ExecutionState.ASSIGNED),
    (ExecutionState.QUEUED, ExecutionState.CANCELLED),
    (ExecutionState.ASSIGNED, ExecutionState.RUNNING),
    (ExecutionState.ASSIGNED, ExecutionState.FAILED),
    (ExecutionState.ASSIGNED, ExecutionState.CANCELLED),
    (ExecutionState.RUNNING, ExecutionState.SUCCEEDED),
    (ExecutionState.RUNNING, ExecutionState.FAILED),
    (ExecutionState.RUNNING, ExecutionState.CANCELLED),
]


@pytest.mark.parametrize(("current", "target"), LEGAL_CASES)
def test_legal_transition_returns_true(
    current: ExecutionState,
    target: ExecutionState,
) -> None:
    assert can_transition(current, target) is True


ILLEGAL_CASES = [
    (current, target)
    for current in ExecutionState
    for target in ExecutionState
    if (current, target) not in LEGAL_CASES
]


@pytest.mark.parametrize(("current", "target"), ILLEGAL_CASES)
def test_illegal_transition_returns_false(
    current: ExecutionState,
    target: ExecutionState,
) -> None:
    assert can_transition(current, target) is False


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (None, ExecutionState.QUEUED),
        ("submitted", ExecutionState.QUEUED),
        (ExecutionState.SUBMITTED, None),
        (ExecutionState.SUBMITTED, "queued"),
    ],
)
def test_transition_check_rejects_invalid_types(
    current: object,
    target: object,
) -> None:
    with pytest.raises(TypeError):
        can_transition(current, target)


@pytest.mark.parametrize(("current", "target"), LEGAL_CASES)
def test_validate_transition_accepts_legal_move(
    current: ExecutionState,
    target: ExecutionState,
) -> None:
    assert validate_transition(current, target) is None


@pytest.mark.parametrize(("current", "target"), ILLEGAL_CASES)
def test_validate_transition_rejects_illegal_move(
    current: ExecutionState,
    target: ExecutionState,
) -> None:
    with pytest.raises(ValueError):
        validate_transition(current, target)


def test_state_survives_pickle_round_trip() -> None:
    original = ExecutionState.RUNNING

    serialized = pickle.dumps(original)
    restored = pickle.loads(serialized)

    assert restored is original
