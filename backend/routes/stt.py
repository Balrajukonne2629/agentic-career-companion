"""
routes/stt.py
=============
Speech-To-Text fallback endpoint.

POST /api/stt
    Accepts a raw audio file uploaded from the browser MediaRecorder API
    when the Web Speech API is unavailable. Transcribes via IBM Watson STT
    and returns the transcript text.

Request
-------
    Content-Type : audio/wav | audio/webm | audio/flac | audio/ogg
    Body         : raw audio bytes (max 10 MB)

Response 200
------------
    { "transcript": "..." }

Response 503
------------
    { "error": true, "message": "Watson STT is not configured." }
    Returned when WATSON_STT_API_KEY is absent from environment.
    The frontend should fall back to the text-input path.
"""

from flask import Blueprint, request, jsonify

from utils.watson_stt import transcribe_audio
from config import config
from errors import AppError
from logger import get_logger

log = get_logger(__name__)
stt_bp = Blueprint("stt", __name__)

MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10 MB


@stt_bp.route("/stt", methods=["POST"])
def stt():
    """
    Transcribe audio to text using IBM Watson STT.

    Returns
    -------
    200 : { "transcript": str }
    400 : { "error": true, "message": "..." }   — missing or oversized audio
    503 : { "error": true, "message": "..." }   — Watson STT not configured
    502 : { "error": true, "message": "..." }   — Watson STT API failure
    """
    if not config.WATSON_STT_AVAILABLE:
        return jsonify({
            "error": True,
            "message": (
                "Watson STT is not configured on this deployment. "
                "Please use the text input field or a browser that supports "
                "the Web Speech API (Chrome, Edge)."
            ),
        }), 503

    audio_bytes = request.get_data()
    if not audio_bytes:
        return jsonify({
            "error": True,
            "message": "No audio data received. Please try again.",
        }), 400

    if len(audio_bytes) > MAX_AUDIO_BYTES:
        return jsonify({
            "error": True,
            "message": (
                f"Audio file too large ({len(audio_bytes) // 1024} KB). "
                f"Maximum allowed size is {MAX_AUDIO_BYTES // 1024 // 1024} MB."
            ),
        }), 400

    content_type = request.content_type or "audio/wav"

    try:
        transcript = transcribe_audio(audio_bytes, content_type=content_type)
        log.info("/api/stt → transcript chars=%d", len(transcript))
        return jsonify({"transcript": transcript}), 200

    except AppError as exc:
        log.error("/api/stt error: %s", exc.message)
        return jsonify(exc.to_dict()), exc.status_code
