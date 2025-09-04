import uuid

from typing import List

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer, Horizontal, Vertical
from textual.css.query import NoMatches
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
    selected_task_title: reactive[str] = reactive("")
    tasks: reactive[List[MainTask]] = reactive(sort_tasks(load_tasks()))

    def compose(self) -> ComposeResult:
        """

        :return:
        """
        yield Header()
        with Vertical():
            with Horizontal():
                yield MainTodoList(self.tasks, id="todo_items")
                with Vertical():
                    yield Label("Test", id="subtasks_title")
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
        """

        :param updated_subtasks:
        :return:
        """
        try:
            tl = self.query_one("#todo_subitems", SubTodoList)
            await tl.set_tasks(self.subtasks)
            print(self.subtasks)
        except NoMatches:
            pass

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
            tl = self.query_one("#todo_items", MainTodoList)
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
        self._enable_add_task()

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

    def on_main_todo_list_add_subtask(self, message: MainTodoList.AddSubtask) -> None:
        """

        :param message:
        :return:
        """
        t = self.get_task_by_id(message.task_id)
        if t is None:
            return

        self._enable_add_subtask()

        # t.subTasks = sort_subtasks(t.subTasks + [Task(title="Test subtask")])
        # self.mutate_reactive(TodoApp.tasks)
        # self.subtasks = t.subTasks

    def on_main_todo_list_focused(self) -> None:
        self._disable_add_task()
        self._disable_add_subtask()

    def on_main_todo_list_task_selected(self, message: MainTodoList.TaskSelected) -> None:
        """

        :param message:
        :return:
        """
        t = self.get_task_by_id(message.task_id)
        if t is None:
            self.selected_task_id = ""
            self.selected_task_title = ""
            return

        self.selected_task_id = t.id
        self.selected_task_title = t.title
        self.subtasks = sort_subtasks(t.subTasks)

    def on_main_todo_list_update_task_state(self, message: MainTodoList.UpdateTaskState) -> None:
        """

        :param message:
        :return:
        """
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

    def _get_add_task_input(self) -> Input:
        return self.query_one("#add_task_input", Input)

    def _enable_add_subtask(self) -> None:
        self._get_add_subtask_container().disabled = False
        self._get_add_subtask_input().focus()

    def _enable_add_task(self) -> None:
        self._get_add_task_container().disabled = False
        self._get_add_task_input().focus()


if __name__ == "__main__":
    app = TodoApp()
    app.run()
