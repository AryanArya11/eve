import pickle
from dataclasses import FrozenInstanceError

import pytest

from eve.task import Task

def test_valid_task_preserves_value() -> None:
    payload = {"start": 1, "stop": 10}

    task  = Task(
        task_id = "task-001",
        workload = "sum-range",
        payload = payload,
    )

    assert task.task_id == "task-001"
    assert task.workload == "sum-range"
    assert task.payload == payload

@pytest.mark.parametrize("task_id", ["", "   "])    
def test_blank_task_id_is_rejected(task_id: str) -> None:
    with pytest.raises(ValueError):
        Task(
            task_id=task_id,
            workload="sum-range",
            payload={} 
        )

@pytest.mark.parametrize("workload", ["", "   "])
def test_blank_workload_is_rejected(workload: str) -> None:
    with pytest.raises(ValueError):
        Task(
            task_id = "task-001",
            workload = workload,
            payload = {}
        )

@pytest.mark.parametrize("workload", [None, 123, []])
def test_non_string_workload_is_rejected(workload: object) -> None:
    with pytest.raises(TypeError):
        Task(
            task_id = "task-001",
            workload= workload,
            payload = {}
        )

def test_leading_or_trailing_workload_whitespace_is_rejected() -> None:
    with pytest.raises(ValueError):
        Task(
            task_id = "task-001",
            workload= '  sum-range  ',
            payload = {}
        )

@pytest.mark.parametrize("task_id", [None, 123, []])
def test_non_string_task_id_is_rejected(task_id: object) -> None:
    with pytest.raises(TypeError):
        Task(
            task_id = task_id,
            workload = "sum-range",
            payload = {}
        )

def test_leading_or_trailing_task_id_whitespace_is_rejected() -> None:
    with pytest.raises(ValueError):
            Task(
                task_id = "  task-001  ",
                workload = "sum-range",
                payload = {}
            )

def test_task_is_frozen() -> None:
    task = Task(
                "task-001",
                "sum-range",
                {"start": 1}
            )

    with pytest.raises(FrozenInstanceError):
        task.task_id = "task-002"


def test_task_survives_pickle_round_trip() -> None:
    original = Task(
        task_id="task-001",
        workload="sum-range",
        payload={"start": 1, "stop": 10},
    )

    serialized = pickle.dumps(original)
    restored = pickle.loads(serialized)

    assert restored == original