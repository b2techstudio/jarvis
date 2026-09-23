from __future__ import annotations

import asyncio
import logging
import subprocess
from typing import Any

import psutil

from app.tools.base import AssistantTool, RiskLevel, ToolResult


LOGGER = logging.getLogger(__name__)


def _endpoint_volume():
    from pycaw.pycaw import AudioUtilities

    return AudioUtilities.GetSpeakers().EndpointVolume


class SystemStatsTool(AssistantTool):
    name = "system_stats"
    description = "Retourne l'utilisation du processeur, de la mémoire et du disque."

    async def execute(self, **kwargs: Any) -> ToolResult:
        cpu, memory, disk = await asyncio.gather(
            asyncio.to_thread(psutil.cpu_percent, 0.2),
            asyncio.to_thread(lambda: psutil.virtual_memory().percent),
            asyncio.to_thread(lambda: psutil.disk_usage("C:\\").percent),
        )
        message = f"CPU {cpu:.0f} %, mémoire {memory:.0f} %, disque {disk:.0f} %."
        return ToolResult(True, message, {"cpu": cpu, "memory": memory, "disk": disk})


class GetVolumeTool(AssistantTool):
    name = "get_volume"
    description = "Indique le volume audio principal de Windows."

    async def execute(self, **kwargs: Any) -> ToolResult:
        try:
            endpoint = await asyncio.to_thread(_endpoint_volume)
            volume = round(endpoint.GetMasterVolumeLevelScalar() * 100)
            muted = bool(endpoint.GetMute())
            suffix = " (muet)" if muted else ""
            return ToolResult(True, f"Le volume est à {volume} %{suffix}.", {"volume": volume, "muted": muted})
        except Exception as exc:
            LOGGER.exception("Volume read failed")
            return ToolResult(False, f"Je ne peux pas lire le volume : {exc}")


class SetVolumeTool(AssistantTool):
    name = "set_volume"
    description = "Règle le volume principal Windows entre 0 et 100 %."
    parameters = {"level": {"type": "integer", "minimum": 0, "maximum": 100}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        try:
            level = max(0, min(100, int(kwargs.get("level", 0))))
            endpoint = await asyncio.to_thread(_endpoint_volume)
            await asyncio.to_thread(endpoint.SetMasterVolumeLevelScalar, level / 100, None)
            LOGGER.info("Volume changed to %s", level)
            return ToolResult(True, f"Volume réglé à {level} %.", {"volume": level})
        except Exception as exc:
            LOGGER.exception("Volume change failed")
            return ToolResult(False, f"Je n’ai pas pu régler le volume : {exc}")


class MuteTool(AssistantTool):
    name = "set_mute"
    description = "Active ou désactive le mode muet Windows."
    parameters = {"muted": {"type": "boolean"}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        muted = bool(kwargs.get("muted", True))
        try:
            endpoint = await asyncio.to_thread(_endpoint_volume)
            await asyncio.to_thread(endpoint.SetMute, muted, None)
            return ToolResult(True, "Son coupé." if muted else "Son réactivé.")
        except Exception as exc:
            LOGGER.exception("Mute change failed")
            return ToolResult(False, f"Je n’ai pas pu modifier le mode muet : {exc}")


class PowerTool(AssistantTool):
    risk_level = RiskLevel.CONFIRMATION_REQUIRED
    parameters = {"action": {"type": "string", "enum": ["shutdown", "restart", "logout"]}}
    name = "power_action"
    description = "Éteint, redémarre ou déconnecte Windows après confirmation explicite."

    async def execute(self, **kwargs: Any) -> ToolResult:
        action = str(kwargs.get("action", ""))
        commands = {
            "shutdown": ["shutdown", "/s", "/t", "0"],
            "restart": ["shutdown", "/r", "/t", "0"],
            "logout": ["shutdown", "/l"],
        }
        if action not in commands:
            return ToolResult(False, "Action d’alimentation inconnue.")
        LOGGER.warning("Executing confirmed power action: %s", action)
        try:
            subprocess.Popen(commands[action])
            return ToolResult(True, "Action système lancée.")
        except OSError as exc:
            return ToolResult(False, f"L’action système a échoué : {exc}")
