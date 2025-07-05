from typing import List

from textual.app import ComposeResult
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import OptionList
from textual.widgets.option_list import Option, OptionDoesNotExist

from tbe_todo_types import MainTask, TaskImportance, TaskState
from tbe_todo_utils import uuid_to_id, format_task_title, save_tasks


class TodoList(Widget):
    """ """

    tasks: reactive[List[MainTask]] = reactive([])

    def __init__(self, tasks: List[MainTask], **kwargs):
        super().__init__(**kwargs)
        self.tasks = tasks

    def compose(self) -> ComposeResult:
        yield OptionList(id="tl_tasks_list")

    def refresh_options(self):
        try:
            tl = self.query_one("#tl_tasks_list", OptionList)
        except NoMatches:
            return

        present_ids = []

        for task in self.tasks:
            option_id = uuid_to_id(task.id)
            task_text = format_task_title(task)

            try:
                opt = tl.get_option(option_id)
                present_ids.append(option_id)
                if opt.prompt != task_text:
                    tl.replace_option_prompt(option_id, task_text)
            except OptionDoesNotExist:
                present_ids.append(option_id)
                tl.add_option(Option(task_text, id=option_id))

        removable_ids = []

        for option in tl.options:
            if option.id not in present_ids:
                removable_ids.append(option.id)

        for removable_id in removable_ids:
            tl.remove_option(removable_id)

        # Check sorting
        for index, task in enumerate(self.tasks):
            option_id = uuid_to_id(task.id)
            idx = tl.get_option_index(option_id)

            if idx != index:
                opt = tl.get_option(option_id)
                tl.remove_option(option_id)
                tl

    def update_options(self, new_tasks: List[MainTask]):
        self.tasks = new_tasks
        self.mutate_reactive(TodoList.tasks)

    def on_mount(self):
        self.refresh_options()

    def watch_tasks(self):
        self.refresh_options()

