"""Streamlit chat composer with a microphone and editable transcription."""

from base64 import b64decode
from binascii import Error
from pathlib import Path
from uuid import uuid4

import streamlit as st

from src.core.config import option
from src.core.transcription import MAX_RECORDING_BYTES, transcribe_question

ASSETS = Path(__file__).parent
COMPOSER_KEY = "finnie_chat_composer"

composer = st.components.v2.component(
    "finnie_chat_composer",
    html=(ASSETS / "composer.html").read_text(encoding="utf-8"),
    css=(ASSETS / "composer.css").read_text(encoding="utf-8"),
    js=(ASSETS / "composer.js").read_text(encoding="utf-8"),
)


def transcription_result(recording):
    """Handle a recording event once and return an editable draft or a status message."""
    result = {"id": str(uuid4())}
    try:
        encoded = recording["audio"]
        mime = recording["mime"]
        if not isinstance(encoded, str) or not isinstance(mime, str):
            raise ValueError("Couldn't read the recording. Try again.")
        if len(encoded) > 4 * ((MAX_RECORDING_BYTES + 2) // 3):
            raise ValueError("Record a question with audio under 25 MB.")
        audio = b64decode(encoded, validate=True)
    except (KeyError, TypeError, Error):
        result["error"] = "Couldn't read the recording. Try again."
    except ValueError as exc:
        result["error"] = str(exc)
    else:
        try:
            result["text"] = transcribe_question(audio, mime)
        except ValueError as exc:
            result["error"] = str(exc)
    return result


def clear_chat_composer():
    st.session_state.pop("chat_transcription", None)
    st.session_state.chat_composer_version = st.session_state.get("chat_composer_version", 0) + 1


def _receive_recording(key):
    recording = st.session_state[key].recording
    if recording is not None:
        st.session_state.chat_transcription = transcription_result(recording)


def chat_question():
    if not option("openai_api_key", "").strip():
        return st.chat_input("Ask Finnie a question…")

    # The callback runs before rendering, so the transcript returns on the same rerun.
    key = f"{COMPOSER_KEY}_{st.session_state.get('chat_composer_version', 0)}"
    result = composer(
        key=key,
        data={"result": st.session_state.get("chat_transcription")},
        on_recording_change=lambda: _receive_recording(key),
        on_question_change=lambda: None,
    )
    if isinstance(result.question, str) and result.question.strip():
        clear_chat_composer()
        return result.question.strip()
    return None
