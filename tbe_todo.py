import uuid

from typing import List

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer, Horizontal, Vertical
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static, Input, Select, Button, Label

from tbe_todo_types import AppActivity, MainTask, Task, TaskImportance, TaskState
from tbe_todo_utils import load_tasks, save_tasks, sort_subtasks, sort_tasks, uuid_to_id
from components.NewTodoList import NewTodoList


class TodoItem(Static, can_focus=True):
    """Displays a single Todo item"""

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
        ("escape", "focus_tasks", "Go to tasks"),
        ("enter", "focus_subtasks", "Go to subtasks"),
        ("q", "quit", "Quit")
    ]

    current_activity: reactive[AppActivity] = reactive(None)
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
                yield NewTodoList(self.tasks, id="todo_items")
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

    async def watch_subtasks(self) -> None:
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
        try:
            tl = self.query_one("#todo_items", NewTodoList)
            await tl.set_tasks(self.tasks)
        except NoMatches:
            pass

        save_tasks(updated_tasks)

    async def render_subtasks(self) -> None:
        """

        :return:
        """
        subtasks_container = self.query_one("#todo_subitems", ScrollableContainer)
        await subtasks_container.remove_children()

        await subtasks_container.mount_all([Label(st.title) for st in self.subtasks])

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

    def action_focus_subtasks(self):
        """ """
        self.current_activity = AppActivity.FOCUS_SUBTASKS

    def action_focus_tasks(self):
        """ """
        self.current_activity = AppActivity.FOCUS_TASKS

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

    def on_mount(self):
        self.current_activity = AppActivity.FOCUS_TASKS

    def on_new_todo_list_add_subtask(self, message: NewTodoList.AddSubtask) -> None:
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

    def on_new_todo_list_task_selected(self, message: NewTodoList.TaskSelected) -> None:
        """

        :param message:
        :return:
        """
        print(f"Selected task: {message.task_id}")
        t = self.get_task_by_id(message.task_id)
        if t is None:
            return

        self.selected_task_title = t.title
        self.subtasks = sort_subtasks(t.subTasks)

    def on_new_todo_list_update_task_state(self, message: NewTodoList.UpdateTaskState) -> None:
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
