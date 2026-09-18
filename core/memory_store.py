"""Small, local-only memory store for Nova.

SQLite is deliberately used from the standard library so the MVP stays easy to
install and the user's memories remain portable and inspectable.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class MemoryStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            )
        """)
        self.connection.commit()

    def add(self, content: str, category: str = "conversation", source: str = "user") -> int:
        if not content.strip():
            raise ValueError("Memory content cannot be empty")
        cursor = self.connection.execute(
            "INSERT INTO memories(category, content, source, created_at) VALUES (?, ?, ?, ?)",
            (category, content.strip(), source, datetime.now(timezone.utc).isoformat()),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def search(self, query: str = "", category: str | None = None, limit: int = 10) -> list[dict]:
        clauses = ["active = 1"]
        values: list[object] = []
        if query.strip():
            clauses.append("content LIKE ?")
            values.append(f"%{query.strip()}%")
        if category:
            clauses.append("category = ?")
            values.append(category)
        values.append(max(1, min(limit, 100)))
        rows = self.connection.execute(
            f"SELECT * FROM memories WHERE {' AND '.join(clauses)} ORDER BY id DESC LIMIT ?",
            values,
        ).fetchall()
        return [dict(row) for row in rows]

    def forget(self, memory_id: int) -> None:
        self.connection.execute("UPDATE memories SET active = 0 WHERE id = ?", (memory_id,))
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
