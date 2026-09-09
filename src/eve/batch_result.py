from dataclasses import dataclass

from eve.state import ExecutionState
from eve.process_executor import ProcessExecutionResult
from eve.outcome import OutcomeStatus

@dataclass(frozen=True)
class InfrastructureFailure:
    error_type: str
    message: str

    def __post_init__(self):
        self._validate_field_name("error type", self.error_type)
        self._validate_field_name("message", self.message)

    @staticmethod
    def _validate_field_name(fieldname: str, value: object):
        if not isinstance(value, str):
            raise TypeError(f"{fieldname} must be a string not {type(value)}")

        if not value.strip():
            raise ValueError(f"{fieldname} cannot be blank")

        if value != value.strip():
            raise ValueError(
                f"{fieldname} cannot have trailing or leading whitespace"
            )


@dataclass(frozen=True)
class BatchTaskResult:
    task_id: str
    attempt_id: str
    state: ExecutionState
    process_result: ProcessExecutionResult | None = None
    infrastructure_failure: InfrastructureFailure | None = None


    def __post_init__(self):
        self._validate_field_name("task_id", self.task_id)
        self._validate_field_name("attempt_id", self.attempt_id)
        self._validate_state(self.state)
        self._validate_batch()

    @staticmethod
    def _validate_field_name(fieldname: str, value: object) -> None:
        if not isinstance(value, str):
            raise TypeError(f"{fieldname} must be a string, not {type(value)}")

        if not value.strip():
            raise ValueError(f"{fieldname} cannot be blank")

        if value != value.strip():
            raise ValueError(
                f"{fieldname} cannot have leading or trailing whitespace"
            )

    @staticmethod
    def _validate_state(state: object) -> None:
        if not isinstance(state, ExecutionState):
            raise TypeError("State must be a member of ExecutionState")

        if state != ExecutionState.SUCCEEDED and state != ExecutionState.FAILED:
            raise ValueError(f"State ({state}) is not 'SUCCEEDED' or 'FAILED'")

    def _validate_batch(self) -> None:
        has_result = self.process_result is not None
        has_failure = self.infrastructure_failure is not None

        if has_result == has_failure:
            raise ValueError(
                "Exactly one of process_result or infrastructure_failure is required"
            )
        
        if has_result:
            if not isinstance(self.process_result, ProcessExecutionResult):
                raise TypeError("Process Result must be a member of ProcessExecutionResult")

            if self.process_result.outcome.task_id != self.task_id:
                raise ValueError('Task IDs do not match')
            
            if self.process_result.attempt_id != self.attempt_id:
                raise ValueError("Attempt IDs do not match")

            if self.process_result.outcome.status is OutcomeStatus.SUCCESS and self.state is not ExecutionState.SUCCEEDED:
                raise ValueError("SUCCESS outcome requires state SUCCEEDED")

            if self.process_result.outcome.status is OutcomeStatus.FAILURE and self.state is not ExecutionState.FAILED:
                raise ValueError("FAILURE outcome requires state FAILED")
        else:
            if not isinstance(self.infrastructure_failure, InfrastructureFailure):
                raise TypeError("infrastructure_failure must be an InfrastructureFailure")

            if self.state != ExecutionState.FAILED:
                raise ValueError("An infrastructure failure requires state FAILED")