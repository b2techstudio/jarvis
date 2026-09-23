from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Note:
    id: int
    text: str
    category: str | None
    created_at: datetime


@dataclass(slots=True)
class MemoryItem:
    id: int
    key: str | None
    value: str
    created_at: datetime

