from dataclasses import dataclass
from enum import Enum


class OutcomeStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"

@dataclass(frozen=True)
class TaskError:
    error_type: str
    message: str

    def __post_init__(self) -> None:
        self._validate_text_field('error_type', self.error_type)
        self._validate_text_field('message', self.message)

    @staticmethod
    def _validate_text_field(field_name: str, value: object) -> None:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a str")
    
        if not value.strip():
            raise ValueError(f"{field_name} cannot be blank")
    
        if value != value.strip():
            raise ValueError(
                f"{field_name} cannot have trailing or leading whitespace"
            )


@dataclass(frozen=True)
class TaskOutcome:
    task_id: str
    status: OutcomeStatus
    value: object = None
    error: TaskError | None = None

    def __post_init__(self) -> None:
        self._validate_text_field('task_id', self.task_id)
        self._validate_status(self.status)
        self._validate_outcome_combination(self.status, self.value, self.error)


    @staticmethod
    def _validate_text_field(field_name: str, value: object) -> None:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a str")

        if not value.strip():
            raise ValueError(f"{field_name} cannot be blank")

        if value != value.strip():
            raise ValueError(
                f"{field_name} cannot have trailing or leading whitespace"
            )

    @staticmethod
    def _validate_status(value: OutcomeStatus) -> None:
        if not isinstance(value, OutcomeStatus):
            raise TypeError("Must be an instance of OutcomeStatus")

    @staticmethod
    def _validate_outcome_combination(status: OutcomeStatus, value: object, error: object) -> None:
        if status == OutcomeStatus.SUCCESS:
            if error is not None:
                raise ValueError("Must be no error, Check TaskError")

        elif status == OutcomeStatus.FAILURE:
            if error is None:
                raise ValueError("failed outcome requires an error")

            if not isinstance(error, TaskError):
                raise TypeError("error must be a TaskError")

            if value is not None:
                raise ValueError("failed outcome cannot contain a returned value")
