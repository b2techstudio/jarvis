from __future__ import annotations

import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.ai.provider import AIProvider, AIResponse, ToolCall


LOGGER = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def process(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> AIResponse:
        chat_tools = [
            {"type": "function", "function": {k: v for k, v in schema.items() if k != "type"}}
            for schema in tools
        ]
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=chat_tools or None,
            tool_choice="auto" if chat_tools else None,
            temperature=0.3,
        )
        message = response.choices[0].message
        calls: list[ToolCall] = []
        for call in message.tool_calls or []:
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                LOGGER.warning("Invalid tool arguments from AI for %s", call.function.name)
                arguments = {}
            calls.append(ToolCall(call.id, call.function.name, arguments))
        return AIResponse(message.content or "", calls)

