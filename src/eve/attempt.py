
from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionAttempt:
    attempt_id: str
    task_id: str
    attempt_number: int

    def __post_init__(self) -> None:
        self._validate_field_name('attempt_id', self.attempt_id)
        self._validate_field_name('task_id', self.task_id)
        self._validate_attempt_number(self.attempt_number)

    @staticmethod
    def _validate_field_name(field_name: str, value: object) -> None:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")

        if not value.strip():
            raise ValueError(f"{field_name} cannot be blank")

        if value != value.strip():
            raise ValueError(
                f"{field_name} cannot have trailing or leading whitespace"
            )
    @staticmethod
    def _validate_attempt_number(value: object) -> None:
        if isinstance(value, bool):
            raise TypeError(f"value cannot be a boolean")
        
        if not isinstance(value, int):
            raise TypeError(f"{value} must be an integer")

        if value < 1:
            raise ValueError(f"{value} must be at least one")


