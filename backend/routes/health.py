"""
routes/health.py
================
Health check endpoint.

GET /api/health
    Verifies that:
    - The Flask application is running.
    - career_data.json can be loaded.
    - Both Granite models respond to a minimal test prompt.
    - Watson STT service status is reported (available / not configured).

This is the first endpoint to call after deployment or after any config
change. If /api/health returns HTTP 200 with both Granite checks passing,
the full pipeline will work.

Do NOT call /api/health in production automatically — each call consumes
IBM watsonx.ai token quota. Use it manually to verify new deployments.
"""

from flask import Blueprint, jsonify

from utils.career_loader import get_all_careers
from utils.granite_client import call_granite_fast, call_granite_strong
from config import config
from errors import AppError
from logger import get_logger

log = get_logger(__name__)
health_bp = Blueprint("health", __name__)

_HEALTH_PROMPT = (
    "Respond with exactly the following JSON and nothing else: "
    '{"status": "ok"}'
)


@health_bp.route("/health", methods=["GET"])
def health():
    """
    Comprehensive health check.

    Returns
    -------
    200 OK
        All checks passed. Body contains per-component status.
    207 Multi-Status
        Application is running but one or more optional checks failed.
    500 Internal Server Error
        A critical check (knowledge base or required config) failed.
    """
    result = {
        "application": "Agentic Career Counseling Companion",
        "schema_version": config.GRANITE_FAST_MODEL,  # sanity check config loads
        "checks": {}
    }

    # -----------------------------------------------------------------------
    # Check 1 — Knowledge base
    # -----------------------------------------------------------------------
    try:
        careers = get_all_careers()
        result["checks"]["knowledge_base"] = {
            "status": "ok",
            "careers_loaded": len(careers),
        }
    except AppError as exc:
        result["checks"]["knowledge_base"] = {
            "status": "error",
            "message": exc.message,
        }
        return jsonify(result), 500

    # -----------------------------------------------------------------------
    # Check 2 — Granite fast model (granite-3-8b-instruct)
    # -----------------------------------------------------------------------
    try:
        response = call_granite_fast(_HEALTH_PROMPT)
        result["checks"]["granite_fast"] = {
            "status": "ok",
            "model": config.GRANITE_FAST_MODEL,
            "response_chars": len(response),
        }
    except AppError as exc:
        result["checks"]["granite_fast"] = {
            "status": "error",
            "model": config.GRANITE_FAST_MODEL,
            "message": exc.message,
        }

    # -----------------------------------------------------------------------
    # Check 3 — Granite strong model (granite-13b-instruct-v2)
    # -----------------------------------------------------------------------
    try:
        response = call_granite_strong(_HEALTH_PROMPT)
        result["checks"]["granite_strong"] = {
            "status": "ok",
            "model": config.GRANITE_STRONG_MODEL,
            "response_chars": len(response),
        }
    except AppError as exc:
        result["checks"]["granite_strong"] = {
            "status": "error",
            "model": config.GRANITE_STRONG_MODEL,
            "message": exc.message,
        }

    # -----------------------------------------------------------------------
    # Check 4 — Watson STT (informational — not required for pipeline)
    # -----------------------------------------------------------------------
    result["checks"]["watson_stt"] = {
        "status": "available" if config.WATSON_STT_AVAILABLE else "not_configured",
        "note": (
            "STT fallback is active."
            if config.WATSON_STT_AVAILABLE
            else "WATSON_STT_API_KEY not set. Browser Web Speech API will be used."
        ),
    }

    # Determine overall HTTP status
    granite_checks = [
        result["checks"].get("granite_fast", {}).get("status"),
        result["checks"].get("granite_strong", {}).get("status"),
    ]
    all_ok = all(s == "ok" for s in granite_checks)
    http_status = 200 if all_ok else 207

    log.info(
        "/api/health → %d | KB=%s | fast=%s | strong=%s",
        http_status,
        result["checks"]["knowledge_base"].get("status"),
        result["checks"].get("granite_fast", {}).get("status"),
        result["checks"].get("granite_strong", {}).get("status"),
    )

    return jsonify(result), http_status
