from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label

class DeleteScreen(ModalScreen[bool]):
    """Screen asking to confirm deletion."""

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Are you sure you want to delete?", id="question"),
            Button("Yes, delete", variant="error", id="delete_button"),
            Button("No", variant="primary", id="cancel_button"),
            id="delete_screen",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "delete_button":
            self.dismiss(True)
        else:
            self.dismiss(False)