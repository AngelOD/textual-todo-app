from enum import StrEnum

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

    def prev(self):
        cls = self.__class__
        members = list(cls)
        index = members.index(self) - 1
        if index < 0:
            index = 0
        return members[index]
