from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "oui"}


def _as_float(value: str | None, default: float) -> float:
    try:
        return float(value) if value is not None else default
    except ValueError:
        return default


@dataclass(slots=True)
class Settings:
    root_dir: Path
    data_dir: Path
    log_dir: Path
    database_path: Path
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    transcription_model: str = "gpt-4o-mini-transcribe"
    assistant_name: str = "Jarvis"
    language: str = "fr-FR"
    enable_tts: bool = True
    enable_wake_word: bool = False
    tts_rate: int = 180
    tts_volume: float = 0.9
    log_level: str = "INFO"
    global_hotkey: str = "<ctrl>+<alt>+<space>"
    minimize_to_tray: bool = True

    @property
    def ai_configured(self) -> bool:
        return bool(self.openai_api_key)

    @classmethod
    def load(cls, root_dir: Path | None = None) -> "Settings":
        root = (root_dir or ROOT_DIR).resolve()
        load_dotenv(root / ".env")
        data_dir = root / "data"
        log_dir = root / "logs"
        data_dir.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            root_dir=root,
            data_dir=data_dir,
            log_dir=log_dir,
            database_path=data_dir / "jarvis.db",
            openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            transcription_model=os.getenv(
                "OPENAI_TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe"
            ),
            assistant_name=os.getenv("ASSISTANT_NAME", "Jarvis"),
            language=os.getenv("LANGUAGE", "fr-FR"),
            enable_tts=_as_bool(os.getenv("ENABLE_TTS"), True),
            enable_wake_word=_as_bool(os.getenv("ENABLE_WAKE_WORD"), False),
            tts_rate=int(_as_float(os.getenv("TTS_RATE"), 180)),
            tts_volume=max(0.0, min(1.0, _as_float(os.getenv("TTS_VOLUME"), 0.9))),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            global_hotkey=os.getenv("GLOBAL_HOTKEY", "<ctrl>+<alt>+<space>"),
            minimize_to_tray=_as_bool(os.getenv("MINIMIZE_TO_TRAY"), True),
        )

