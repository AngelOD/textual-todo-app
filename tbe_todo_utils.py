import json
import pathlib

from typing import List

from tbe_todo_types import MainTask, Task, TaskImportance, TaskState


TODO_FILE = "todo_list.json"


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
    return [t for t in tasks if t.state != TaskState.COMPLETED] + \
        [t for t in tasks if t.state == TaskState.COMPLETED]


def sort_tasks(tasks: List[MainTask]) -> List[MainTask]:
    desired_order = list(TaskImportance)
    new_tasks = []

    unfinished_tasks = [t for t in tasks if t.state != TaskState.COMPLETED]
    finished_tasks = [t for t in tasks if t.state == TaskState.COMPLETED]

    for importance in desired_order:
        new_tasks += [t for t in unfinished_tasks if t.importance == importance]

    return new_tasks + finished_tasks


def uuid_to_id(uuid_to_convert: str) -> str:
    return f"id_{uuid_to_convert}".replace("-", "_")
