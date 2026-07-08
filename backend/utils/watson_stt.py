"""
utils/watson_stt.py
===================
IBM Watson Speech-To-Text fallback client.

Used only when the browser's Web Speech API is unavailable.
The frontend records audio as a WAV/FLAC blob and POSTs it to
/api/stt, which calls transcribe_audio() here.

Availability guard
------------------
If WATSON_STT_API_KEY is absent, WATSON_STT_AVAILABLE is False in config.py
and the /api/stt route returns a 503 with a clear message rather than a
crash. The frontend displays the text-input fallback in that case.
"""

from typing import Any

from config import config
from errors import GraniteCallError
from logger import get_logger

log = get_logger(__name__)

_stt_client: Any = None


def _get_stt_client() -> Any:
    """Return the shared Watson STT client, initialising on first call."""
    global _stt_client
    if _stt_client is not None:
        return _stt_client

    try:
        from ibm_watson import SpeechToTextV1
        from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

        authenticator = IAMAuthenticator(config.WATSON_STT_API_KEY)
        client = SpeechToTextV1(authenticator=authenticator)
        client.set_service_url(config.WATSON_STT_URL)
        _stt_client = client
        log.info("Watson STT client initialised (url=%s)", config.WATSON_STT_URL)
        return _stt_client
    except Exception as exc:
        raise GraniteCallError(
            "Failed to initialise Watson Speech-To-Text client.",
            detail=str(exc),
        ) from exc


def transcribe_audio(audio_bytes: bytes, content_type: str = "audio/wav") -> str:
    """
    Transcribe audio bytes to text using IBM Watson STT.

    Parameters
    ----------
    audio_bytes : bytes
        Raw audio content from the browser MediaRecorder.
    content_type : str
        MIME type of the audio. Defaults to "audio/wav".
        Also accepts "audio/webm", "audio/flac", "audio/ogg".

    Returns
    -------
    str
        Transcribed text, stripped of leading/trailing whitespace.

    Raises
    ------
    GraniteCallError
        If the Watson STT API call fails or returns no transcript.
    """
    if not config.WATSON_STT_AVAILABLE:
        raise GraniteCallError(
            "Watson STT is not configured. "
            "Set WATSON_STT_API_KEY and WATSON_STT_URL in your .env file."
        )

    try:
        client = _get_stt_client()
        result = client.recognize(
            audio=audio_bytes,
            content_type=content_type,
            model="en-US_BroadbandModel",
        ).get_result()

        results = result.get("results", [])
        if not results:
            raise GraniteCallError(
                "Watson STT returned no transcription results. "
                "Audio may be too short, silent, or in an unsupported format."
            )

        transcript = results[0]["alternatives"][0]["transcript"].strip()
        log.info("Watson STT transcript (chars=%d)", len(transcript))
        return transcript

    except GraniteCallError:
        raise
    except Exception as exc:
        raise GraniteCallError(
            "Watson STT transcription failed unexpectedly.",
            detail=str(exc),
        ) from exc
