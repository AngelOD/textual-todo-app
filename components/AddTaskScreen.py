from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Select
from models import MainTask
from models.enums import TaskImportance

class AddTaskScreen(ModalScreen[MainTask|None]):
    """Screen with a dialog to add or edit a task."""

    BINDINGS = [("escape", "escape", "Close")]

    def __init__(self, task: MainTask|None = None, **kwargs):
        super().__init__(**kwargs)
        self._edit_task = task

    def compose(self) -> ComposeResult:
        yield Grid(
            Input(id="add_task_input", placeholder="Task description"),
            Select.from_values(TaskImportance, id="add_task_importance", prompt="Importance", value=TaskImportance.MEDIUM, allow_blank=False),
            Button("Save", variant="primary", id="add_task_button"),
            Button("Cancel", variant="error", id="cancel_add_task_button"),
            id="add_task_screen",
        )

    def on_mount(self):
        input_widget = self.query_one("#add_task_input", Input)
        importance_select = self.query_one("#add_task_importance", Select)
        save_button = self.query_one("#add_task_button", Button)

        if self._edit_task is not None:
            input_widget.value = self._edit_task.title
            importance_select.value = self._edit_task.importance
            save_button.label = "Update Task"
        else:
            save_button.label = "Add Task"

        input_widget.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()

        if event.button.id == "cancel_add_task_button":
            self.dismiss(None)
            return

        input_widget = self.query_one("#add_task_input", Input)
        importance_select = self.query_one("#add_task_importance", Select)

        if input_widget.value.strip() == "":
            self.notify("Missing task description", severity="warning", title="Incomplete input")
            return

        self.dismiss(MainTask(title=input_widget.value.strip(), importance=TaskImportance(importance_select.selection)))

    def action_escape(self):
        self.dismiss(None)
