from __future__ import annotations

from typing import Any

from app.memory.repository import NoteRepository
from app.tools.base import AssistantTool, ToolResult


class AddNoteTool(AssistantTool):
    name = "add_note"
    description = "Ajoute une note dans la base locale."
    parameters = {
        "text": {"type": "string"},
        "category": {"type": ["string", "null"]},
    }

    def __init__(self, repository: NoteRepository) -> None:
        self.repository = repository

    async def execute(self, **kwargs: Any) -> ToolResult:
        try:
            note = self.repository.add(
                str(kwargs.get("text", "")), kwargs.get("category")
            )
            return ToolResult(True, "C’est noté.", {"id": note.id})
        except ValueError as exc:
            return ToolResult(False, str(exc))


class ListNotesTool(AssistantTool):
    name = "list_notes"
    description = "Retourne les dernières notes enregistrées."
    parameters = {"limit": {"type": "integer", "minimum": 1, "maximum": 20}}

    def __init__(self, repository: NoteRepository) -> None:
        self.repository = repository

    async def execute(self, **kwargs: Any) -> ToolResult:
        notes = self.repository.recent(int(kwargs.get("limit", 5)))
        if not notes:
            return ToolResult(True, "Tu n’as encore aucune note.", {"notes": []})
        lines = [f"{index}. {note.text}" for index, note in enumerate(notes, start=1)]
        return ToolResult(True, "Tes dernières notes :\n" + "\n".join(lines), {"notes": [n.text for n in notes]})

