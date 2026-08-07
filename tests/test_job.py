import pickle
from dataclasses import FrozenInstanceError

import pytest

from eve.task import Task
from eve.job import Job


## Testing for tasks
# Creating a global Task Object for testing Job
t = Task('task-001', 'sum-range', {"start":1, "stop":10})


def test_valid_job_preserves_value() -> None:
    tasks = (t,)
    job = Job(
        job_id = "job-001",
        tasks = (t,)
    )

    assert job.job_id == "job-001"
    assert job.tasks == tasks

@pytest.mark.parametrize("job_id", ["", "   "])
def test_blank_job_id_is_rejected(job_id: str) -> None:
    with pytest.raises(ValueError):
        Job(
            job_id=job_id,
            tasks = (t,)
        )

@pytest.mark.parametrize("job_id", [None, 123, []])
def test_non_string_job_id_is_rejected(job_id: object) -> None:
    with pytest.raises(TypeError):
        Job(
            job_id=job_id,
            tasks = (t,)
        )

def test_leading_or_trailing_job_id_whitespace_is_rejeceted() -> None:
    with pytest.raises(ValueError):
        Job(
            job_id = "  job-001  ",
            tasks = (t,)
        )

def test_list_tasks_is_rejected() -> None:
    with pytest.raises(TypeError):
        Job(
            job_id='job-001',
            tasks=[t]
        )

def test_blank_tasks_is_rejected() -> None:
    with pytest.raises(ValueError):
        Job(
            job_id="job-001",
            tasks=tuple()
        )

@pytest.mark.parametrize("invalid_member", (None, 123, 'not-a-task'))
def test_non_task_member_is_rejected(invalid_member: object) -> None:
    with pytest.raises(TypeError):
        Job(
            job_id='job-001',
            tasks=(invalid_member,),
        )

def test_duplicate_task_ids_are_rejected() -> None:
    first = Task(
        "task-001",
        "sum-range",
        {"start": 1},
    )
    second = Task(
        "task-001",
        "sum-range",
        {"start": 100},
    )
    with pytest.raises(ValueError):
        Job(
            job_id='job-001',
            tasks= (first, second),
        )

def test_diff_task_ids_with_identical_payloads_are_allowed() -> None:
    payload = {'start':1, 'stop':10}
    first = Task(
            "task-001",
            "sum-range",
            payload,
        )
    second = Task(
            "task-002",
            "sum-range",
            payload,
        )
    
    job = Job(
            job_id='job-001',
            tasks= (first, second),
        )

    assert job.tasks == (first, second)

def test_job_is_frozen() -> None:
    job = Job(
        job_id="job-001",
        tasks=(t,)
    )
    with pytest.raises(FrozenInstanceError):
        job.job_id = "job-002"

def test_job_survives_pickle_round_trip() -> None:
    original = Job(
        job_id="job-001",
        tasks=(t,),
    )

    serialized = pickle.dumps(original)
    restored = pickle.loads(serialized)

    assert restored == original