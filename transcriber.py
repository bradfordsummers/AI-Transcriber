"""
transcriber.py — Sends audio files to a Whisper-compatible API for transcription.

Supports both OpenAI and OpenRouter as API providers.
Runs the API call in a background thread so the GUI stays responsive.
"""

import os
import threading
from typing import Callable

from openai import OpenAI

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def transcribe(
    file_path: str,
    api_key: str,
    on_success: Callable[[str], None],
    on_error: Callable[[str], None],
    api_provider: str = "OpenAI",
) -> None:
    """Transcribe an audio file via Whisper API in a background thread.

    Parameters
    ----------
    file_path : str
        Path to the .wav file to transcribe.
    api_key : str
        API key for the chosen provider.
    on_success : callable
        Called with the transcription text on success.
    on_error : callable
        Called with an error message string on failure.
    api_provider : str
        "OpenAI" or "OpenRouter".
    """
    thread = threading.Thread(
        target=_do_transcribe,
        args=(file_path, api_key, on_success, on_error, api_provider),
        daemon=True,
    )
    thread.start()


def _do_transcribe(
    file_path: str,
    api_key: str,
    on_success: Callable[[str], None],
    on_error: Callable[[str], None],
    api_provider: str = "OpenAI",
) -> None:
    """Internal: perform the actual API call (runs in a thread)."""
    try:
        if not api_key:
            on_error(f"No API key provided. Please enter your {api_provider} API key.")
            return

        if not os.path.exists(file_path):
            on_error(f"Audio file not found: {file_path}")
            return

        if api_provider == "OpenRouter":
            client = OpenAI(
                api_key=api_key,
                base_url=OPENROUTER_BASE_URL,
            )
        else:
            client = OpenAI(api_key=api_key)

        with open(file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
            )

        # response is a plain string when response_format="text"
        text = str(response).strip()
        on_success(text)

    except Exception as exc:
        on_error(f"Transcription error: {exc}")

    finally:
        # Clean up the temp audio file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass
