import pickle
from dataclasses import FrozenInstanceError

import pytest

from eve.attempt import ExecutionAttempt
from eve.local_queue import QueuedExecution, LocalExecutionQueue
from eve.task import Task


## Small Helper File
def make_execution(task_id: str, attempt_id: str, attempt_number: int) -> QueuedExecution:
    task = Task(
        task_id = task_id,
        workload = 'sum-range',
        payload = {'start' : 1, 'stop' : 10}
    )
    attempt = ExecutionAttempt(
        attempt_id = attempt_id,
        task_id = task_id,
        attempt_number = attempt_number
    )
    return QueuedExecution(
        task = task,
        attempt = attempt
    )

@pytest.mark.parametrize("task", [None, 123, []])
def test_non_task_value_is_rejected(task: object) -> None:
    with pytest.raises(TypeError):
        execution = QueuedExecution(
            task= task,
            attempt= ExecutionAttempt(
                attempt_id= 'attempt-001',
                task_id= 'task-001',
                attempt_number= 1
            )
        )

@pytest.mark.parametrize("attempt", [None, 123, []])
def test_non_execution_attempt_is_rejected(attempt: object) -> None:
    with pytest.raises(TypeError):
        execution =  QueuedExecution(
            task = Task(
                            task_id= 'task-001',
                            workload = 'sum-range',
                            payload = {'start' : 1, 'stop' : 10},
                        ),
            attempt = attempt
        )

@pytest.mark.parametrize(('task_task_id', 'attempt_task_id'),
                         [
                             ('task-001', 'task-002'),
                             ('task-01', 'task-001'),
                             ('task-1', 'task-2')
                         ]
                    )
def test_mismatched_task_id_is_rejected(task_task_id:object, attempt_task_id:object) -> None:
    with pytest.raises(ValueError):
        execution = QueuedExecution(
            task = Task(
                task_id = task_task_id,
                workload = 'sum-range',
                payload = {'start' : 1, 'stop' : 10},
            ),
            attempt = ExecutionAttempt(
                attempt_id= 'attempt-001',
                task_id= attempt_task_id,
                attempt_number= 1
            )
        )

def test_queued_execution_is_frozen() -> None:
    execution = QueuedExecution(
        task = Task(
            task_id= 'task-001',
            workload = 'sum-range',
            payload = {'start' : 1, 'end' : 10}
        ),
        attempt = ExecutionAttempt(
            attempt_id = 'attempt-001',
            task_id = 'task-001',
            attempt_number = 1
        )
    )
    task = Task(
        task_id = 'task-002',
        workload = 'sum-range',
        payload = {'start' : 1, 'stop' : 10}
    )
    with pytest.raises(FrozenInstanceError):
        execution.task = task

def test_queued_execution_survies_pickle_round_trip() -> None:
    original = QueuedExecution(
            task = Task(
                task_id= 'task-001',
                workload = 'sum-range',
                payload = {'start' : 1, 'end' : 10}
            ),
            attempt = ExecutionAttempt(
                attempt_id = 'attempt-001',
                task_id = 'task-001',
                attempt_number = 1
            )
        )

    serialized = pickle.dumps(original)
    restored = pickle.loads(serialized)

    assert restored == original


def test_valid_task_and_attempt_are_preserved() -> None:
    task = Task( 
        task_id = 'task-001',
        workload = 'sum-range',
        payload = {'start' : 1, 'stop' : 10}
    )
    attempt = ExecutionAttempt(
        attempt_id = 'attempt-001',
        task_id = 'task-001',
        attempt_number = 1
    )
    execution = QueuedExecution(
        task = task,
        attempt = attempt
    )

    assert execution.task is task
    assert execution.attempt is attempt

def test_queue_behavior() -> None:
    queue = LocalExecutionQueue()

    assert queue.is_empty() is True
    assert queue.length() == 0

def test_enqueue_behavior() -> None:
    queue = LocalExecutionQueue()
    execution = make_execution(
        task_id= 'task-001',
        attempt_id= 'attempt-001',
        attempt_number= 1,
    )

    queue.enqueue(execution)

    assert queue.is_empty() is False
    assert queue.length() == 1
    assert queue.peek() is execution

def test_fifo_behavior() -> None:
    queue = LocalExecutionQueue()
    first = make_execution(
        attempt_id= 'attempt-001',
        task_id = 'task-001',
        attempt_number= 1
    )
    second = make_execution(
            attempt_id= 'attempt-002',
            task_id = 'task-001',
            attempt_number= 2
    )
    third = make_execution(
            attempt_id= 'attempt-003',
            task_id = 'task-001',
            attempt_number= 3
    )
    queue.enqueue(first)
    queue.enqueue(second)
    queue.enqueue(third)

    assert queue.dequeue() is first
    assert queue.dequeue() is second
    assert queue.dequeue() is third
    assert queue.is_empty() is True

def test_peek_does_not_remove() -> None:
    queue = LocalExecutionQueue()
    execution = make_execution(
        task_id = 'task-001',
        attempt_id = 'attempt-001',
        attempt_number = 1
    )
    queue.enqueue(execution)

    assert queue.peek() is execution
    assert queue.length() == 1
    assert queue.dequeue() is execution

@pytest.mark.parametrize('item', [
    None,
    123,
    Task('task-01','sum','{"start": 1}'),
    ExecutionAttempt(
            attempt_id = 'attempt-001',
            task_id = 'task-001',
            attempt_number = 1
    )
])
def test_invalid_members_enqueue_is_rejected(item: object) -> None:
    queue = LocalExecutionQueue()
    with pytest.raises(TypeError):
        queue.enqueue(item)


def test_duplicate_attempt_ids_is_rejected() -> None:
    queue = LocalExecutionQueue()
    first_execution = make_execution(
        task_id = 'task-001',
        attempt_id = 'attempt-001',
        attempt_number = 1
    )
    second_execution = make_execution(
        task_id = 'task-002',
        attempt_id = 'attempt-001',
        attempt_number = 1
    )

    queue.enqueue(first_execution)

    with pytest.raises(ValueError):
        queue.enqueue(second_execution)

    assert queue.length() == 1
    assert queue.peek() is first_execution

def test_if_re_enqueue_after_dequeue() -> None:
    queue = LocalExecutionQueue()
    execution = make_execution(
        task_id = 'task-001',
        attempt_id = 'attempt-001',
        attempt_number = 1
    )
    queue.enqueue(execution)
    queue.dequeue()
    queue.enqueue(execution)

    assert queue.length() == 1

def test_empty_operations() -> None:
    queue = LocalExecutionQueue()

    with pytest.raises(IndexError):
        queue.peek()

    with pytest.raises(IndexError):
        queue.dequeue()