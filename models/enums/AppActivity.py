from enum import auto, Enum

class AppActivity(Enum):
    FOCUS_TASKS = auto()
    FOCUS_SUBTASKS = auto()
    ADD_TASK = auto()
    ADD_SUBTASK = auto()
