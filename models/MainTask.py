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

    def __lt__(self, other):
        print('MainTask.__lt__')

        if not isinstance(other, MainTask):
            if isinstance(other, Task):
                return super().__lt__(other)
            return False

        if self.is_completed() != other.is_completed():
            return other.is_completed()

        if self.importance != other.importance:
            importance_order = list(TaskImportance)
            return importance_order.index(self.importance) < importance_order.index(other.importance)

        return self.title < other.title
