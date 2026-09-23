from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel,
    QLineEdit, QSlider, QSpinBox, QTabWidget, QVBoxLayout, QWidget,
)

from app.core.config import Settings


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Paramètres")
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.addTab(self._general_tab(), "Général")
        tabs.addTab(self._voice_tab(), "Voix")
        tabs.addTab(self._microphone_tab(), "Microphone")
        tabs.addTab(self._ai_tab(), "IA")
        layout.addWidget(tabs)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _general_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        self.name_edit = QLineEdit(self.settings.assistant_name)
        self.language_combo = QComboBox()
        self.language_combo.addItems(["fr-FR", "en-US"])
        self.language_combo.setCurrentText(self.settings.language)
        self.tray_check = QCheckBox("Réduire dans la zone de notification")
        self.tray_check.setChecked(self.settings.minimize_to_tray)
        self.startup_check = QCheckBox("Démarrer avec Windows (prévu après la V1)")
        self.startup_check.setEnabled(False)
        form.addRow("Nom", self.name_edit)
        form.addRow("Langue", self.language_combo)
        form.addRow(self.tray_check)
        form.addRow(self.startup_check)
        return page

    def _voice_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        self.tts_check = QCheckBox("Activer les réponses vocales")
        self.tts_check.setChecked(self.settings.enable_tts)
        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(100, 300)
        self.rate_spin.setValue(self.settings.tts_rate)
        self.tts_volume = QSlider(Qt.Horizontal)
        self.tts_volume.setRange(0, 100)
        self.tts_volume.setValue(round(self.settings.tts_volume * 100))
        form.addRow(self.tts_check)
        form.addRow("Vitesse", self.rate_spin)
        form.addRow("Volume", self.tts_volume)
        return page

    def _microphone_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        self.mic_combo = QComboBox()
        self.mic_combo.addItem("Périphérique Windows par défaut")
        self.sensitivity = QSlider(Qt.Horizontal)
        self.sensitivity.setRange(0, 100)
        self.sensitivity.setValue(50)
        form.addRow("Entrée", self.mic_combo)
        form.addRow("Sensibilité", self.sensitivity)
        form.addRow(QLabel("Le choix avancé du périphérique sera persisté dans une version future."))
        return page

    def _ai_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        model = QLineEdit(self.settings.openai_model)
        model.setReadOnly(True)
        status = QLabel("Connectée" if self.settings.ai_configured else "Clé absente dans .env")
        status.setObjectName("good" if self.settings.ai_configured else "bad")
        key = QLabel("••••••••" if self.settings.ai_configured else "Non configurée")
        form.addRow("Modèle", model)
        form.addRow("État API", status)
        form.addRow("Clé", key)
        return page

    def _save(self) -> None:
        self.settings.assistant_name = self.name_edit.text().strip() or "Jarvis"
        self.settings.language = self.language_combo.currentText()
        self.settings.minimize_to_tray = self.tray_check.isChecked()
        self.settings.enable_tts = self.tts_check.isChecked()
        self.settings.tts_rate = self.rate_spin.value()
        self.settings.tts_volume = self.tts_volume.value() / 100
        self.accept()

