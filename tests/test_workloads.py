import pytest

from eve.workloads import execute_workload, sum_range

def test_sum_range_returns_expected_result() -> None:
    payload = {'start' : 1, 'stop': 10}
    assert sum_range(payload=payload) == 45

def test_sum_range_supports_empty_range() -> None:
    payload = {'start' : 0, 'stop': 0}
    assert sum_range(payload=payload) == 0

@pytest.mark.parametrize('payload', [[], (), None])
def test_sum_range_rejects_non_dictionary_payload(payload: object) -> None:
    with pytest.raises(TypeError):
        sum_range(payload=payload)

@pytest.mark.parametrize('payload', [
    {'start': 1},
    {'stop': 10},
    {},
])
def test_sum_range_rejects_missing_field(payload: object) -> None:
    with pytest.raises(ValueError):
        sum_range(payload=payload)

@pytest.mark.parametrize('payload', [
    {'start' : 1, 'stop' : 2.5},
    {'start' : None, 'stop' : 10},
    {'start' : True, 'stop' : 2.5},
])
def test_sum_range_rejects_non_integer_field(payload: object) -> None:
    with pytest.raises(TypeError):
        sum_range(payload=payload)

@pytest.mark.parametrize('payload', [
    {"start": True, "stop": 10},
    {"start": 1, "stop": False}
])
def test_sum_range_rejects_boolean_field(payload: object) -> None:
    with pytest.raises(TypeError):
        sum_range(payload=payload)

@pytest.mark.parametrize('payload', [
    {'start' : 10, 'stop' : 1},
    {'start' : 7, 'stop' : 6},
    {'start' : 90, 'stop' : 20},
])
def test_sum_range_rejects_backward_range(payload: object) -> None:
    with pytest.raises(ValueError):
        sum_range(payload=payload)

def test_execute_workload_selects_registered_handler() -> None:
    workload = 'sum-range'
    payload = {'start':1, 'stop':10}  
    assert execute_workload(workload=workload, payload=payload) == 45

@pytest.mark.parametrize('workload', ['sum-list', 'sub-range', 'test-sum-range'])
def test_execute_workload_rejects_unknown_name(workload: object) -> None:
    payload = {'start':1, 'stop':10}
    with pytest.raises(ValueError):
        execute_workload(workload=workload, payload=payload)

@pytest.mark.parametrize('workload', [None, 123, []])
def test_execute_workload_rejects_non_string_name(workload: object) -> None:
    payload = {'start':1, 'stop':10}
    with pytest.raises(TypeError):
        execute_workload(workload=workload, payload=payload)

def test_echo_returns_none() -> None:
    payload = None
    exec = execute_workload(workload='echo', payload=payload)

    assert exec is None

def test_echo_returns_object() -> None:
    payload = {'start':1, 'stop':10}
    exec = execute_workload(workload='echo', payload=payload)

    assert exec is payload