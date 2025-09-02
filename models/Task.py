import uuid
from dataclasses import dataclass, field
from models.enums import TaskState

@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    state: TaskState = TaskState.NEW

    def is_completed(self) -> bool:
        return self.state == TaskState.COMPLETED

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "state": self.state.value,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            title=data["title"],
            state=TaskState(data["state"]),
        )

    def __eq__(self, other):
        if not isinstance(other, Task):
            return False

        return self.id == other.id

    def __lt__(self, other):
        if not isinstance(other, Task):
            return False

        if self.is_completed() != other.is_completed():
            return other.is_completed()

        return self.title < other.title
