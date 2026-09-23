from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod

import pyttsx3


class TextToSpeechProvider(ABC):
    @abstractmethod
    async def speak(self, text: str) -> None:
        raise NotImplementedError


class WindowsTextToSpeech(TextToSpeechProvider):
    def __init__(self, rate: int = 180, volume: float = 0.9, language: str = "fr") -> None:
        self.rate = rate
        self.volume = volume
        self.language = language.casefold()

    def _speak(self, text: str) -> None:
        engine = pyttsx3.init()
        engine.setProperty("rate", self.rate)
        engine.setProperty("volume", self.volume)
        for voice in engine.getProperty("voices"):
            languages = " ".join(str(item) for item in getattr(voice, "languages", []))
            descriptor = f"{voice.name} {voice.id} {languages}".casefold()
            if self.language[:2] in descriptor or "french" in descriptor:
                engine.setProperty("voice", voice.id)
                break
        engine.say(text)
        engine.runAndWait()
        engine.stop()

    async def speak(self, text: str) -> None:
        if text.strip():
            await asyncio.to_thread(self._speak, text)

