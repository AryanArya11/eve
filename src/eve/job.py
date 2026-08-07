from dataclasses import dataclass
from eve.task import Task


@dataclass(frozen=True)
class Job:
    job_id: str
    tasks: tuple[Task, ...]

    def __post_init__(self) -> None:
        self._validate_text_field('job_id', self.job_id)
        self._validate_instances(self.tasks)


    @staticmethod
    def _validate_text_field(field_name: str, value: object) -> None:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be string")

        if not value.strip():
            raise ValueError(f"{field_name} cannot be blank")

        if value != value.strip():
            raise ValueError(
                f"{field_name} cannot have trailing or leading whitespace"
            )

    @staticmethod
    def _validate_instances(task: tuple[Task,...]) -> None:
        if not isinstance(task, tuple):
            raise TypeError(f"{task} must be tuple")

        if not task:
            raise ValueError(f"task cannot be empty")
        
        if not all(isinstance(x, Task) for x in task):
            raise TypeError(f"{task} must contain members/instances")

        task_ids = [t.task_id for t in task]

        if len(task_ids) != len(set(task_ids)):
            raise ValueError("task ids must be unique")
            
