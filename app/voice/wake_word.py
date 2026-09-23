from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable


class WakeWordProvider(ABC):
    @abstractmethod
    def start(self, callback: Callable[[], None]) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError


class DisabledWakeWord(WakeWordProvider):
    """Extension point for a future local wake-word engine."""

    def start(self, callback: Callable[[], None]) -> None:
        return None

    def stop(self) -> None:
        return None

