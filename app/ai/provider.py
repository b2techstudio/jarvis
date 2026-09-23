from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(slots=True)
class AIResponse:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class AIProvider(ABC):
    @abstractmethod
    async def process(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> AIResponse:
        raise NotImplementedError

