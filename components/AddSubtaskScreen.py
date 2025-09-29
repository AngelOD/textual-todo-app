from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Input
from models import Task

class AddSubtaskScreen(ModalScreen[Task | None]):
    """Screen with a dialog to add a subtask to a task."""

    def __init__(self, subtask: Task|None = None, **kwargs):
        super().__init__(**kwargs)
        self._edit_task = subtask

    def compose(self) -> ComposeResult:
        yield Grid(
            Input(id="add_subtask_input", placeholder="Subtask description"),
            Button("Add Subtask", variant="primary", id="add_subtask_button"),
            Button("Cancel", variant="error", id="cancel_add_subtask_button"),
            id="add_subtask_dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_add_subtask_button":
            self.dismiss(None)
