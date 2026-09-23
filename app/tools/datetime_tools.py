from __future__ import annotations

from datetime import datetime
from typing import Any

import dateparser

from app.tools.base import AssistantTool, ToolResult


WEEKDAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MONTHS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def french_date(value: datetime) -> str:
    return f"{WEEKDAYS[value.weekday()]} {value.day} {MONTHS[value.month - 1]} {value.year}"


class CurrentDateTimeTool(AssistantTool):
    name = "current_datetime"
    description = "Donne l'heure et la date locales du système."

    async def execute(self, **kwargs: Any) -> ToolResult:
        now = datetime.now().astimezone()
        return ToolResult(
            True,
            f"Il est {now:%H h %M}. Nous sommes le {french_date(now)}.",
            {"iso": now.isoformat()},
        )


class ParseDateTool(AssistantTool):
    name = "parse_date"
    description = "Interprète une date relative en français, par exemple vendredi prochain."
    parameters = {"expression": {"type": "string"}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        expression = str(kwargs.get("expression", ""))
        parsed = dateparser.parse(
            expression,
            languages=["fr"],
            settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": datetime.now()},
        )
        if parsed is None:
            return ToolResult(False, "Je n’ai pas compris cette date.")
        return ToolResult(True, f"Ce sera le {french_date(parsed)}.", {"iso": parsed.isoformat()})

