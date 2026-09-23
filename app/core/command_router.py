from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RouteKind(StrEnum):
    TOOL = "tool"
    CONVERSATION = "conversation"
    CONFIRM = "confirm"
    CANCEL = "cancel"


@dataclass(slots=True)
class Route:
    kind: RouteKind
    tool_name: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char)).strip()


class CommandRouter:
    YES = {"oui", "confirme", "je confirme", "vas-y", "d'accord", "ok", "execute"}
    NO = {"non", "annule", "annuler", "laisse tomber", "stop"}

    def route(self, message: str, awaiting_confirmation: bool = False) -> Route:
        clean = normalize(message).strip(" .!?…")
        if awaiting_confirmation:
            if clean in {normalize(value) for value in self.YES}:
                return Route(RouteKind.CONFIRM)
            if clean in {normalize(value) for value in self.NO}:
                return Route(RouteKind.CANCEL)

        note_match = re.match(
            r"(?:note(?: que)?|ajoute dans mes notes\s*:?)\s+(.+)",
            message.strip().strip(" .!?…"),
            flags=re.IGNORECASE,
        )
        if note_match:
            return Route(RouteKind.TOOL, "add_note", {"text": note_match.group(1).strip()})
        if re.search(r"(?:quelles?|liste|montre).*(?:notes?)|dernieres notes", clean):
            return Route(RouteKind.TOOL, "list_notes", {"limit": 5})

        volume = re.search(r"(?:mets?|regle|passe).*?(?:son|volume).*?(\d{1,3})\s*%?", clean)
        if volume:
            return Route(RouteKind.TOOL, "set_volume", {"level": int(volume.group(1))})
        if re.search(r"(?:quel|combien).*(?:son|volume)|niveau du (?:son|volume)", clean):
            return Route(RouteKind.TOOL, "get_volume")
        if re.search(r"(?:coupe|mute).*(?:son|volume)|mets.*muet", clean):
            return Route(RouteKind.TOOL, "set_mute", {"muted": True})
        if re.search(r"(?:remets|reactive|unmute).*(?:son|volume)", clean):
            return Route(RouteKind.TOOL, "set_mute", {"muted": False})

        if re.search(r"(?:quelle heure|quel jour|quelle date|sommes-nous)", clean):
            relative = re.search(r"date (?:de |du )?(.+)", clean)
            if relative and relative.group(1) not in {"aujourd'hui", "ce jour"}:
                return Route(RouteKind.TOOL, "parse_date", {"expression": relative.group(1)})
            return Route(RouteKind.TOOL, "current_datetime")

        search = re.match(r"(?:recherche|cherche)(?: sur (?:internet|le web))?\s+(.+)", clean)
        if search:
            return Route(RouteKind.TOOL, "web_search", {"query": search.group(1)})
        url = re.match(r"ouvre\s+(https?://\S+|www\.\S+)", clean)
        if url:
            return Route(RouteKind.TOOL, "open_url", {"url": url.group(1)})

        folder = re.match(r"ouvre (?:le dossier |mes? )?(bureau|documents?|telechargements?|downloads?)", clean)
        if folder:
            return Route(RouteKind.TOOL, "open_folder", {"folder": folder.group(1)})

        power_patterns = {
            "shutdown": r"(?:eteins|arrete).*(?:pc|ordinateur|windows)",
            "restart": r"(?:redemarre).*(?:pc|ordinateur|windows)",
            "logout": r"(?:deconnecte).*(?:session|utilisateur)",
        }
        for action, pattern in power_patterns.items():
            if re.search(pattern, clean):
                return Route(RouteKind.TOOL, "power_action", {"action": action})

        close_match = re.match(r"(?:ferme|quitte)\s+(.+)", clean)
        if close_match:
            return Route(RouteKind.TOOL, "close_application", {"application": close_match.group(1)})
        open_match = re.match(r"(?:ouvre|lance|demarre)\s+(.+)", clean)
        if open_match:
            return Route(RouteKind.TOOL, "open_application", {"application": open_match.group(1)})

        if re.search(r"(?:cpu|processeur|ram|memoire|espace disque)", clean):
            return Route(RouteKind.TOOL, "system_stats")
        return Route(RouteKind.CONVERSATION)
