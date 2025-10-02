from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Input
from models import Task

class AddSubtaskScreen(ModalScreen[Task | None]):
    """Screen with a dialog to add a subtask to a task or edit an existing one."""

    BINDINGS = [("escape", "escape", "Close")]

    def __init__(self, subtask: Task|None = None, **kwargs):
        super().__init__(**kwargs)
        self._edit_task = subtask

    def compose(self) -> ComposeResult:
        yield Grid(
            Input(id="add_subtask_input", placeholder="Subtask description"),
            Button("Add Subtask", variant="primary", id="add_subtask_button"),
            Button("Cancel", variant="error", id="cancel_add_subtask_button"),
            id="add_subtask_screen",
        )

    def on_mount(self):
        input_widget = self.query_one("#add_subtask_input", Input)
        save_button = self.query_one("#add_subtask_button", Button)

        if self._edit_task is not None:
            input_widget.value = self._edit_task.title
            save_button.label = "Update Subtask"
        else:
            save_button.label = "Add Subtask"

        input_widget.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()

        if event.button.id == "cancel_add_subtask_button":
            self.dismiss(None)
            return

        input_widget = self.query_one("#add_subtask_input", Input)
        if input_widget.value.strip() == "":
            self.notify("Missing subtask description", severity="warning", title="Incomplete input")
            return

        self.dismiss(Task(title=input_widget.value.strip()))

    def action_escape(self):
        self.dismiss(None)
