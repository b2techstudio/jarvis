from __future__ import annotations

import ctypes
import logging
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from app.ai.openai_provider import OpenAIProvider
from app.core.assistant import AssistantEngine
from app.core.command_router import CommandRouter
from app.core.config import Settings
from app.core.logger import configure_logging
from app.memory.database import Database
from app.memory.repository import NoteRepository
from app.tools.apps import ApplicationResolver, CloseApplicationTool, OpenApplicationTool
from app.tools.base import ToolRegistry
from app.tools.browser import OpenUrlTool, WebSearchTool
from app.tools.datetime_tools import CurrentDateTimeTool, ParseDateTool
from app.tools.files import OpenFileTool, OpenFolderTool, SearchFileTool
from app.tools.notes import AddNoteTool, ListNotesTool
from app.tools.system import GetVolumeTool, MuteTool, PowerTool, SetVolumeTool, SystemStatsTool
from app.ui.main_window import MainWindow
from app.ui.styles.theme import STYLESHEET
from app.voice.speech_to_text import OpenAISpeechToText, UnavailableSpeechToText
from app.voice.text_to_speech import WindowsTextToSpeech


LOGGER = logging.getLogger(__name__)


def build_registry(notes: NoteRepository, settings: Settings | None = None) -> ToolRegistry:
    registry = ToolRegistry()
    resolver = ApplicationResolver.from_json(settings.data_dir / "apps.json") if settings else ApplicationResolver()
    for tool in (
        OpenApplicationTool(resolver),
        CloseApplicationTool(resolver),
        SystemStatsTool(),
        GetVolumeTool(),
        SetVolumeTool(),
        MuteTool(),
        PowerTool(),
        OpenUrlTool(),
        WebSearchTool(),
        OpenFolderTool(),
        OpenFileTool(),
        SearchFileTool(),
        AddNoteTool(notes),
        ListNotesTool(notes),
        CurrentDateTimeTool(),
        ParseDateTool(),
    ):
        registry.register(tool)
    return registry


def create_window(settings: Settings) -> MainWindow:
    database = Database(settings.database_path)
    database.initialize()
    notes = NoteRepository(database)
    registry = build_registry(notes, settings)
    ai_provider = (
        OpenAIProvider(settings.openai_api_key, settings.openai_model)
        if settings.ai_configured
        else None
    )
    stt = (
        OpenAISpeechToText(
            settings.openai_api_key, settings.transcription_model, settings.language
        )
        if settings.ai_configured
        else UnavailableSpeechToText()
    )
    tts = WindowsTextToSpeech(
        rate=settings.tts_rate,
        volume=settings.tts_volume,
        language=settings.language,
    )
    assistant = AssistantEngine(
        name=settings.assistant_name,
        registry=registry,
        router=CommandRouter(),
        ai_provider=ai_provider,
    )
    return MainWindow(settings, database, assistant, stt, tts)


def main() -> int:
    settings = Settings.load()
    configure_logging(settings.log_dir, settings.log_level)
    LOGGER.info("Starting JARVIS Desktop")
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "B2TechStudio.JarvisDesktop.V1"
            )
        except Exception:
            LOGGER.debug("Could not set Windows app ID", exc_info=True)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName(f"{settings.assistant_name} Desktop")
    app.setStyleSheet(STYLESHEET)

    def exception_hook(exc_type, exc_value, exc_traceback) -> None:
        LOGGER.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
        QMessageBox.critical(None, "Erreur", "Une erreur inattendue est survenue. Consulte les logs.")

    sys.excepthook = exception_hook
    window = create_window(settings)
    window.show()
    QTimer.singleShot(250, window.show_onboarding_if_needed)
    exit_code = app.exec()
    LOGGER.info("JARVIS Desktop stopped")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
