from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Select
from models import MainTask
from models.enums import TaskImportance

class AddTaskScreen(ModalScreen[MainTask|None]):

    def __init__(self, task: MainTask|None = None, **kwargs):
        super().__init__(**kwargs)
        self._edit_task = task

    def compose(self) -> ComposeResult:
        yield Grid(
            Input(id="add_task_input", placeholder="Task description"),
            Select.from_values(TaskImportance, id="add_task_importance", prompt="Importance", value=TaskImportance.MEDIUM, allow_blank=False),
            Button("Add Task", variant="primary", id="add_task_button"),
            Button("Cancel", variant="error", id="cancel_add_task_button"),
            id="add_task_dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_add_task_button":
            self.dismiss(None)
            return

        # TODO Add validation
        # TODO Add task
