from __future__ import annotations

import webbrowser
from typing import Any
from urllib.parse import quote_plus, urlparse

from app.tools.base import AssistantTool, ToolResult


class OpenUrlTool(AssistantTool):
    name = "open_url"
    description = "Ouvre une adresse HTTP ou HTTPS dans le navigateur par défaut."
    parameters = {"url": {"type": "string"}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        url = str(kwargs.get("url", "")).strip()
        if not urlparse(url).scheme:
            url = f"https://{url}"
        if urlparse(url).scheme not in {"http", "https"}:
            return ToolResult(False, "Seules les adresses HTTP et HTTPS sont autorisées.")
        opened = webbrowser.open(url)
        return ToolResult(opened, "Page ouverte." if opened else "Je n’ai pas pu ouvrir cette page.")


class WebSearchTool(AssistantTool):
    name = "web_search"
    description = "Lance une recherche web dans le navigateur par défaut."
    parameters = {"query": {"type": "string"}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = str(kwargs.get("query", "")).strip()
        if not query:
            return ToolResult(False, "La recherche est vide.")
        opened = webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
        return ToolResult(opened, f"Je recherche « {query} ».")

