from __future__ import annotations

import io
import logging
import threading
import wave

import numpy as np
import sounddevice as sd


LOGGER = logging.getLogger(__name__)


class MicrophoneRecorder:
    def __init__(self, sample_rate: int = 16_000, device: int | None = None) -> None:
        self.sample_rate = sample_rate
        self.device = device
        self._chunks: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()

    @property
    def is_recording(self) -> bool:
        return self._stream is not None

    def start(self) -> None:
        if self.is_recording:
            return
        self._chunks = []

        def callback(indata, _frames, _time, status) -> None:
            if status:
                LOGGER.warning("Microphone status: %s", status)
            with self._lock:
                self._chunks.append(indata.copy())

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            device=self.device,
            callback=callback,
        )
        self._stream.start()
        LOGGER.info("Microphone recording started")

    def stop(self) -> bytes:
        if self._stream is None:
            return b""
        stream, self._stream = self._stream, None
        stream.stop()
        stream.close()
        with self._lock:
            audio = np.concatenate(self._chunks, axis=0) if self._chunks else np.empty((0, 1), dtype=np.int16)
            self._chunks = []
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio.tobytes())
        LOGGER.info("Microphone recording stopped")
        return buffer.getvalue()

    @staticmethod
    def devices() -> list[str]:
        return [
            f"{index}: {device['name']}"
            for index, device in enumerate(sd.query_devices())
            if int(device["max_input_channels"]) > 0
        ]

