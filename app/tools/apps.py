from __future__ import annotations

import asyncio
import logging
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from app.tools.base import AssistantTool, RiskLevel, ToolResult


LOGGER = logging.getLogger(__name__)


DEFAULT_APPS: dict[str, tuple[str, ...]] = {
    "bloc-notes": ("notepad.exe",),
    "notepad": ("notepad.exe",),
    "calculatrice": ("calc.exe",),
    "explorateur": ("explorer.exe",),
    "navigateur": ("msedge.exe", "chrome.exe", "firefox.exe"),
    "edge": ("msedge.exe",),
    "chrome": ("chrome.exe",),
    "firefox": ("firefox.exe",),
    "spotify": ("spotify.exe",),
    "discord": ("discord.exe",),
    "steam": ("steam.exe",),
    "vscode": ("code.exe",),
    "visual studio code": ("code.exe",),
}


class ApplicationResolver:
    def __init__(self, extra_apps: dict[str, str] | None = None) -> None:
        self.apps = dict(DEFAULT_APPS)
        for name, executable in (extra_apps or {}).items():
            self.apps[name.casefold()] = (executable,)

    def resolve(self, name: str) -> str | None:
        candidates = self.apps.get(name.strip().casefold(), ())
        for executable in candidates:
            found = shutil.which(executable)
            if found:
                return found
            discovered = self._common_location(executable)
            if discovered:
                return str(discovered)
        return None

    @classmethod
    def from_json(cls, path: Path) -> "ApplicationResolver":
        if not path.exists():
            return cls()
        try:
            content = json.loads(path.read_text(encoding="utf-8"))
            mappings = {str(key): str(value) for key, value in content.items()}
            return cls(mappings)
        except (OSError, ValueError, TypeError):
            LOGGER.exception("Invalid application mapping file: %s", path)
            return cls()

    @staticmethod
    def _common_location(executable: str) -> Path | None:
        roots = [
            os.getenv("LOCALAPPDATA"),
            os.getenv("APPDATA"),
            os.getenv("ProgramFiles"),
            os.getenv("ProgramFiles(x86)"),
        ]
        patterns = {
            "spotify.exe": ("Spotify/Spotify.exe",),
            "discord.exe": ("Discord/Update.exe",),
            "code.exe": ("Programs/Microsoft VS Code/Code.exe", "Microsoft VS Code/Code.exe"),
            "steam.exe": ("Steam/steam.exe",),
        }
        for root in filter(None, roots):
            for relative in patterns.get(executable.casefold(), ()):
                candidate = Path(root) / relative
                if candidate.exists():
                    return candidate
        return None


class OpenApplicationTool(AssistantTool):
    name = "open_application"
    description = "Ouvre une application Windows autorisée par son nom courant."
    parameters = {"application": {"type": "string", "description": "Nom de l'application"}}

    def __init__(self, resolver: ApplicationResolver) -> None:
        self.resolver = resolver

    async def execute(self, **kwargs: Any) -> ToolResult:
        app_name = str(kwargs.get("application", "")).strip()
        executable = self.resolver.resolve(app_name)
        if not executable:
            return ToolResult(False, f"Je n’ai pas trouvé {app_name} sur cet ordinateur.")
        try:
            await asyncio.to_thread(subprocess.Popen, [executable])
            LOGGER.info("Application opened: %s", app_name)
            return ToolResult(True, f"{app_name.capitalize()} ouverte.")
        except OSError as exc:
            LOGGER.exception("Could not open application %s", app_name)
            return ToolResult(False, f"Impossible d’ouvrir {app_name} : {exc}")


class CloseApplicationTool(AssistantTool):
    name = "close_application"
    description = "Ferme une application Windows connue après confirmation."
    risk_level = RiskLevel.CONFIRMATION_REQUIRED
    parameters = {"application": {"type": "string"}}

    def __init__(self, resolver: ApplicationResolver) -> None:
        self.resolver = resolver

    async def execute(self, **kwargs: Any) -> ToolResult:
        app_name = str(kwargs.get("application", "")).strip()
        executable = self.resolver.resolve(app_name)
        if not executable:
            return ToolResult(False, f"Je n’ai pas trouvé {app_name}.")
        image_name = Path(executable).name
        result = await asyncio.to_thread(
            subprocess.run,
            ["taskkill", "/IM", image_name],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            LOGGER.info("Application closed: %s", app_name)
            return ToolResult(True, f"{app_name.capitalize()} fermée.")
        return ToolResult(False, f"Je n’ai pas pu fermer {app_name} proprement.")
