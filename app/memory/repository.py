from __future__ import annotations

from datetime import datetime

from app.memory.database import Database
from app.memory.models import MemoryItem, Note


def _parse_date(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class NoteRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def add(self, text: str, category: str | None = None) -> Note:
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("Une note ne peut pas être vide.")
        with self.database.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO notes(text, category) VALUES (?, ?)", (cleaned, category)
            )
            row = connection.execute(
                "SELECT * FROM notes WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return Note(row["id"], row["text"], row["category"], _parse_date(row["created_at"]))

    def recent(self, limit: int = 5) -> list[Note]:
        safe_limit = max(1, min(limit, 50))
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM notes ORDER BY id DESC LIMIT ?", (safe_limit,)
            ).fetchall()
        return [Note(r["id"], r["text"], r["category"], _parse_date(r["created_at"])) for r in rows]


class MemoryManager:
    def __init__(self, database: Database) -> None:
        self.database = database

    def save_memory(self, value: str, key: str | None = None) -> int:
        with self.database.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO memory_items(key, value) VALUES (?, ?)", (key, value)
            )
            return int(cursor.lastrowid)

    def search_memory(self, query: str, limit: int = 10) -> list[MemoryItem]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM memory_items WHERE value LIKE ? OR key LIKE ? ORDER BY id DESC LIMIT ?",
                (f"%{query}%", f"%{query}%", max(1, min(limit, 50))),
            ).fetchall()
        return [MemoryItem(r["id"], r["key"], r["value"], _parse_date(r["created_at"])) for r in rows]

    def get_recent_memories(self, limit: int = 10) -> list[MemoryItem]:
        return self.search_memory("", limit)

    def delete_memory(self, memory_id: int) -> bool:
        with self.database.connect() as connection:
            cursor = connection.execute("DELETE FROM memory_items WHERE id = ?", (memory_id,))
            return cursor.rowcount > 0

