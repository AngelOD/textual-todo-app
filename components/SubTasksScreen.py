from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label

from .SubTodoList import SubTodoList

class SubTasksScreen(Screen):
    """Screen with the list of subtasks."""

    BINDINGS = [
        ("escape", "escape", "Close"),
        ("t", "test", "Test"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("Testing", id="subtasks_title")
            yield SubTodoList([], id="todo_subitems")
        yield Footer()

    def action_test(self) -> None:
        """Action to test something."""
        pass

    def action_escape(self) -> None:
        """Close the screen."""
        self.app.pop_screen()