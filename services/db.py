import sqlite3

from typing import List

from models import MainTask, Task
from tbe_todo_utils import load_tasks as load_tasks_from_json

db_name = "todo_list.db"

def init_db() -> None:
    """Initialize the SQLite database for the application."""

    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS table_versions (
                table_name TEXT PRIMARY KEY,
                version INTEGER NOT NULL
            )
        """)

        # Create or migrate tasks table
        tasks_table_version = get_table_version("tasks")
        if tasks_table_version < 1:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    state TEXT NOT NULL,
                    importance TEXT NOT NULL
                )
            """)
            set_table_version("tasks", 1)

        # Create or migrate subtasks table
        subtasks_table_version = get_table_version("subtasks")
        if subtasks_table_version < 1:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subtasks (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    state TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_subtasks_task_id ON subtasks (task_id)")
            set_table_version("subtasks", 1)

def migrate_from_json() -> None:
    """Migrate data from JSON to SQLite database."""
    json_tasks = load_tasks_from_json()

    for task in json_tasks:
        for subtask in task.subTasks:
            if subtask.task_id is None or len(subtask.task_id.strip()) == 0:
                subtask.task_id = task.id

        save_task(task)

def load_tasks(include_subtasks: bool = True) -> List[MainTask]:
    """Load tasks from the SQLite database."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id, title, state, importance FROM tasks")
        db_tasks = cursor.fetchall()

        tasks = []
        for row in db_tasks:
            main_task = MainTask(id=row[0], title=row[1], state=row[2], importance=row[3])
            main_task.subTasks = load_subtasks_for_task(main_task.id) if include_subtasks else []
            tasks.append(main_task)

        return tasks

def load_subtasks_for_task(task_id: str) -> List[Task]:
    """Load subtasks for a task from the SQLite database."""
    if task_id is None or len(task_id.strip()) == 0:
        raise ValueError("Task ID is required.")

    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id, task_id, title, state FROM subtasks WHERE task_id=?", (task_id,))
        subtasks = cursor.fetchall()

        return [Task(id=row[0], task_id=row[1], title=row[2], state=row[3]) for row in subtasks]

def save_task(task: MainTask) -> None:
    """Save tasks to the SQLite database."""
    if task.id is None:
        raise ValueError("Task ID is required.")

    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        main_task_query = "INSERT OR REPLACE INTO tasks (id, title, state, importance) VALUES (?, ?, ?, ?)"
        params = (task.id, task.title, task.state, task.importance)
        cursor.execute(main_task_query, params)

        sub_task_query = "INSERT OR REPLACE INTO subtasks (id, task_id, title, state) VALUES (?, ?, ?, ?)"
        params = [(t.id, t.task_id, t.title, t.state) for t in task.subTasks]
        cursor.executemany(sub_task_query, params)

def save_subtask(subtask: Task) -> None:
    """Save subtasks to the SQLite database."""
    if subtask.id is None:
        raise ValueError("Subtask ID is required.")

    if subtask.task_id is None or len(subtask.task_id.strip()) == 0:
        raise ValueError("Task ID is required.")

    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        cursor.execute("INSERT OR REPLACE INTO subtasks (id, task_id, title, state) VALUES (?, ?, ?, ?)",
                       (subtask.id, subtask.task_id, subtask.title, subtask.state))

def delete_task(task_id: str) -> None:
    """Delete a task from the SQLite database."""
    if task_id is None or len(task_id.strip()) == 0:
        raise ValueError("Task ID is required.")

    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        cursor.execute("DELETE FROM subtasks WHERE task_id=?", (task_id,))

def delete_subtask(subtask_id: str) -> None:
    """Delete a subtask from the SQLite database."""
    if subtask_id is None or len(subtask_id.strip()) == 0:
        raise ValueError("Subtask ID is required.")

    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        cursor.execute("DELETE FROM subtasks WHERE id=?", (subtask_id,))

def get_table_version(table_name: str) -> int:
    """Get the version of a table in the SQLite database."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT version FROM table_versions WHERE table_name=?", (table_name,))
        row = cursor.fetchone()

        return row[0] if row else 0

def set_table_version(table_name: str, version: int) -> None:
    """Set the version of a table in the SQLite database."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        cursor.execute("INSERT OR REPLACE INTO table_versions (table_name, version) VALUES (?, ?)", (table_name, version))

init_db()
migrate_from_json()