import asyncio

from app.tools.base import AssistantTool, RiskLevel, ToolRegistry, ToolResult


class SafeTool(AssistantTool):
    name = "safe"
    description = "test"

    async def execute(self, **kwargs):
        return ToolResult(True, "ok")


class SensitiveTool(SafeTool):
    name = "sensitive"
    risk_level = RiskLevel.CONFIRMATION_REQUIRED


def test_registry_rejects_duplicates() -> None:
    registry = ToolRegistry()
    registry.register(SafeTool())
    try:
        registry.register(SafeTool())
        raise AssertionError("duplicate should fail")
    except ValueError:
        pass


def test_confirmation_is_enforced() -> None:
    registry = ToolRegistry()
    registry.register(SensitiveTool())
    rejected = asyncio.run(registry.execute("sensitive"))
    accepted = asyncio.run(registry.execute("sensitive", confirmed=True))
    assert rejected.success is False
    assert rejected.data["confirmation_required"] is True
    assert accepted.success is True

