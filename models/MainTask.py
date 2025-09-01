from dataclasses import dataclass, field
from typing import List

from .Task import Task
from models.enums import TaskState, TaskImportance

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
