"""Convert a recorded voice question into text using OpenAI's audio API."""

import requests

from src.core.config import option


MAX_RECORDING_BYTES = 25_000_000


def transcribe_question(audio: bytes) -> str:
    api_key = option("openai_api_key", "").strip()
    if not api_key:
        raise ValueError("Set OPENAI_API_KEY to enable voice questions.")
    if not audio or len(audio) > MAX_RECORDING_BYTES:
        raise ValueError("Record a question with audio under 25 MB.")

    try:
        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": ("question.wav", audio, "audio/wav")},
            data={"model": option("openai_transcription_model", "whisper-1")},
            timeout=(5, 45),
        )
        response.raise_for_status()
        result = response.json()
    except (requests.RequestException, ValueError):
        raise ValueError("Couldn't transcribe the recording. Try again or type your question.") from None

    transcript = result.get("text") if isinstance(result, dict) else None
    if not isinstance(transcript, str) or not transcript.strip():
        raise ValueError("No speech was transcribed. Try recording your question again.")
    return transcript.strip()
