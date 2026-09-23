from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout,
)

from app.core.config import Settings
from app.voice.microphone import MicrophoneRecorder
from app.voice.text_to_speech import TextToSpeechProvider


class OnboardingDialog(QDialog):
    completed = Signal()

    def __init__(
        self,
        settings: Settings,
        tts: TextToSpeechProvider,
        executor: ThreadPoolExecutor,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.settings = settings
        self.tts = tts
        self.executor = executor
        self.setWindowTitle(f"Bienvenue dans {settings.assistant_name}")
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        title = QLabel("Bonjour.\n\nJe suis ton nouvel assistant personnel.")
        title.setObjectName("title")
        layout.addWidget(title)
        layout.addWidget(
            QLabel(
                "Avant de commencer, vérifions rapidement le microphone, "
                "les haut-parleurs et la configuration de l’intelligence artificielle."
            )
        )
        tests = QHBoxLayout()
        mic = QPushButton("Tester le microphone")
        speaker = QPushButton("Tester le haut-parleur")
        ai = QPushButton("Tester la connexion IA")
        mic.clicked.connect(self._test_microphone)
        speaker.clicked.connect(self._test_speaker)
        ai.clicked.connect(self._test_ai)
        tests.addWidget(mic)
        tests.addWidget(speaker)
        tests.addWidget(ai)
        layout.addLayout(tests)
        continue_button = QPushButton("Assistant prêt")
        continue_button.clicked.connect(self.accept)
        layout.addWidget(continue_button)

    def _test_microphone(self) -> None:
        try:
            devices = MicrophoneRecorder.devices()
            message = f"{len(devices)} entrée(s) audio détectée(s)." if devices else "Aucune entrée audio détectée."
            QMessageBox.information(self, "Microphone", message)
        except Exception as exc:
            QMessageBox.warning(self, "Microphone", f"Microphone indisponible : {exc}")

    def _test_speaker(self) -> None:
        self.executor.submit(asyncio.run, self.tts.speak("Test audio. Le haut-parleur fonctionne."))
        QMessageBox.information(self, "Haut-parleur", "Le message de test a été envoyé.")

    def _test_ai(self) -> None:
        if self.settings.ai_configured:
            QMessageBox.information(self, "Intelligence artificielle", "La clé API est configurée.")
        else:
            QMessageBox.warning(
                self,
                "Intelligence artificielle",
                "Aucune clé API n’est configurée. Les commandes locales restent disponibles.",
            )

