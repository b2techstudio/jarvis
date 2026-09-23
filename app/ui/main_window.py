from __future__ import annotations

import asyncio
import logging
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime

import psutil
from PySide6.QtCore import QObject, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QColor, QCloseEvent, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QMainWindow, QMessageBox, QPushButton, QSystemTrayIcon, QVBoxLayout, QWidget,
    QMenu,
)

from app.core.assistant import AssistantEngine
from app.core.config import Settings
from app.core.events import AssistantState
from app.core.hotkey import GlobalHotkey
from app.memory.database import Database
from app.ui.onboarding import OnboardingDialog
from app.ui.settings_dialog import SettingsDialog
from app.ui.widgets.orb import AssistantOrb
from app.voice.microphone import MicrophoneRecorder
from app.voice.speech_to_text import SpeechToTextProvider
from app.voice.text_to_speech import TextToSpeechProvider, WindowsTextToSpeech


LOGGER = logging.getLogger(__name__)


class UiBridge(QObject):
    state_changed = Signal(object)
    answer_ready = Signal(str, str)
    transcription_ready = Signal(str)
    error = Signal(str)
    hotkey_triggered = Signal()


def create_icon(size: int = 64) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QColor("#70e7ff"))
    painter.setBrush(QColor("#123441"))
    painter.drawEllipse(5, 5, size - 10, size - 10)
    painter.setBrush(QColor("#70e7ff"))
    painter.drawEllipse(size // 2 - 5, size // 2 - 5, 10, 10)
    painter.end()
    return QIcon(pixmap)


class MainWindow(QMainWindow):
    def __init__(
        self,
        settings: Settings,
        database: Database,
        assistant: AssistantEngine,
        stt: SpeechToTextProvider,
        tts: TextToSpeechProvider,
    ) -> None:
        super().__init__()
        self.settings = settings
        self.database = database
        self.assistant = assistant
        self.stt = stt
        self.tts = tts
        self.recorder = MicrophoneRecorder()
        self.executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="jarvis")
        self.bridge = UiBridge()
        self.bridge.state_changed.connect(self.set_state)
        self.bridge.answer_ready.connect(self._show_answer)
        self.bridge.transcription_ready.connect(self._on_transcription)
        self.bridge.error.connect(self._show_error)
        self.bridge.hotkey_triggered.connect(self.toggle_recording)
        self.assistant.on_state = self.bridge.state_changed.emit
        self._really_quit = False

        self.setWindowTitle(f"{settings.assistant_name} Desktop")
        self.setWindowIcon(create_icon())
        self.resize(1040, 720)
        self.setMinimumSize(820, 600)
        self._build_ui()
        self._build_tray()
        self.hotkey = GlobalHotkey(settings.global_hotkey, self.bridge.hotkey_triggered.emit)
        self.hotkey.start()
        self._start_clock()

    def _build_ui(self) -> None:
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(24, 18, 24, 18)

        header = QHBoxLayout()
        self.title_label = QLabel(self.settings.assistant_name.upper())
        self.title_label.setObjectName("title")
        self.connection_label = QLabel(
            "● IA connectée" if self.settings.ai_configured else "○ IA locale uniquement"
        )
        self.connection_label.setObjectName("good" if self.settings.ai_configured else "muted")
        self.mic_status = QLabel("● Micro prêt")
        self.clock_label = QLabel()
        settings_button = QPushButton("Paramètres")
        settings_button.clicked.connect(self.open_settings)
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.connection_label)
        header.addWidget(self.mic_status)
        header.addWidget(self.clock_label)
        header.addWidget(settings_button)
        outer.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(18)
        assistant_panel = QFrame()
        assistant_panel.setObjectName("panel")
        assistant_layout = QVBoxLayout(assistant_panel)
        assistant_layout.setAlignment(Qt.AlignCenter)
        self.orb = AssistantOrb()
        self.state_label = QLabel(AssistantState.IDLE.value)
        self.state_label.setObjectName("state")
        self.state_label.setAlignment(Qt.AlignCenter)
        self.transcription_label = QLabel("Clique sur le microphone ou écris une commande.")
        self.transcription_label.setWordWrap(True)
        self.transcription_label.setAlignment(Qt.AlignCenter)
        self.answer_label = QLabel("Assistant prêt.")
        self.answer_label.setWordWrap(True)
        self.answer_label.setAlignment(Qt.AlignCenter)
        self.answer_label.setMinimumHeight(70)
        assistant_layout.addWidget(self.orb, alignment=Qt.AlignCenter)
        assistant_layout.addWidget(self.state_label)
        assistant_layout.addWidget(self.transcription_label)
        assistant_layout.addWidget(self.answer_label)
        body.addWidget(assistant_panel, 3)

        history_panel = QFrame()
        history_panel.setObjectName("panel")
        history_layout = QVBoxLayout(history_panel)
        history_layout.addWidget(QLabel("HISTORIQUE"))
        self.history_list = QListWidget()
        history_layout.addWidget(self.history_list)
        self.metrics_label = QLabel("CPU —  ·  RAM —")
        self.metrics_label.setObjectName("muted")
        history_layout.addWidget(self.metrics_label)
        body.addWidget(history_panel, 2)
        outer.addLayout(body, 1)

        controls = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Écris une commande…")
        self.input_edit.returnPressed.connect(self.submit_text)
        send_button = QPushButton("Envoyer")
        send_button.clicked.connect(self.submit_text)
        self.mic_button = QPushButton("●")
        self.mic_button.setObjectName("mic")
        self.mic_button.setToolTip(f"Push-to-talk — raccourci {self.settings.global_hotkey}")
        self.mic_button.clicked.connect(self.toggle_recording)
        controls.addWidget(self.input_edit, 1)
        controls.addWidget(send_button)
        controls.addWidget(self.mic_button)
        outer.addLayout(controls)
        self.setCentralWidget(central)

    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(create_icon(), self)
        menu = QMenu()
        open_action = QAction("Ouvrir Jarvis", self)
        listen_action = QAction("Déclencher l’écoute", self)
        settings_action = QAction("Paramètres", self)
        quit_action = QAction("Quitter", self)
        open_action.triggered.connect(self._restore)
        listen_action.triggered.connect(self.toggle_recording)
        settings_action.triggered.connect(self.open_settings)
        quit_action.triggered.connect(self.quit_application)
        menu.addActions([open_action, listen_action, settings_action])
        menu.addSeparator()
        menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: self._restore() if reason == QSystemTrayIcon.DoubleClick else None)
        self.tray.show()

    def _start_clock(self) -> None:
        timer = QTimer(self)
        timer.timeout.connect(self._update_status)
        timer.start(1000)
        self._status_timer = timer
        self._update_status()

    def _update_status(self) -> None:
        self.clock_label.setText(datetime.now().strftime("%H:%M:%S"))
        self.metrics_label.setText(
            f"CPU {psutil.cpu_percent():.0f} %  ·  RAM {psutil.virtual_memory().percent:.0f} %"
        )

    @Slot()
    def submit_text(self) -> None:
        text = self.input_edit.text().strip()
        if not text:
            return
        self.input_edit.clear()
        self._submit(text)

    def _submit(self, text: str) -> None:
        self.transcription_label.setText(text)
        self.input_edit.setEnabled(False)
        future = self.executor.submit(asyncio.run, self.assistant.handle(text))
        future.add_done_callback(lambda item: self._assistant_done(text, item))

    def _assistant_done(self, user_text: str, future: Future[str]) -> None:
        try:
            self.bridge.answer_ready.emit(user_text, future.result())
        except Exception as exc:
            LOGGER.exception("Assistant request failed")
            self.bridge.error.emit(f"La demande a échoué : {exc}")

    @Slot(str, str)
    def _show_answer(self, user_text: str, answer: str) -> None:
        self.answer_label.setText(answer)
        self.history_list.addItem(f"Toi · {user_text}")
        self.history_list.addItem(f"{self.settings.assistant_name} · {answer}")
        self.history_list.scrollToBottom()
        self.database.save_conversation("user", user_text)
        self.database.save_conversation("assistant", answer)
        self.input_edit.setEnabled(True)
        self.input_edit.setFocus()
        if self.settings.enable_tts:
            self.executor.submit(asyncio.run, self.tts.speak(answer))
        QTimer.singleShot(900, lambda: self.set_state(AssistantState.IDLE))

    @Slot()
    def toggle_recording(self) -> None:
        if self.recorder.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self) -> None:
        try:
            self.recorder.start()
            self.mic_button.setProperty("recording", True)
            self.mic_button.style().unpolish(self.mic_button)
            self.mic_button.style().polish(self.mic_button)
            self.mic_button.setText("■")
            self.mic_status.setText("● Enregistrement")
            self.set_state(AssistantState.LISTENING)
            self.transcription_label.setText("Je t’écoute… Clique à nouveau pour terminer.")
        except Exception as exc:
            LOGGER.exception("Microphone start failed")
            self._show_error(f"Microphone indisponible : {exc}")

    def _stop_recording(self) -> None:
        try:
            audio = self.recorder.stop()
            self.mic_button.setProperty("recording", False)
            self.mic_button.style().unpolish(self.mic_button)
            self.mic_button.style().polish(self.mic_button)
            self.mic_button.setText("●")
            self.mic_status.setText("● Micro prêt")
            self.set_state(AssistantState.ANALYZING)
            self.transcription_label.setText("Transcription en cours…")
            future = self.executor.submit(asyncio.run, self.stt.transcribe(audio))
            future.add_done_callback(self._transcription_done)
        except Exception as exc:
            LOGGER.exception("Microphone stop failed")
            self._show_error(f"Impossible de terminer l’enregistrement : {exc}")

    def _transcription_done(self, future: Future[str]) -> None:
        try:
            text = future.result().strip()
            if not text:
                self.bridge.error.emit("Je n’ai rien entendu.")
                return
            self._submit_from_signal(text)
        except Exception as exc:
            LOGGER.exception("Transcription failed")
            self.bridge.error.emit(str(exc))

    def _submit_from_signal(self, text: str) -> None:
        self.bridge.transcription_ready.emit(text)

    @Slot(str)
    def _on_transcription(self, text: str) -> None:
        self._submit(text)

    @Slot(object)
    def set_state(self, state: AssistantState) -> None:
        self.state_label.setText(state.value)
        self.orb.set_state(state)

    @Slot(str)
    def _show_error(self, message: str) -> None:
        self.set_state(AssistantState.ERROR)
        self.answer_label.setText(message)
        self.input_edit.setEnabled(True)
        QTimer.singleShot(1800, lambda: self.set_state(AssistantState.IDLE))

    @Slot()
    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.title_label.setText(self.settings.assistant_name.upper())
            self.tts = WindowsTextToSpeech(
                self.settings.tts_rate, self.settings.tts_volume, self.settings.language
            )

    def show_onboarding_if_needed(self) -> None:
        if self.database.get_setting("onboarding_complete") == "true":
            return
        dialog = OnboardingDialog(self.settings, self.tts, self.executor, self)
        if dialog.exec():
            self.database.set_setting("onboarding_complete", "true")

    def _restore(self) -> None:
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.settings.minimize_to_tray and not self._really_quit:
            event.ignore()
            self.hide()
            self.tray.showMessage(
                self.settings.assistant_name,
                "L’assistant continue de fonctionner dans la zone de notification.",
                QSystemTrayIcon.Information,
                2500,
            )
            return
        event.accept()
        QTimer.singleShot(0, self.quit_application)

    def quit_application(self) -> None:
        if self._really_quit:
            QApplication.quit()
            return
        self._really_quit = True
        self.hotkey.stop()
        if self.recorder.is_recording:
            self.recorder.stop()
        self.executor.shutdown(wait=False, cancel_futures=True)
        QApplication.quit()
