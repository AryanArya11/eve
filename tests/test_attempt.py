from eve.attempt import ExecutionAttempt
import pytest
import pickle
from dataclasses import FrozenInstanceError


def test_valid_attempt_preserves_values() -> None:
    attempt = ExecutionAttempt(
        attempt_id= 'attempt-001',
        task_id= "task-001",
        attempt_number= 1
    )

    assert attempt.attempt_id == 'attempt-001'
    assert attempt.task_id == 'task-001'
    assert attempt.attempt_number == 1

def test_multiple_attempts_can_reference_same_task() -> None:
    first = ExecutionAttempt(
        attempt_id= 'attempt-001',
        task_id= "task-001",
        attempt_number= 1
    )
    second = ExecutionAttempt(
        attempt_id= 'attempt-002',
        task_id= "task-001",
        attempt_number= 2
    )

    assert first.attempt_id != second.attempt_id
    assert first.task_id == second.task_id
    assert first.attempt_number != second.attempt_number


@pytest.mark.parametrize("attempt_id", [None, 123, []])
def test_non_string_attempt_id(attempt_id: str) -> None:
    with pytest.raises(TypeError):
        attempt = ExecutionAttempt(
            attempt_id= attempt_id,
            task_id = 'task-001',
            attempt_number= 1
        )

@pytest.mark.parametrize("attempt_id", ["", "   ", " attempt-001"])
def test_blank_attempt_id(attempt_id: str) -> None:
    with pytest.raises(ValueError):
        attempt = ExecutionAttempt(
            attempt_id= attempt_id,
            task_id = 'task-001',
            attempt_number= 1
        )

@pytest.mark.parametrize("task_id", [None, 123, []])
def test_non_string_task_id(task_id: str) -> None:
    with pytest.raises(TypeError):
        attempt = ExecutionAttempt(
            attempt_id= 'attempt-001',
            task_id = task_id,
            attempt_number= 1
        )

@pytest.mark.parametrize("task_id", ['', '   ', ' task-001'])
def test_blank_task_id(task_id: str) -> None:
    with pytest.raises(ValueError):
        attempt = ExecutionAttempt(
            attempt_id= 'attempt-001',
            task_id = task_id,
            attempt_number= 1
        )

@pytest.mark.parametrize("attempt_number", [None, '1', 1.5, []])
def test_non_integer_attempt_numbers(attempt_number: int) -> None:
    with pytest.raises(TypeError):
        attempt = ExecutionAttempt(
            attempt_id = 'attempt-001',
            task_id = 'task-001',
            attempt_number = attempt_number
        )

@pytest.mark.parametrize("attempt_number", [True, False])
def test_boolean_attempt_numbers(attempt_number: int) -> None:
    with pytest.raises(TypeError):
        attempt = ExecutionAttempt(
            attempt_id = 'attempt-001',
            task_id = 'task-001',
            attempt_number = attempt_number
        )

@pytest.mark.parametrize("attempt_number", [0, -1, -10])
def test_invalid_range_attempt_numbers(attempt_number: int) -> None:
    with pytest.raises(ValueError):
        attempt = ExecutionAttempt(
            attempt_id = 'attempt-001',
            task_id = 'task-001',
            attempt_number = attempt_number
        )

def test_attempt_is_frozen() -> None:
    attempt = ExecutionAttempt(
        'attempt-001',
        'task-001',
        1
    )
    with pytest.raises(FrozenInstanceError):
        attempt.attempt_number = 2


def test_attempt_survives_pickle_round_trip() -> None:
    original = ExecutionAttempt(
        'attempt-001',
        'task-001',
        1
    )

    serialized = pickle.dumps(original)
    restored = pickle.loads(serialized)

    assert restored == original
    