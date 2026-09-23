from __future__ import annotations

from abc import ABC, abstractmethod

from openai import AsyncOpenAI


class SpeechToTextProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio: bytes) -> str:
        raise NotImplementedError


class OpenAISpeechToText(SpeechToTextProvider):
    def __init__(self, api_key: str, model: str, language: str = "fr-FR") -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.language = language.split("-")[0]

    async def transcribe(self, audio: bytes) -> str:
        if len(audio) <= 44:
            return ""
        result = await self.client.audio.transcriptions.create(
            model=self.model,
            file=("recording.wav", audio, "audio/wav"),
            language=self.language,
        )
        return result.text.strip()


class UnavailableSpeechToText(SpeechToTextProvider):
    async def transcribe(self, audio: bytes) -> str:
        raise RuntimeError(
            "La transcription vocale nécessite une clé OpenAI. Tu peux utiliser le champ de texte en attendant."
        )

