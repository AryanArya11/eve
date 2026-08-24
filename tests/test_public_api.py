import eve

EXPECTED_PUBLIC_NAMES = set([
    'Task',
    'Job',
    'ExecutionAttempt',
    'OutcomeStatus',
    'TaskError',
    'TaskOutcome',
    'ExecutionState',
    'QueuedExecution',
    'ProcessExecutionResult',
    'LocalCoordinator',
])

def test_public_names_are_declared():
    test = set(eve.__all__)

    assert test == EXPECTED_PUBLIC_NAMES

def test_public_names_are_accessible():
    for name in EXPECTED_PUBLIC_NAMES:
        assert hasattr(eve, name)