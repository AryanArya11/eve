from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    task_id: str
    workload: str
    payload: object

    def __post_init__(self) -> None:
        self._validate_text_field("task_id", self.task_id)
        self._validate_text_field("workload", self.workload)

    @staticmethod
    def _validate_text_field(field_name: str, value: object) -> None:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")

        if not value.strip():
            raise ValueError(f"{field_name} cannot be blank")

        if value != value.strip():
            raise ValueError(
                f"{field_name} cannot have trailing or leading whitespace"
            )