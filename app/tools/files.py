from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from app.tools.base import AssistantTool, ToolResult


KNOWN_FOLDERS = {
    "bureau": Path.home() / "Desktop",
    "desktop": Path.home() / "Desktop",
    "documents": Path.home() / "Documents",
    "téléchargements": Path.home() / "Downloads",
    "telechargements": Path.home() / "Downloads",
    "downloads": Path.home() / "Downloads",
}


class OpenFolderTool(AssistantTool):
    name = "open_folder"
    description = "Ouvre un dossier utilisateur connu ou un chemin existant."
    parameters = {"folder": {"type": "string"}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        value = str(kwargs.get("folder", "")).strip()
        path = KNOWN_FOLDERS.get(value.casefold(), Path(value).expanduser())
        if not path.is_dir():
            return ToolResult(False, f"Je n’ai pas trouvé le dossier {value}.")
        await asyncio.to_thread(os.startfile, str(path))
        return ToolResult(True, f"Dossier {value} ouvert.")


class OpenFileTool(AssistantTool):
    name = "open_file"
    description = "Ouvre un fichier existant avec son application associée."
    parameters = {"path": {"type": "string"}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        path = Path(str(kwargs.get("path", ""))).expanduser()
        if not path.is_file():
            return ToolResult(False, "Je n’ai pas trouvé ce fichier.")
        await asyncio.to_thread(os.startfile, str(path))
        return ToolResult(True, f"{path.name} ouvert.")


class SearchFileTool(AssistantTool):
    name = "search_file"
    description = "Recherche un fichier par nom dans Bureau, Documents et Téléchargements."
    parameters = {"name": {"type": "string"}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = str(kwargs.get("name", "")).strip().casefold()
        if not query:
            return ToolResult(False, "Le nom du fichier est vide.")

        def search() -> list[str]:
            matches: list[str] = []
            for root in dict.fromkeys(KNOWN_FOLDERS.values()):
                if not root.exists():
                    continue
                for current, dirs, files in os.walk(root):
                    dirs[:] = [d for d in dirs if not d.startswith(".")]
                    for filename in files:
                        if query in filename.casefold():
                            matches.append(str(Path(current) / filename))
                            if len(matches) >= 10:
                                return matches
            return matches

        matches = await asyncio.to_thread(search)
        if not matches:
            return ToolResult(False, f"Aucun fichier correspondant à « {query} ».")
        return ToolResult(True, f"J’ai trouvé {len(matches)} fichier(s).", {"matches": matches})

