from typing import List, Optional

from textual.message import Message
from textual.widgets import ListView, ListItem, Label

from models import MainTask
from models.enums import TaskState
from tbe_todo_utils import id_to_uuid, uuid_to_id, format_task_title


class MainTodoList(ListView):
    """
    A ListView-based widget for MainTask entries
    """

    BINDINGS = [
        ("c", "complete_task", "Mark Completed"),
        ("n", "renew_task", "Mark New"),
        ("-", "regress_task", "Prev State"),
        ("+", "progress_task", "Next State")
    ]

    def __init__(self, tasks: Optional[List[MainTask]] = None, **kwargs):
        super().__init__(**kwargs)
        self._tasks: List[MainTask] = []
        self._tasks_waiting = tasks or []

    async def on_mount(self):
        await self.set_tasks(self._tasks_waiting)
        self._tasks_waiting = []

    def on_focus(self):
        self.post_message(MainTodoList.Focused())

    def on_list_view_highlighted(self) -> None:
        selected_task = self.get_selected_task()
        if selected_task is None:
            self.post_message(MainTodoList.TaskSelected(task_id=""))

        self.post_message(MainTodoList.TaskSelected(task_id=id_to_uuid(selected_task.id)))

    def action_add_subtask(self) -> None:
        selected_task = self.get_selected_task()

        if selected_task is None:
            return

        self.post_message(MainTodoList.AddSubtask(task_id=id_to_uuid(selected_task.id)))

    def action_complete_task(self) -> None:
        self._update_task_state(TaskState.COMPLETED)

    def action_edit_task(self) -> None:
        selected_task = self.get_selected_task()

        if selected_task is None:
            return

        self.post_message(MainTodoList.EditTask(task_id=id_to_uuid(selected_task.id)))

    def action_progress_task(self) -> None:
        selected_task = self.get_selected_task()
        if selected_task is None:
            return

        self._update_task_state(selected_task.state.next())

    def action_regress_task(self) -> None:
        selected_task = self.get_selected_task()
        if selected_task is None:
            return

        self._update_task_state(selected_task.state.prev())

    def action_renew_task(self) -> None:
        self._update_task_state(TaskState.NEW)

    # ----- Public API -----

    async def set_tasks(self, tasks: List[MainTask]) -> None:
        """Replace the entire list of tasks and refresh the view, preserving selection."""
        self._tasks = list(tasks)
        await self._refresh_items_preserving_selection()

    async def add_task(self, task: MainTask) -> None:
        """Add a task and refresh the view with sorting and selection preservation."""
        self._tasks.append(task)
        await self._refresh_items_preserving_selection()

    async def update_task(self, updated_task: MainTask) -> None:
        """Upsert a task (matched by id) and refresh the view with sorting and selection preservation."""
        for idx, t in enumerate(self._tasks):
            if t.id == updated_task.id:
                self._tasks[idx] = updated_task
                break
        else:
            self._tasks.append(updated_task)

        await self._refresh_items_preserving_selection()

    async def remove_task_by_id(self, task_id: str) -> None:
        """Remove a task by UUID string and refresh the view, preserving selection when possible."""
        self._tasks = [t for t in self._tasks if t.id != task_id]
        await self._refresh_items_preserving_selection()

    def get_selected_task(self) -> Optional[MainTask]:
        """Return the currently selected task, or None if no task is selected."""
        selected_item_id = self._get_current_highlighted_id()
        if selected_item_id is None:
            return None

        selected_item_id = id_to_uuid(selected_item_id)
        for task in self._tasks:
            if task.id == selected_item_id:
                return task

        return None


    # ----- Textual Message Classes -----

    class AddSubtask(Message):
        """Message requesting adding a subtask"""

        def __init__(self, task_id: str) -> None:
            super().__init__()
            self.task_id = task_id

    class EditTask(Message):
        """Message requesting editing a task"""

        def __init__(self, task_id: str) -> None:
            super().__init__()
            self.task_id = task_id

    class Focused(Message):
        """Message indicating that the widget was focused"""

        def __init__(self) -> None:
            super().__init__()

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


    # ----- Internal helpers -----

    def _make_item(self, task: MainTask) -> ListItem:
        item_id = uuid_to_id(task.id)
        text = format_task_title(task)
        return ListItem(Label(text), id=item_id)

    def _get_current_highlighted_id(self) -> Optional[str]:
        # Try to capture the currently highlighted item's id (if available)
        try:
            current_index = self.index  # ListView's highlighted index
        except Exception:
            current_index = None

        if current_index is None:
            return None

        items = list(self.children)
        if not items or current_index < 0 or current_index >= len(items):
            return None

        current_item = items[current_index]
        return getattr(current_item, "id", None)

    def _set_highlight_by_id(self, target_id: str) -> None:
        # Find the new index for the id and set it as the highlighted index
        items = list(self.children)
        ids = [getattr(it, "id", None) for it in items]
        if target_id in ids:
            new_index = ids.index(target_id)
            try:
                self.index = new_index  # Programmatically set the highlight
            except Exception:
                # If direct assignment isn't supported in your Textual version, we leave as-is.
                pass

    async def _refresh_items_preserving_selection(self) -> None:
        # Save the currently highlighted item's id
        highlighted_id = self._get_current_highlighted_id()

        # Sort tasks by importance and build new items
        sorted_tasks = sorted(self._tasks)
        desired_ids = [uuid_to_id(t.id) for t in sorted_tasks]

        # If the structure already matches, do an in-place label update; else rebuild
        existing_items = list(self.children)
        existing_ids = [getattr(it, "id", None) for it in existing_items]

        rebuild = existing_ids != desired_ids or len(existing_items) != len(desired_ids)

        if rebuild:
            # Rebuild entirely
            for child in list(self.children):
                await child.remove()

            # Append in sorted order
            for task in sorted_tasks:
                await self.append(self._make_item(task))
        else:
            # Same structure; only update labels if the text changed
            id_to_task = {uuid_to_id(t.id): t for t in sorted_tasks}
            for it in existing_items:
                item_id = getattr(it, "id", None)
                if item_id is None:
                    continue
                task = id_to_task.get(item_id)
                if task is None:
                    continue
                desired_text = format_task_title(task)

                # ListItem(Label(...)) -> its first child should be our Label
                if it.children:
                    label = it.children[0]
                    # Label has update(str) to change content
                    try:
                        # Only update if content differs to avoid unnecessary renders
                        if getattr(label, "renderable", None) != desired_text:
                            label.update(desired_text)
                    except Exception:
                        # Fallback: try direct update
                        label.update(desired_text)

        # Restore highlight if possible; if nothing was highlighted or it no longer exists, leave as-is.
        if highlighted_id:
            self._set_highlight_by_id(highlighted_id)
        else:
            # If nothing is highlighted and we have items, ensure we highlight the first one
            items = list(self.children)
            if items:
                try:
                    self.index = 0
                    self.mutate_reactive(MainTodoList.index)
                except Exception:
                    pass

    def _update_task_state(self, task_state: TaskState) -> None:
        selected_task = self.get_selected_task()

        if selected_task is None:
            return

        self.post_message(
            MainTodoList.UpdateTaskState(task_id=id_to_uuid(selected_task.id), task_state=task_state))