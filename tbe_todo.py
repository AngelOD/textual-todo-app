import uuid

from typing import List

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Select, Button, Label

from tbe_todo_utils import load_tasks, save_tasks, sort_subtasks, sort_tasks
from models import MainTask, Task
from models.enums import TaskImportance
from components import DeleteScreen, MainTodoList, SubTodoList


class TodoApp(App):
    CSS_PATH = 'tbe_todo.tcss'
    BINDINGS = [
        ("a", "add_task", "Add Task"),
        ("s", "add_subtask", "Add Subtask"),
        ("delete", "delete_task", "Delete Task"),
        ("q", "quit", "Quit")
    ]

    is_editing: reactive[bool] = reactive(False)
    subtasks: reactive[List[Task]] = reactive([])
    selected_subtask_id: reactive[str] = reactive("")
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

    def action_add_task(self):
        self._enable_add_task()

    def action_add_subtask(self):
        if self._get_task_by_id(self.selected_task_id) is None:
            self.notify("No task selected", severity="error", title="Unable to add subtask")
            self._disable_add_subtask()
            return

        self._enable_add_subtask()

    def action_delete_task(self):
        def check_delete(confirmed: bool|None) -> None:
            if confirmed:
                t = self._get_task_by_id(self.selected_task_id)
                if t is None:
                    return

                self.tasks.remove(t)
                self.mutate_reactive(TodoApp.tasks)

        self.push_screen(DeleteScreen(), check_delete)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "add_task_button":
            title_input = self._get_add_task_input()
            importance_select = self._get_add_task_importance()

            if title_input.value.strip() == "":
                self.notify("Missing task description", severity="warning", title="Incomplete input")
                return

            if self.is_editing:
                t = self._get_task_by_id(self.selected_task_id)
                if t is None:
                    self.notify("No task selected", severity="error", title="Unable to edit task")
                    self._disable_add_task()
                    return
                t.title = title_input.value.strip()
                t.importance = TaskImportance(importance_select.selection)
                self.mutate_reactive(TodoApp.tasks)
                self._disable_add_task()
                return

            self.tasks = sort_tasks(self.tasks + [
                MainTask(title=title_input.value.strip(), importance=TaskImportance(importance_select.selection))])
            self._disable_add_task()
        elif event.button.id == "add_subtask_button":
            t = self._get_task_by_id(self.selected_task_id)
            if t is None:
                self.notify("No task selected", severity="error", title="Unable to add subtask")
                return

            title_input = self._get_add_subtask_input()

            if title_input.value.strip() == "":
                self.notify("Missing subtask description", severity="warning", title="Incomplete input")
                return

            if self.is_editing:
                t = self._get_subtask_by_id(self.selected_subtask_id)
                if t is None:
                    self.notify("No subtask selected", severity="error", title="Unable to edit subtask")
                    self._disable_add_subtask()
                    return

                t.title = title_input.value.strip()
                self.mutate_reactive(TodoApp.subtasks)
                self.mutate_reactive(TodoApp.tasks)
                self._disable_add_subtask()
                return

            t.subTasks = sort_subtasks(t.subTasks + [Task(title=title_input.value.strip())])
            self.mutate_reactive(TodoApp.tasks)
            self.subtasks = t.subTasks
            self._disable_add_subtask()

    def on_main_todo_list_add_subtask(self, message: MainTodoList.AddSubtask) -> None:
        t = self._get_task_by_id(message.task_id)
        if t is None:
            return

        self._enable_add_subtask()

    def on_main_todo_list_edit_task(self, message: MainTodoList.EditTask) -> None:
        t = self._get_task_by_id(message.task_id)
        if t is None:
            return

        self.selected_subtask_id = t.id
        self._get_add_task_input().value = t.title
        self._get_add_task_importance().value = t.importance
        self._enable_edit_task()

    def on_main_todo_list_focused(self) -> None:
        self._disable_add_task()
        self._disable_add_subtask()

    def on_main_todo_list_task_selected(self, message: MainTodoList.TaskSelected) -> None:
        t = self._get_task_by_id(message.task_id)
        if t is None:
            self.selected_task_id = ""
            self.selected_task_title = ""
            return

        self.selected_task_id = t.id
        self.selected_task_title = t.title
        self.subtasks = sort_subtasks(t.subTasks)

    def on_main_todo_list_update_task_state(self, message: MainTodoList.UpdateTaskState) -> None:
        t = self._get_task_by_id(message.task_id)
        if t is None:
            return

        t.state = message.task_state
        sorted_tasks = sort_tasks(self.tasks)
        if sorted_tasks == self.tasks:
            self.mutate_reactive(TodoApp.tasks)
        else:
            self.tasks = sorted_tasks

    def on_sub_todo_list_delete_task(self, message: SubTodoList.DeleteTask) -> None:
        def check_delete(confirmed: bool|None) -> None:
            if confirmed:
                subtask = self._get_subtask_by_id(message.task_id)
                if subtask is None:
                    return

                self.subtasks.remove(subtask)
                self.mutate_reactive(TodoApp.subtasks)
                self.mutate_reactive(TodoApp.tasks)

        self.push_screen(DeleteScreen(), check_delete)

    def on_sub_todo_list_edit_task(self, message: SubTodoList.EditTask) -> None:
        t = self._get_subtask_by_id(message.task_id)
        if t is None:
            return

        self.selected_subtask_id = t.id
        self._get_add_subtask_input().value = t.title
        self._enable_edit_subtask()

    def on_sub_todo_list_focused(self) -> None:
        self._disable_add_task()
        self._disable_add_subtask()

    def on_sub_todo_list_update_task_state(self, message: SubTodoList.UpdateTaskState) -> None:
        t = self._get_subtask_by_id(message.task_id)
        if t is None:
            return

        t.state = message.task_state
        self.mutate_reactive(TodoApp.subtasks)
        self.mutate_reactive(TodoApp.tasks)

    # ----- Internal helpers -----

    def _disable_add_subtask(self) -> None:
        self.is_editing = False
        self._get_add_subtask_container().disabled = True
        self._get_add_subtask_input().clear()

    def _disable_add_task(self) -> None:
        self.is_editing = False
        self._get_add_task_container().disabled = True
        self._get_add_task_input().clear()

    def _get_add_subtask_button(self) -> Button:
        return self.query_one("#add_subtask_button", Button)

    def _get_add_subtask_container(self) -> Horizontal:
        return self.query_one("#add_subtask_container", Horizontal)

    def _get_add_subtask_input(self) -> Input:
        return self.query_one("#add_subtask_input", Input)

    def _get_add_task_button(self) -> Button:
        return self.query_one("#add_task_button", Button)

    def _get_add_task_container(self) -> Horizontal:
        return self.query_one("#add_task_container", Horizontal)

    def _get_add_task_importance(self) -> Select:
        return self.query_one("#add_task_importance", Select)

    def _get_add_task_input(self) -> Input:
        return self.query_one("#add_task_input", Input)

    def _get_subtask_by_id(self, task_id: str) -> Task | None:
        if self.subtasks is None or len(self.subtasks) == 0:
            return None

        for subtask in self.subtasks:
            if subtask.id == task_id:
                return subtask

        return None

    def _get_subtasks_list(self) -> SubTodoList:
        return self.query_one("#todo_subitems", SubTodoList)

    def _get_subtasks_title(self) -> Label:
        return self.query_one("#subtasks_title", Label)

    def _get_task_by_id(self, task_id: str) -> MainTask | None:
        for task in self.tasks:
            if task.id == task_id:
                return task

        return None

    def _get_tasks_list(self) -> MainTodoList:
        return self.query_one("#todo_items", MainTodoList)

    def _enable_add_subtask(self) -> None:
        self.is_editing = False
        self._get_add_subtask_container().disabled = False
        self._get_add_subtask_button().label = "Add Subtask"
        self._get_add_subtask_input().focus()

    def _enable_add_task(self) -> None:
        self.is_editing = False
        self._get_add_task_container().disabled = False
        self._get_add_task_button().label = "Add Task"
        self._get_add_task_input().focus()

    def _enable_edit_subtask(self) -> None:
        self.is_editing = True
        self._get_add_subtask_container().disabled = False
        self._get_add_subtask_button().label = "Save"
        self._get_add_subtask_input().focus()

    def _enable_edit_task(self) -> None:
        self.is_editing = True
        self._get_add_task_container().disabled = False
        self._get_add_task_button().label = "Save"
        self._get_add_task_input().focus()


if __name__ == "__main__":
    app = TodoApp()
    app.run()
