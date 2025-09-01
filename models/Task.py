import uuid
from dataclasses import dataclass, field
from models.enums import TaskState

@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    state: TaskState = TaskState.NEW

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
