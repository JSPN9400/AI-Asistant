from memory.sqlite_store import SQLiteMemory

_mem: SQLiteMemory | None = None


def _store() -> SQLiteMemory:
    global _mem
    if _mem is None:
        _mem = SQLiteMemory()
    return _mem


def create_note(content: str) -> str:
    if not content:
        return "I need some content to save as a note."
    _store().add_note(content)
    return "Note saved."


def list_notes(limit: int = 5) -> str:
    notes = _store().list_notes(limit)
    if not notes:
        return "You have no notes."
    return "Your latest notes: " + " | ".join(f"{nid}: {c}" for nid, c in notes)


def remember_preference(key: str, value: str) -> str:
    _store().set_preference(key, value)
    return f"I'll remember that your {key} is {value}."


def read_preference(key: str) -> str:
    val = _store().get_preference(key)
    if val is None:
        return f"I don't have a preference stored for {key}."
    return f"Your {key} is {val}."


def create_task(description: str) -> str:
    if not description:
        return "I need a description for the task."
    _store().add_task(description)
    return "Task added to your list."


def list_tasks(status: str | None = None, limit: int = 10) -> str:
    tasks = _store().list_tasks(status=status, limit=limit)
    if not tasks:
        return "You have no tasks."
    parts = [f"{tid} [{st}]: {desc}" for tid, desc, st in tasks]
    return "Your tasks: " + " | ".join(parts)


def complete_task(task_id: int) -> str:
    _store().update_task_status(task_id, "done")
    return f"Marked task {task_id} as done."

