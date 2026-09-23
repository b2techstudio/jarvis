from __future__ import annotations

from enum import StrEnum


class AssistantState(StrEnum):
    IDLE = "En veille"
    LISTENING = "Écoute"
    ANALYZING = "Analyse"
    EXECUTING = "Exécution"
    RESPONDING = "Réponse"
    ERROR = "Indisponible"

