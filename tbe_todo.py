import uuid

from typing import List

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Select, Button, Label

from tbe_todo_utils import load_tasks, save_tasks, sort_subtasks, sort_tasks
from models import MainTask, Task
from models.enums import TaskImportance
from components import MainTodoList, SubTodoList


class TodoApp(App):
    CSS_PATH = 'tbe_todo.tcss'
    BINDINGS = [
        ("a", "add_task", "Add Task"),
        ("q", "quit", "Quit")
    ]

    subtasks: reactive[List[Task]] = reactive([])
    selected_task_id: reactive[str] = reactive("")
    selected_task_title: reactive[str] = reactive("[No task selected]")
    tasks: reactive[List[MainTask]] = reactive(sort_tasks(load_tasks()))

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Horizontal():
                yield MainTodoList(self.tasks, id="todo_items")
                with Vertical():
                    yield Label("Testing", id="subtasks_title")
                    yield SubTodoList(self.subtasks, id="todo_subitems")
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
        await self._get_subtasks_list().set_tasks(self.subtasks)

    def watch_selected_task_title(self) -> None:
        self._get_subtasks_title().update(content=self.selected_task_title, layout=False)

    async def watch_tasks(self, updated_tasks: List[MainTask]) -> None:
        await self._get_tasks_list().set_tasks(self.tasks)
        save_tasks(updated_tasks)

    def get_task_by_id(self, task_id: str) -> MainTask | None:
        for task in self.tasks:
            if task.id == task_id:
                return task

        return None

    def action_add_task(self):
        self._enable_add_task()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "add_task_button":
            title_input = self._get_add_task_input()
            importance_select = self._get_add_task_importance()

            if title_input.value.strip() == "":
                self.notify("Missing task description", severity="warning", title="Incomplete input")
                return

            self.tasks = sort_tasks(self.tasks + [
                MainTask(title=title_input.value.strip(), importance=TaskImportance(importance_select.selection))])
            self._disable_add_task()
        elif event.button.id == "add_subtask_button":
            t = self.get_task_by_id(self.selected_task_id)
            if t is None:
                self.notify("No task selected", severity="error", title="Unable to add subtask")
                return

            title_input = self._get_add_subtask_input()

            if title_input.value.strip() == "":
                self.notify("Missing subtask description", severity="warning", title="Incomplete input")
                return

            t.subTasks = sort_subtasks(t.subTasks + [Task(title=title_input.value.strip())])
            self.mutate_reactive(TodoApp.tasks)
            self.subtasks = t.subTasks
            self._disable_add_subtask()

    def on_main_todo_list_add_subtask(self, message: MainTodoList.AddSubtask) -> None:
        t = self.get_task_by_id(message.task_id)
        if t is None:
            return

        self._enable_add_subtask()

    def on_main_todo_list_focused(self) -> None:
        self._disable_add_task()
        self._disable_add_subtask()

    def on_main_todo_list_open_subtasks(self) -> None:
        self._get_subtasks_list().focus()

    def on_main_todo_list_task_selected(self, message: MainTodoList.TaskSelected) -> None:
        t = self.get_task_by_id(message.task_id)
        if t is None:
            self.selected_task_id = ""
            self.selected_task_title = ""
            return

        self.selected_task_id = t.id
        self.selected_task_title = t.title
        self.subtasks = sort_subtasks(t.subTasks)

    def on_main_todo_list_update_task_state(self, message: MainTodoList.UpdateTaskState) -> None:
        t = self.get_task_by_id(message.task_id)
        if t is None:
            return

        t.state = message.task_state
        sorted_tasks = sort_tasks(self.tasks)
        if sorted_tasks == self.tasks:
            self.mutate_reactive(TodoApp.tasks)
        else:
            self.tasks = sorted_tasks


    # ----- Internal helpers -----

    def _disable_add_subtask(self) -> None:
        self._get_add_subtask_container().disabled = True
        self._get_add_subtask_input().clear()

    def _disable_add_task(self) -> None:
        self._get_add_task_container().disabled = True
        self._get_add_task_input().clear()

    def _get_add_subtask_container(self) -> Horizontal:
        return self.query_one("#add_subtask_container", Horizontal)

    def _get_add_subtask_input(self) -> Input:
        return self.query_one("#add_subtask_input", Input)

    def _get_add_task_container(self) -> Horizontal:
        return self.query_one("#add_task_container", Horizontal)

    def _get_add_task_importance(self) -> Select:
        return self.query_one("#add_task_importance", Select)

    def _get_add_task_input(self) -> Input:
        return self.query_one("#add_task_input", Input)

    def _get_subtasks_list(self) -> SubTodoList:
        return self.query_one("#todo_subitems", SubTodoList)

    def _get_subtasks_title(self) -> Label:
        return self.query_one("#subtasks_title", Label)

    def _get_tasks_list(self) -> MainTodoList:
        return self.query_one("#todo_items", MainTodoList)

    def _enable_add_subtask(self) -> None:
        self._get_add_subtask_container().disabled = False
        self._get_add_subtask_input().focus()

    def _enable_add_task(self) -> None:
        self._get_add_task_container().disabled = False
        self._get_add_task_input().focus()


if __name__ == "__main__":
    app = TodoApp()
    app.run()
