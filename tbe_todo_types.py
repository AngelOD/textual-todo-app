import uuid
from dataclasses import dataclass, field
from enum import auto, Enum, StrEnum
from typing import List


class AppActivity(Enum):
    FOCUS_TASKS = auto()
    FOCUS_SUBTASKS = auto()
    ADD_TASK = auto()
    ADD_SUBTASK = auto()


class TaskImportance(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


class TaskState(StrEnum):
    NEW = "new"
    STARTED = "started"
    FINALISING = "finalising"
    COMPLETED = "completed"

    def next(self):
        cls = self.__class__
        members = list(cls)
        index = members.index(self) + 1
        if index >= len(members):
            index = len(members) - 1
        return members[index]


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


@dataclass
class MainTask(Task):
    importance: TaskImportance = TaskImportance.MEDIUM
    subTasks: List[Task] = field(default_factory=list)

    def to_dict(self):
        return {
            **super().to_dict(),
            "importance": self.importance.value,
            "subTasks": [item.to_dict() for item in self.subTasks]
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            title=data["title"],
            state=TaskState(data["state"]),
            importance=TaskImportance(data["importance"]),
            subTasks=[Task.from_dict(t) for t in data["subTasks"]]
        )
