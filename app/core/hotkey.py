from __future__ import annotations

import logging
from collections.abc import Callable

from pynput import keyboard


LOGGER = logging.getLogger(__name__)


class GlobalHotkey:
    def __init__(self, shortcut: str, callback: Callable[[], None]) -> None:
        self.shortcut = shortcut
        self.callback = callback
        self.listener: keyboard.GlobalHotKeys | None = None

    def start(self) -> None:
        try:
            self.listener = keyboard.GlobalHotKeys({self.shortcut: self.callback})
            self.listener.start()
            LOGGER.info("Global hotkey enabled: %s", self.shortcut)
        except Exception:
            LOGGER.exception("Could not enable global hotkey")

    def stop(self) -> None:
        if self.listener:
            self.listener.stop()
            self.listener = None

