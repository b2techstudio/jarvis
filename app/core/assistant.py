from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from app.ai.prompts import SYSTEM_PROMPT
from app.ai.provider import AIProvider
from app.core.command_router import CommandRouter, RouteKind
from app.core.events import AssistantState
from app.tools.base import RiskLevel, ToolRegistry, ToolResult


LOGGER = logging.getLogger(__name__)
StateCallback = Callable[[AssistantState], None]


@dataclass(slots=True)
class PendingAction:
    tool_name: str
    arguments: dict[str, Any]


class AssistantEngine:
    def __init__(
        self,
        name: str,
        registry: ToolRegistry,
        router: CommandRouter,
        ai_provider: AIProvider | None = None,
        on_state: StateCallback | None = None,
        max_history: int = 12,
    ) -> None:
        self.name = name
        self.registry = registry
        self.router = router
        self.ai_provider = ai_provider
        self.on_state = on_state or (lambda _state: None)
        self.max_history = max_history
        self.history: list[dict[str, Any]] = []
        self.pending_action: PendingAction | None = None

    def _state(self, state: AssistantState) -> None:
        self.on_state(state)

    async def handle(self, message: str) -> str:
        message = message.strip()
        if not message:
            return "Je n’ai rien entendu."
        self._state(AssistantState.ANALYZING)
        route = self.router.route(message, self.pending_action is not None)
        if route.kind is RouteKind.CONFIRM and self.pending_action:
            pending, self.pending_action = self.pending_action, None
            result = await self._execute(pending.tool_name, pending.arguments, confirmed=True)
            return self._finish(message, result.message)
        if route.kind is RouteKind.CANCEL and self.pending_action:
            self.pending_action = None
            return self._finish(message, "Action annulée.")
        if self.pending_action is not None:
            return self._finish(message, "Réponds simplement oui pour confirmer, ou non pour annuler.")
        if route.kind is RouteKind.TOOL and route.tool_name:
            tool = self.registry.get(route.tool_name)
            if tool and tool.risk_level is RiskLevel.CONFIRMATION_REQUIRED:
                self.pending_action = PendingAction(route.tool_name, route.arguments)
                prompt = self._confirmation_prompt(route.tool_name, route.arguments)
                return self._finish(message, prompt)
            result = await self._execute(route.tool_name, route.arguments)
            return self._finish(message, result.message)
        if self.ai_provider is None:
            return self._finish(
                message,
                "La connexion IA n’est pas configurée. Je peux quand même gérer les applications, le volume, les notes, les fichiers, la date et l’heure.",
            )
        response = await self._ask_ai(message)
        return self._finish(message, response)

    async def _execute(
        self, name: str, arguments: dict[str, Any], confirmed: bool = False
    ) -> ToolResult:
        self._state(AssistantState.EXECUTING)
        LOGGER.info("Executing tool: %s", name)
        try:
            return await self.registry.execute(name, confirmed=confirmed, **arguments)
        except Exception:
            LOGGER.exception("Tool failed: %s", name)
            return ToolResult(False, "L’action a échoué de façon inattendue.")

    async def _ask_ai(self, message: str) -> str:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT.format(assistant_name=self.name)},
            *self.history[-self.max_history :],
            {"role": "user", "content": message},
        ]
        try:
            first = await self.ai_provider.process(messages, self.registry.schemas())
            if not first.tool_calls:
                return first.text or "Je n’ai pas de réponse pour le moment."
            call = first.tool_calls[0]
            tool = self.registry.get(call.name)
            if tool is None:
                return "L’IA a demandé une action inconnue."
            if tool.risk_level is RiskLevel.CONFIRMATION_REQUIRED:
                self.pending_action = PendingAction(call.name, call.arguments)
                return self._confirmation_prompt(call.name, call.arguments)
            result = await self._execute(call.name, call.arguments)
            return result.message
        except Exception as exc:
            LOGGER.exception("AI provider error")
            return f"Le service d’intelligence artificielle est indisponible : {type(exc).__name__}."

    def _finish(self, user_message: str, answer: str) -> str:
        self.history.extend(
            [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": answer},
            ]
        )
        self.history = self.history[-self.max_history :]
        self._state(AssistantState.RESPONDING)
        return answer

    @staticmethod
    def _confirmation_prompt(name: str, arguments: dict[str, Any]) -> str:
        if name == "power_action":
            labels = {"shutdown": "éteindre", "restart": "redémarrer", "logout": "déconnecter la session"}
            action = labels.get(str(arguments.get("action")), "effectuer cette action")
            return f"Veux-tu vraiment {action} ? Réponds oui pour confirmer."
        if name == "close_application":
            return f"Veux-tu vraiment fermer {arguments.get('application', 'cette application')} ? Du travail non enregistré pourrait être perdu."
        return "Cette action est sensible. Veux-tu vraiment continuer ?"

