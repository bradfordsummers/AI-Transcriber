"""
recorder.py — Audio recording module using sounddevice.

Records 16 kHz mono 16-bit PCM audio in a background thread and saves to a
temporary WAV file when stopped.
"""

import os
import tempfile
import threading

import numpy as np
import sounddevice as sd
from scipy.io import wavfile

SAMPLE_RATE = 16_000  # 16 kHz — optimal for speech / Whisper
CHANNELS = 1          # Mono
DTYPE = "int16"       # 16-bit PCM


class Recorder:
    """Records audio from the default input device in a background thread."""

    def __init__(self) -> None:
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self.is_recording = False
        self.last_file: str | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start recording audio in a background thread."""
        if self.is_recording:
            return

        self._frames = []
        self._stop_event.clear()
        self.is_recording = True

        self._thread = threading.Thread(target=self._record, daemon=True)
        self._thread.start()

    def stop(self) -> str | None:
        """Stop recording and save to a temp WAV file.

        Returns the path to the saved WAV file, or None on failure.
        """
        if not self.is_recording:
            return None

        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
        self.is_recording = False

        return self._save()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _record(self) -> None:
        """Background recording loop using sounddevice InputStream."""
        try:
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=1024,
                callback=self._audio_callback,
            )
            self._stream.start()

            # Block until stop is signalled
            self._stop_event.wait()

            self._stream.stop()
            self._stream.close()
            self._stream = None
        except Exception as exc:
            print(f"[recorder] Error during recording: {exc}")
            self.is_recording = False

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info,  # noqa: ANN001
        status: sd.CallbackFlags,
    ) -> None:
        """Called by sounddevice for each audio block."""
        if status:
            print(f"[recorder] sounddevice status: {status}")
        with self._lock:
            self._frames.append(indata.copy())

    def _save(self) -> str | None:
        """Concatenate recorded frames and write to a temp WAV file."""
        with self._lock:
            if not self._frames:
                return None
            audio_data = np.concatenate(self._frames, axis=0)

        try:
            fd, path = tempfile.mkstemp(suffix=".wav", prefix="transcriber_")
            os.close(fd)
            wavfile.write(path, SAMPLE_RATE, audio_data)
            self.last_file = path
            return path
        except Exception as exc:
            print(f"[recorder] Error saving WAV: {exc}")
            return None
