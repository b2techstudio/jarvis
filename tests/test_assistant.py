import asyncio

from app.core.assistant import AssistantEngine
from app.core.command_router import CommandRouter
from app.tools.base import AssistantTool, RiskLevel, ToolRegistry, ToolResult


class PowerFake(AssistantTool):
    name = "power_action"
    description = "fake"
    risk_level = RiskLevel.CONFIRMATION_REQUIRED

    async def execute(self, **kwargs):
        return ToolResult(True, "Action exécutée.")


def test_sensitive_action_requires_confirmation() -> None:
    registry = ToolRegistry()
    registry.register(PowerFake())
    engine = AssistantEngine("Jarvis", registry, CommandRouter())
    first = asyncio.run(engine.handle("Éteins le PC"))
    second = asyncio.run(engine.handle("oui"))
    assert "Veux-tu vraiment" in first
    assert second == "Action exécutée."

