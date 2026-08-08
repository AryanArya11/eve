import pickle
from dataclasses import FrozenInstanceError

import pytest

from eve.outcome import OutcomeStatus, TaskError, TaskOutcome


def test_successful_outcome_preserves_returned_value() -> None:
    outcome = TaskOutcome(
        task_id= 'task-001',
        status= OutcomeStatus.SUCCESS,
        value= 42,
    )

    assert outcome.task_id == 'task-001'
    assert outcome.status is OutcomeStatus.SUCCESS
    assert outcome.value == 42
    assert outcome.error is None

def test_successful_outcome_can_return_None() -> None:
    outcome = TaskOutcome(
        task_id= 'task-001',
        status= OutcomeStatus.SUCCESS,
        value= None
    )

    assert outcome.status is OutcomeStatus.SUCCESS
    assert outcome.value is None
    assert outcome.error is None

def test_failed_outcome_preserves_structured_error() -> None:
    error = TaskError(
        error_type= 'ValueError',
        message= 'start must be less than stop'
    )

    outcome = TaskOutcome(
        task_id='task-001',
        status=OutcomeStatus.FAILURE,
        error= error
    )

    assert outcome.status is OutcomeStatus.FAILURE
    assert outcome.value is None
    assert outcome.error == error


def test_succesful_outcome_with_error_is_rejected() -> None:
    error = TaskError(
        error_type="ValueError",
        message='start and stop are swapped'
    )

    with pytest.raises(ValueError):
        TaskOutcome(
            task_id='task-001',
            status=OutcomeStatus.SUCCESS,
            value= 42,
            error= error
        )

def test_failed_outcome_without_error_is_rejected() -> None:
    with pytest.raises(ValueError):
        TaskOutcome(
            task_id='task-001',
            status=OutcomeStatus.FAILURE,
        )

def test_failed_outcome_with_returned_value_is_rejected() -> None:
    error = TaskError(
        'ValueError',
        'Unexpected Result'
    )

    with pytest.raises(ValueError):
        TaskOutcome(
            'task-001',
            OutcomeStatus.FAILURE,
            42,
            error=error
        )

def test_failed_outcome_with_non_task_error_is_rejected() -> None:
    with pytest.raises(TypeError):
        TaskOutcome(
            'task-001',
            OutcomeStatus.FAILURE,
            value=None,
            error= "execution failed"
        )

@pytest.mark.parametrize('task_id', [None, 123, []])
def test_invalid_task_id_values_is_rejected(task_id: str) -> None:
    with pytest.raises(TypeError):
        outcome = TaskOutcome(
            task_id = task_id,
            status= OutcomeStatus.SUCCESS,
            value=42,
            error= None,
        )

@pytest.mark.parametrize('task_id', ['', '   '])
def test_blank_task_id_values_is_rejected(task_id: str) -> None:
    with pytest.raises(ValueError):
        outcome = TaskOutcome(
            task_id = task_id,
            status= OutcomeStatus.SUCCESS,
            value=42,
            error= None,
        )

@pytest.mark.parametrize('status', [None, 123, [], '', '   '])
def test_invalid_status_values_is_rejected(status: object) -> None:
    with pytest.raises(TypeError):
        outcome = TaskOutcome(
            task_id='task-001',
            status= status,
            value = 42
        )

@pytest.mark.parametrize(('error_type, message'), [("", 'message'),('   ', 'message'),('ValueError', ''),('ValueError', '   ')],)
def test_task_error_blank_field_validation(error_type: str, message: str) -> None:
    with pytest.raises(ValueError):
        error = TaskError(
            error_type = error_type,
            message = message,
        )

@pytest.mark.parametrize(('error_type, message'), [(None, 'msg'), (123, 'msg'), ('ValueError', None), ('ValueError', 123)])
def test_task_error_non_string_field_validation(error_type: str, message: str) -> None:
    with pytest.raises(TypeError):
        error = TaskError(
            error_type= error_type,
            message= message
        )

@pytest.mark.parametrize("task_id", [" task-001", "task-001 "])
def test_task_id_surrounding_whitespace_is_rejected(task_id: str) -> None:
    with pytest.raises(ValueError):
        TaskOutcome(
            task_id=task_id,
            status=OutcomeStatus.SUCCESS,
        )

@pytest.mark.parametrize(
    ("error_type", "message"),
    [
        (" ValueError", "message"),
        ("ValueError ", "message"),
        ("ValueError", " message"),
        ("ValueError", "message "),
    ],
)
def test_task_error_surrounding_whitespace_is_rejected(
    error_type: str,
    message: str,
) -> None:
    with pytest.raises(ValueError):
        TaskError(
            error_type=error_type,
            message=message,
        )    

def test_task_error_frozen() -> None:
    error = TaskError(
        "ValueError",
        "Unexpected Input",
    )

    with pytest.raises(FrozenInstanceError):
        error.error_type = 'TypeError'

def test_task_outcome_frozen() -> None:
    outcome = TaskOutcome(
        "task-001",
        OutcomeStatus.SUCCESS,
        42,
        None,
    )

    with pytest.raises(FrozenInstanceError):
        outcome.task_id = 'task-002'




def test_succesful_task_outcome_survives_pickle_round_trip() -> None:

    original = TaskOutcome(
        "task-001",
        OutcomeStatus.SUCCESS,
        42,
        None,
    )

    serialized = pickle.dumps(original)
    restored = pickle.loads(serialized)

    assert restored == original


def test_failed_task_outcome_survives_pickle_round_trip() -> None:

    error = TaskError(
        "ValueError",
        "Unexpected Input",
    )

    original = TaskOutcome(
        'task-001',
        OutcomeStatus.FAILURE,
        error= error
    )

    serialized = pickle.dumps(original)
    restored = pickle.loads(serialized)

    assert restored == original