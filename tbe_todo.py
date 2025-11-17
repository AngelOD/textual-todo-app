from typing import List

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Label

from tbe_todo_utils import load_tasks, save_tasks, sort_subtasks, sort_tasks
from models import MainTask, Task
from components import AddSubtaskScreen, AddTaskScreen, DeleteScreen, MainTodoList, SubTasksScreen, SubTodoList
from services import db


class TodoApp(App):
    CSS_PATH = "tbe_todo.tcss"
    BINDINGS = [
        ("a", "add_task", "Add Task"),
        ("s", "add_subtask", "Add Subtask"),
        ("e", "edit_task", "Edit (Sub)Task"),
        ("delete", "delete_task", "Delete Task"),
        ("t", "test", "Test"),
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
        yield Footer()

    async def watch_subtasks(self) -> None:
        await self._get_subtasks_list().set_tasks(self.subtasks)

    def watch_selected_task_title(self) -> None:
        self._get_subtasks_title().update(content=self.selected_task_title, layout=False)

    async def watch_tasks(self, updated_tasks: List[MainTask]) -> None:
        await self._get_tasks_list().set_tasks(self.tasks)
        save_tasks(updated_tasks)

    def action_test(self) -> None:
        self.push_screen(SubTasksScreen())
        print(db.load_tasks())

    def action_add_task(self):
        def handle_add_task(task: MainTask|None) -> None:
            if task is None:
                return

            self.tasks = sort_tasks(self.tasks + [task])
            self.mutate_reactive(TodoApp.tasks)

        self.push_screen(AddTaskScreen(), handle_add_task)

    def action_add_subtask(self):
        t = self._get_task_by_id(self.selected_task_id)
        if t is None:
            self.notify("No task selected", severity="error", title="Unable to add subtask")
            return

        # self._enable_add_subtask()
        def handle_add_subtask(task: Task|None) -> None:
            if task is None:
                return

            t.subTasks = sort_subtasks(t.subTasks + [Task(title=task.title)])
            self.mutate_reactive(TodoApp.tasks)
            self.subtasks = t.subTasks

        self.push_screen(AddSubtaskScreen(), handle_add_subtask)

    def action_delete_task(self):
        t = self._get_task_by_id(self.selected_task_id)
        if t is None:
            self.notify("No task selected", severity="error", title="Unable to edit task")
            return

        def check_delete(confirmed: bool|None) -> None:
            if confirmed:
                t = self._get_task_by_id(self.selected_task_id)
                if t is None:
                    return

                self.tasks.remove(t)
                self.mutate_reactive(TodoApp.tasks)

        self.push_screen(DeleteScreen(), check_delete)

    def action_edit_task(self):
        t = self._get_task_by_id(self.selected_task_id)
        if t is None:
            self.notify("No task selected", severity="error", title="Unable to edit task")
            return

        if self._get_subtasks_list().has_focus:
            subtask = self._get_subtask_by_id(self.selected_subtask_id)

            def handle_edit_subtask(task: Task|None) -> None:
                if task is None:
                    return

                subtask.title = task.title
                self.mutate_reactive(TodoApp.subtasks)
                self.mutate_reactive(TodoApp.tasks)

            self.push_screen(AddSubtaskScreen(subtask), handle_edit_subtask)
            return

        def handle_edit_task(task: MainTask|None) -> None:
            if task is None:
                return

            t.title = task.title
            t.importance = task.importance
            self.mutate_reactive(TodoApp.tasks)

        self.push_screen(AddTaskScreen(t), handle_edit_task)

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

                task = self._get_task_by_id(self.selected_task_id)
                if task is None:
                    return

                task.subTasks.remove(subtask)
                self.mutate_reactive(TodoApp.tasks)
                self.subtasks = task.subTasks
                self.mutate_reactive(TodoApp.subtasks)

        self.push_screen(DeleteScreen(), check_delete)

    def on_sub_todo_list_task_selected(self, message: SubTodoList.TaskSelected) -> None:
        self.selected_subtask_id = message.task_id

    def on_sub_todo_list_update_task_state(self, message: SubTodoList.UpdateTaskState) -> None:
        t = self._get_subtask_by_id(message.task_id)
        if t is None:
            return

        t.state = message.task_state
        self.mutate_reactive(TodoApp.subtasks)
        self.mutate_reactive(TodoApp.tasks)

    # ----- Internal helpers -----

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


if __name__ == "__main__":
    app = TodoApp()
    app.run()
