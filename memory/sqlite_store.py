import sqlite3
import json
from pathlib import Path
from typing import List, Tuple

from assistant.paths import data_dir


DB_PATH = data_dir() / "assistant_memory.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS preferences (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS command_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT,
    intent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS learned_commands (
    phrase TEXT PRIMARY KEY,
    intent TEXT NOT NULL,
    slots_json TEXT NOT NULL,
    language TEXT DEFAULT 'unknown',
    success_count INTEGER DEFAULT 1,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class SQLiteMemory:
    def __init__(self, path: Path = DB_PATH):
        self.conn = sqlite3.connect(path)
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def set_preference(self, key: str, value: str) -> None:
        self.conn.execute(
            "REPLACE INTO preferences(key, value) VALUES(?, ?)", (key, value)
        )
        self.conn.commit()

    def get_preference(self, key: str) -> str | None:
        row = self.conn.execute(
            "SELECT value FROM preferences WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else None

    def add_note(self, content: str) -> None:
        self.conn.execute("INSERT INTO notes(content) VALUES(?)", (content,))
        self.conn.commit()

    def list_notes(self, limit: int = 10) -> List[Tuple[int, str]]:
        rows = self.conn.execute(
            "SELECT id, content FROM notes ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return list(rows)

    def log_command(self, text: str, intent: str) -> None:
        self.conn.execute(
            "INSERT INTO command_history(text, intent) VALUES (?, ?)",
            (text, intent),
        )
        self.conn.commit()

    def list_command_history(self, limit: int = 20) -> List[Tuple[str, str, str]]:
        rows = self.conn.execute(
            "SELECT text, intent, created_at FROM command_history "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return list(rows)

    # --- Learned commands ---

    def get_learned_command(self, phrase: str) -> tuple[str, dict, str] | None:
        row = self.conn.execute(
            "SELECT intent, slots_json, language FROM learned_commands WHERE phrase = ?",
            (phrase,),
        ).fetchone()
        if row is None:
            return None
        intent, slots_json, language = row
        return intent, json.loads(slots_json), language or "unknown"

    def remember_command(
        self,
        phrase: str,
        intent: str,
        slots: dict,
        language: str = "unknown",
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO learned_commands(phrase, intent, slots_json, language, success_count)
            VALUES(?, ?, ?, ?, 1)
            ON CONFLICT(phrase) DO UPDATE SET
                intent = excluded.intent,
                slots_json = excluded.slots_json,
                language = excluded.language,
                success_count = learned_commands.success_count + 1,
                last_used = CURRENT_TIMESTAMP
            """,
            (phrase, intent, json.dumps(slots), language),
        )
        self.conn.commit()

    # --- Tasks ---

    def add_task(self, description: str) -> None:
        self.conn.execute(
            "INSERT INTO tasks(description) VALUES(?)",
            (description,),
        )
        self.conn.commit()

    def list_tasks(self, status: str | None = None, limit: int = 20) -> List[Tuple[int, str, str]]:
        if status:
            rows = self.conn.execute(
                "SELECT id, description, status FROM tasks WHERE status = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            )
        else:
            rows = self.conn.execute(
                "SELECT id, description, status FROM tasks "
                "ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        return list(rows)

    def update_task_status(self, task_id: int, status: str) -> None:
        self.conn.execute(
            "UPDATE tasks SET status = ? WHERE id = ?",
            (status, task_id),
        )
        self.conn.commit()

