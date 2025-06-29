import json
import pathlib
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Dict, List

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer, Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static, Input, Select, Button, Label

TODO_FILE = "todo_list.json"


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
        retval = super().to_dict()
        return {
            **retval,
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


class TodoItem(Static, can_focus=True):
    """Displays a single ToDo item"""

    BINDINGS = [
        ("s", "add_subtask", "Add Subtask"),
        ("c", "complete_task", "Mark Completed"),
        ("n", "renew_task", "Mark New"),
        ("-", "regress_task", "Prev State"),
        ("+", "progress_task", "Next State")
    ]

    local_task: reactive[MainTask] = reactive(None)

    def __init__(self, task: MainTask):
        super().__init__()
        self.local_task = task
        self.id = uuid_to_id(task.id if isinstance(task, MainTask) else uuid.uuid4())

    def on_mount(self):
        if self.local_task is None:
            self.update(f"[reverse]Empty task[/]")
            return

        marker = "\\[ ]"
        wrapper = "[italic]"
        wrapper_end = "[/]"
        match self.local_task.state:
            case TaskState.STARTED:
                marker = "\\[-]"
                wrapper = ""
                wrapper_end = ""
            case TaskState.FINALISING:
                marker = "\\[+]"
                wrapper = "[underline]"
            case TaskState.COMPLETED:
                marker = "\\[X]"
                wrapper = "[strike][dim]"
                wrapper_end = "[/][/]"

        self.update(f"{marker} {wrapper}{self.local_task.title}{wrapper_end} -- \\[{self.local_task.importance.value}]")

    def on_focus(self, from_app_focus: bool):
        self.post_message(TodoItem.TaskSelected(task_id=self.local_task.id))

    def action_add_subtask(self) -> None:
        self.post_message(TodoItem.AddSubtask(task_id=self.local_task.id))

    def action_complete_task(self) -> None:
        self.post_message(TodoItem.UpdateTaskState(task_id=self.local_task.id, task_state=TaskState.COMPLETED))

    def action_progress_task(self) -> None:
        new_state = self.local_task.state
        match new_state:
            case TaskState.NEW:
                new_state = TaskState.STARTED
            case TaskState.STARTED:
                new_state = TaskState.FINALISING
            case TaskState.FINALISING:
                new_state = TaskState.COMPLETED

        if new_state != self.local_task.state:
            self.post_message(TodoItem.UpdateTaskState(task_id=self.local_task.id, task_state=new_state))

    def action_regress_task(self) -> None:
        new_state = self.local_task.state
        match new_state:
            case TaskState.COMPLETED:
                new_state = TaskState.FINALISING
            case TaskState.FINALISING:
                new_state = TaskState.STARTED
            case TaskState.STARTED:
                new_state = TaskState.NEW

        if new_state != self.local_task.state:
            self.post_message(TodoItem.UpdateTaskState(task_id=self.local_task.id, task_state=new_state))

    def action_renew_task(self) -> None:
        self.post_message(TodoItem.UpdateTaskState(task_id=self.local_task.id, task_state=TaskState.NEW))

    def update_task(self, new_task: MainTask):
        self.local_task = new_task
        self.mutate_reactive(TodoItem.local_task)

    class AddSubtask(Message):
        """Message requesting adding a subtask"""

        def __init__(self, task_id: str) -> None:
            super().__init__()
            self.task_id = task_id

    class TaskSelected(Message):
        """Message notifying the system that a specific task has been selected"""

        def __init__(self, task_id: str) -> None:
            super().__init__()
            self.task_id = task_id

    class UpdateTaskState(Message):
        """Message sending task update"""

        def __init__(self, task_id: str, task_state: TaskState) -> None:
            super().__init__()
            self.task_id = task_id
            self.task_state = task_state


class TodoApp(App):
    CSS_PATH = 'tbe_todo.tcss'
    BINDINGS = [
        ("a", "add_task", "Add Task"),
        ("q", "quit", "Quit")
    ]

    subtasks: reactive[List[Task]] = reactive([])
    selected_task_title: reactive[str] = reactive("")
    tasks: reactive[List[MainTask]] = reactive(sort_tasks(load_tasks()))
    to_reselect: str | None = None

    def compose(self) -> ComposeResult:
        """

        :return:
        """
        yield Header()
        with Vertical():
            with Horizontal():
                yield ScrollableContainer(name="todo_items", id="todo_items", can_focus=False, can_focus_children=True)
                with Vertical():
                    yield Label("Test", id="subtasks_title")
                    yield ScrollableContainer(name="todo_subitems", id="todo_subitems", can_focus=False,
                                              can_focus_children=True)
                    with Horizontal(id="add_subtask_container", disabled=True):
                        yield Input(id="add_subtask_input", placeholder="Subtask description")
                        yield Button("Add Subtask", variant="default", id="add_subtask_button")
            with Horizontal(id="add_task_container", disabled=True):
                yield Input(id="add_task_input", placeholder="Task description")
                yield Select.from_values(TaskImportance, id="add_task_importance", prompt="Importance",
                                         value=TaskImportance.MEDIUM, allow_blank=False)
                yield Button("Add Task", variant="primary", id="add_task_button")
        yield Footer()

    async def watch_subtasks(self, updated_subtasks: List[Task]) -> None:
        """

        :param updated_subtasks:
        :return:
        """
        await self.render_subtasks()

    def watch_selected_task_title(self, updated_title: str) -> None:
        """

        :param updated_title:
        :return:
        """
        title = self.query_one("#subtasks_title", Label)
        title.update(updated_title)

    async def watch_tasks(self, updated_tasks: List[MainTask]) -> None:
        """

        :param updated_tasks:
        :return:
        """
        await self.render_tasks()
        save_tasks(updated_tasks)

    async def render_subtasks(self) -> None:
        """

        :return:
        """
        subtasks_container = self.query_one("#todo_subitems", ScrollableContainer)
        await subtasks_container.remove_children()

        await subtasks_container.mount_all([Label(st.title) for st in self.subtasks])

    async def render_tasks(self) -> None:
        """

        :return:
        """
        tasks_container = self.query_one("#todo_items", ScrollableContainer)
        await tasks_container.remove_children()

        await tasks_container.mount_all([TodoItem(t) for t in self.tasks])

        if self.to_reselect is not None:
            task = self.query_one(f"#{self.to_reselect}", TodoItem)
            task.focus()
            self.to_reselect = None

    def get_task_by_id(self, task_id: str) -> MainTask | None:
        """Search for a MainTask by id and return it if found"""
        for task in self.tasks:
            if task.id == task_id:
                return task

        return None

    def action_add_task(self):
        """Handler for "add task" keypress"""
        add_container = self.query_one("#add_task_container", Horizontal)
        task_input = self.query_one("#add_task_input", Input)

        add_container.disabled = False
        task_input.focus()

    def action_quit(self) -> None:
        """Handler for "quit" keypress"""
        self.app.exit()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "add_task_button":
            add_container = self.query_one("#add_task_container", Horizontal)
            title_input = self.query_one("#add_task_input", Input)
            importance_select = self.query_one("#add_task_importance", Select)

            if title_input.value.strip() == "":
                self.notify("Missing task description", severity="warning", title="Incomplete input")
                return

            self.tasks = sort_tasks(self.tasks + [
                MainTask(title=title_input.value.strip(), importance=TaskImportance(importance_select.selection))])
            add_container.disabled = True

    def on_todo_item_add_subtask(self, message: TodoItem.AddSubtask) -> None:
        """

        :param message:
        :return:
        """
        t = self.get_task_by_id(message.task_id)
        if t is None:
            return

        add_container = self.query_one("#add_subtask_container", Horizontal)
        subtask_input = self.query_one("#add_subtask_input", Input)

        t.subTasks = sort_subtasks(t.subTasks + [Task(title="Test subtask")])
        self.to_reselect = uuid_to_id(t.id)
        self.mutate_reactive(TodoApp.tasks)

    def on_todo_item_task_selected(self, message: TodoItem.TaskSelected) -> None:
        """

        :param message:
        :return:
        """
        t = self.get_task_by_id(message.task_id)
        if t is None:
            return

        self.selected_task_title = t.title
        self.subtasks = sort_subtasks(t.subTasks)

    def on_todo_item_update_task_state(self, message: TodoItem.UpdateTaskState) -> None:
        """

        :param message:
        :return:
        """
        t = self.get_task_by_id(message.task_id)
        if t is None:
            return

        t.state = message.task_state
        self.to_reselect = uuid_to_id(t.id)
        sorted_tasks = sort_tasks(self.tasks)
        if sorted_tasks == self.tasks:
            self.mutate_reactive(TodoApp.tasks)
        else:
            self.tasks = sorted_tasks


if __name__ == "__main__":
    app = TodoApp()
    app.run()
