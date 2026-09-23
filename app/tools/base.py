from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RiskLevel(StrEnum):
    SAFE = "safe"
    CONFIRMATION_REQUIRED = "confirmation_required"
    FORBIDDEN_AUTOMATICALLY = "forbidden_automatically"


@dataclass(slots=True)
class ToolResult:
    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)


class AssistantTool(ABC):
    name: str
    description: str
    risk_level: RiskLevel = RiskLevel.SAFE
    parameters: dict[str, Any] = {}

    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "additionalProperties": False,
            },
        }

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        raise NotImplementedError


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, AssistantTool] = {}

    def register(self, tool: AssistantTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"L'outil '{tool.name}' est déjà enregistré.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> AssistantTool | None:
        return self._tools.get(name)

    def all(self) -> list[AssistantTool]:
        return list(self._tools.values())

    def schemas(self) -> list[dict[str, Any]]:
        return [tool.schema() for tool in self.all()]

    async def execute(
        self, name: str, *, confirmed: bool = False, **kwargs: Any
    ) -> ToolResult:
        tool = self.get(name)
        if tool is None:
            return ToolResult(False, f"Outil inconnu : {name}.")
        if tool.risk_level is RiskLevel.FORBIDDEN_AUTOMATICALLY:
            return ToolResult(False, "Cette action est interdite en mode automatique.")
        if tool.risk_level is RiskLevel.CONFIRMATION_REQUIRED and not confirmed:
            return ToolResult(False, "Cette action nécessite une confirmation.", {"confirmation_required": True})
        return await tool.execute(**kwargs)

