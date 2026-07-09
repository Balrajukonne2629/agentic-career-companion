"""
app.py
======
Main Flask application factory for the Agentic Career Counseling Companion.

Responsibilities
----------------
- Initialise Flask with CORS, session, and error handler configuration.
- Register all route blueprints.
- Register global exception handlers (typed AppError subclasses).
- Serve the built React frontend from /static/ for all non-API routes
  (enables IBM Cloud Foundry deployment without a separate static file server).

Application startup sequence
-----------------------------
1. config.py loads and validates all environment variables.
2. logger.py configures the root logger.
3. Flask app is created and configured.
4. Blueprints are registered.
5. Error handlers are registered.
6. career_data.json is loaded eagerly to fail fast on startup if corrupt.

Running locally
---------------
    cd backend
    python app.py

Running via gunicorn (production / Cloud Foundry)
--------------------------------------------------
    gunicorn app:app
"""

import os
from datetime import timedelta

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from config import config
from errors import AppError
from logger import get_logger
from routes.health   import health_bp
from routes.pipeline import pipeline_bp
from routes.stt      import stt_bp

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> Flask:
    """
    Create and configure the Flask application.

    Returns
    -------
    Flask
        Configured Flask application instance.
    """
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
        static_url_path="",
    )

    # -------------------------------------------------------------------
    # Core configuration
    # -------------------------------------------------------------------
    app.config["SECRET_KEY"] = config.FLASK_SECRET_KEY
    app.config["DEBUG"] = config.DEBUG
    app.config["SESSION_COOKIE_SAMESITE"] = config.SESSION_COOKIE_SAMESITE
    # SameSite=None requires Secure=True. Otherwise, use HTTPS in production.
    if config.SESSION_COOKIE_SAMESITE.lower() == "none":
        app.config["SESSION_COOKIE_SECURE"] = True
    else:
        app.config["SESSION_COOKIE_SECURE"] = not config.DEBUG
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
        seconds=config.SESSION_LIFETIME_SECONDS
    )

    # -------------------------------------------------------------------
    # CORS — allow React dev server and dynamic frontend origins
    # -------------------------------------------------------------------
    cors_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://agentic-career-companion.vercel.app",
    ]
    if config.FRONTEND_URL and config.FRONTEND_URL not in cors_origins:
        cors_origins.append(config.FRONTEND_URL)

    CORS(
        app,
        origins=cors_origins,
        supports_credentials=True,    # Required for session cookies
    )

    # -------------------------------------------------------------------
    # Blueprint registration — all API routes under /api prefix
    # -------------------------------------------------------------------
    app.register_blueprint(health_bp,   url_prefix="/api")
    app.register_blueprint(pipeline_bp, url_prefix="/api")
    app.register_blueprint(stt_bp,      url_prefix="/api")

    # -------------------------------------------------------------------
    # Global error handlers — return consistent JSON error envelopes
    # -------------------------------------------------------------------

    @app.errorhandler(AppError)
    def handle_app_error(exc: AppError):
        """Convert typed AppError subclasses to JSON responses."""
        log.error("AppError [%d]: %s | detail=%s", exc.status_code, exc.message, exc.detail)
        return jsonify(exc.to_dict()), exc.status_code

    @app.errorhandler(404)
    def handle_404(exc):
        """Return JSON 404 for API routes; fall through to React for others."""
        return jsonify({"error": True, "message": "Endpoint not found."}), 404

    @app.errorhandler(405)
    def handle_405(exc):
        return jsonify({"error": True, "message": "Method not allowed."}), 405

    @app.errorhandler(500)
    def handle_500(exc):
        log.exception("Unhandled internal server error")
        return jsonify({
            "error": True,
            "message": "An unexpected error occurred. Please try again.",
        }), 500

    # -------------------------------------------------------------------
    # Serve React build for all non-API routes (Cloud Foundry deployment)
    # -------------------------------------------------------------------

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_react(path: str):
        """
        Serve the React SPA.

        - If the path matches a real file in /static/, serve it directly
          (JS bundles, CSS, images, favicon, etc.).
        - For all other paths (React Router client-side routes), serve
          index.html and let React Router handle navigation.
        """
        static_folder = app.static_folder
        if static_folder and path:
            target = os.path.join(static_folder, path)
            if os.path.isfile(target):
                return send_from_directory(static_folder, path)
        if static_folder and os.path.isfile(os.path.join(static_folder, "index.html")):
            return send_from_directory(static_folder, "index.html")
        return jsonify({
            "message": (
                "Agentic Career Counseling Companion API. "
                "React frontend not yet built. "
                "Run 'npm run build' in /frontend and copy output to /backend/static/."
            )
        }), 200

    # -------------------------------------------------------------------
    # Eager knowledge base load — fail fast if career_data.json is corrupt
    # -------------------------------------------------------------------
    with app.app_context():
        try:
            from utils.career_loader import get_all_careers
            careers = get_all_careers()
            log.info("Startup: knowledge base loaded (%d careers)", len(careers))
        except Exception as exc:
            log.error("Startup: FAILED to load knowledge base — %s", exc)
            # Do not crash the app — health check will report the error

    log.info(
        "Flask app created | env=%s | debug=%s | stt=%s",
        config.FLASK_ENV,
        config.DEBUG,
        "available" if config.WATSON_STT_AVAILABLE else "not configured",
    )
    return app


# ---------------------------------------------------------------------------
# Entry point — development server only
# ---------------------------------------------------------------------------

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=config.DEBUG,
    )
