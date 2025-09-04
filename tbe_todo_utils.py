import json
import pathlib

from typing import List

from models import MainTask, Task
from models.enums import TaskImportance, TaskState


TODO_FILE = "todo_list.json"


def format_task_title(task: Task):
    marker = "\\[ ]"
    wrapper = "[italic]"
    wrapper_end = "[/]"

    match task.state:
        case TaskState.STARTED:
            marker = "\\[-]"
            wrapper = ""
            wrapper_end = ""
        case TaskState.FINALISING:
            marker = "\\[+]"
            wrapper = "[underline]"
            wrapper_end = "[/]"
        case TaskState.COMPLETED:
            marker = "\\[x]"
            wrapper = "[strike][dim]"
            wrapper_end = "[/][/]"

    suffix = f" ({task.importance.value[0].upper()})" if isinstance(task, MainTask) else ""

    return f"{marker} {wrapper}{task.title}{wrapper_end}{suffix}"


def load_tasks() -> List[MainTask]:
    """
    Loads tasks from JSON file
    :return:
    """
    path = pathlib.Path(TODO_FILE)

    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

            if not isinstance(data, list):
                print(f"Warning: {TODO_FILE} is not a valid todo file. Starting with an empty list.")
                return []
            return [MainTask.from_dict(t) for t in data]
    except (json.JSONDecodeError, FileNotFoundError, TypeError) as err:
        print(f"Error: {err}. Starting with an empty list.")
        return []


def save_tasks(tasks: List[MainTask]) -> None:
    """Saves tasks to JSON file"""
    path = pathlib.Path(TODO_FILE)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([t.to_dict() for t in tasks], f, indent=2)


def sort_subtasks(tasks: List[Task]) -> List[Task]:
    return sorted(tasks)


def sort_tasks(tasks: List[MainTask]) -> List[MainTask]:
    return sorted(tasks)


def uuid_to_id(uuid_to_convert: str) -> str:
    return f"id_{uuid_to_convert}".replace("-", "_")

def id_to_uuid(id_to_convert: str) -> str:
    return id_to_convert.replace("id_", "").replace("_", "-")
