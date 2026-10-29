import sqlite3
from pathlib import Path
from typing import Any

class Database:
    """Small SQLite persistence layer. Each operation gets its own connection."""
    def __init__(self, path: str = "data/agent.db"):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self):
        with self.connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user','assistant','tool')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id, id);
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','done')),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_tasks_session_id ON tasks(session_id, status, id);
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    char_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def add_message(self, session_id: str, role: str, content: str) -> int:
        if role not in {"user", "assistant", "tool"}:
            raise ValueError("Unsupported message role")
        with self.connect() as conn:
            cur = conn.execute("INSERT INTO messages(session_id, role, content) VALUES(?,?,?)", (session_id, role, content))
            return int(cur.lastrowid)

    def get_messages(self, session_id: str, limit: int = 30) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 200))
        with self.connect() as conn:
            rows = conn.execute("SELECT role, content, created_at FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?", (session_id, limit)).fetchall()
        return [dict(row) for row in reversed(rows)]

    def clear_messages(self, session_id: str) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))

    def add_task(self, session_id: str, title: str) -> int:
        title = title.strip()
        if not title or len(title) > 500:
            raise ValueError("Task title must be between 1 and 500 characters")
        with self.connect() as conn:
            cur = conn.execute("INSERT INTO tasks(session_id, title) VALUES(?,?)", (session_id, title))
            return int(cur.lastrowid)

    def list_tasks(self, session_id: str, status: str | None = None) -> list[dict[str, Any]]:
        with self.connect() as conn:
            if status:
                rows = conn.execute("SELECT * FROM tasks WHERE session_id=? AND status=? ORDER BY id DESC", (session_id, status)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM tasks WHERE session_id=? ORDER BY id DESC", (session_id,)).fetchall()
        return [dict(row) for row in rows]

    def complete_task(self, session_id: str, task_id: int) -> bool:
        with self.connect() as conn:
            cur = conn.execute("UPDATE tasks SET status='done', completed_at=CURRENT_TIMESTAMP WHERE session_id=? AND id=? AND status='open'", (session_id, task_id))
            return cur.rowcount > 0

    def add_document(self, session_id: str, filename: str, summary: str, char_count: int) -> int:
        with self.connect() as conn:
            cur = conn.execute("INSERT INTO documents(session_id, filename, summary, char_count) VALUES(?,?,?,?)", (session_id, filename, summary, char_count))
            return int(cur.lastrowid)

    def list_documents(self, session_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM documents WHERE session_id=? ORDER BY id DESC", (session_id,)).fetchall()
        return [dict(row) for row in rows]
