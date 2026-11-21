"""
config.py
=========
Centralised configuration loader for the Agentic Career Counseling Companion.

Loads all required environment variables from .env at startup.
Raises a clear, descriptive error for any missing required variable so that
the failure is detected immediately on startup rather than silently at runtime
inside an agent call.

Usage
-----
    from config import Config
    cfg = Config()
    api_key = cfg.IBM_API_KEY
"""

import os
from dotenv import load_dotenv

# Load .env file values into the process environment.
# Silent if .env is absent (Cloud Foundry sets vars directly in the environment).
load_dotenv()


class ConfigurationError(Exception):
    """Raised when a required environment variable is missing."""


DEFAULT_CORS_ORIGINS: list[str] = [
    "https://agentic-career-companion.balrajukonne.cv",
    "https://agentic-career-companion.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
]


def parse_cors_origins(raw: str | None) -> list[str]:
    """
    Parse comma-separated CORS origins from environment variable.
    Trims whitespace and strips any trailing slashes.
    Ignores empty items.
    Falls back to DEFAULT_CORS_ORIGINS if raw is empty or None.
    """
    if not raw:
        return list(DEFAULT_CORS_ORIGINS)
    origins = [item.strip().rstrip("/") for item in raw.split(",") if item.strip()]
    return origins if origins else list(DEFAULT_CORS_ORIGINS)


class Config:
    """
    Immutable application configuration resolved from environment variables.

    All attributes are set once in __init__ and never mutated.
    Agents and utilities import a single shared instance from this module
    (see bottom of file).
    """

    # ------------------------------------------------------------------
    # Required variables — startup fails if any of these are absent.
    # ------------------------------------------------------------------
    REQUIRED_VARS = [
        "IBM_API_KEY",
        "IBM_PROJECT_ID",
        "IBM_WATSONX_URL",
        "FLASK_SECRET_KEY",
    ]

    def __init__(self):
        self._validate_required()

        # IBM watsonx.ai
        self.IBM_API_KEY: str = os.environ["IBM_API_KEY"]
        self.IBM_PROJECT_ID: str = os.environ["IBM_PROJECT_ID"]
        self.IBM_WATSONX_URL: str = os.environ["IBM_WATSONX_URL"]

        # IBM Watson STT (optional — fallback only)
        self.WATSON_STT_API_KEY: str = os.environ.get("WATSON_STT_API_KEY", "")
        self.WATSON_STT_URL: str = os.environ.get(
            "WATSON_STT_URL",
            "https://api.us-south.speech-to-text.watson.cloud.ibm.com",
        )
        self.WATSON_STT_AVAILABLE: bool = bool(self.WATSON_STT_API_KEY)

        # Flask
        self.FLASK_SECRET_KEY: str = os.environ["FLASK_SECRET_KEY"]
        self.FLASK_ENV: str = os.environ.get("FLASK_ENV", "production")
        self.DEBUG: bool = self.FLASK_ENV == "development"

        # Frontend URLs & CORS allowed origins
        self.CORS_ORIGINS: list[str] = parse_cors_origins(os.environ.get("CORS_ORIGINS"))
        self.FRONTEND_URL: str = os.environ.get(
            "FRONTEND_URL", "https://agentic-career-companion.balrajukonne.cv"
        )
        if self.FRONTEND_URL:
            trimmed_frontend = self.FRONTEND_URL.strip().rstrip("/")
            if trimmed_frontend and trimmed_frontend not in self.CORS_ORIGINS:
                self.CORS_ORIGINS.append(trimmed_frontend)

        # Session config
        is_production = self.FLASK_ENV == "production" and not self.DEBUG
        default_samesite = "None" if is_production else "Lax"
        self.SESSION_COOKIE_SAMESITE: str = os.environ.get(
            "SESSION_COOKIE_SAMESITE", default_samesite
        )
        self.SESSION_LIFETIME_SECONDS: int = int(
            os.environ.get("SESSION_LIFETIME_SECONDS", "3600")
        )

        # Logging
        self.LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").upper()

        # Granite model identifiers
        self.GRANITE_FAST_MODEL: str = "ibm/granite-4-h-small"
        self.GRANITE_STRONG_MODEL: str = "ibm/granite-4-h-small"

        # Knowledge base path
        self.CAREER_DATA_PATH: str = os.path.join(
            os.path.dirname(__file__), "data", "career_data.json"
        )

    def _validate_required(self) -> None:
        """Raise ConfigurationError listing ALL missing required variables."""
        missing = [v for v in self.REQUIRED_VARS if not os.environ.get(v)]
        if missing:
            raise ConfigurationError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Copy .env.example to .env and populate the missing values."
            )

    def __repr__(self) -> str:
        return (
            f"Config(env={self.FLASK_ENV}, "
            f"watsonx_url={self.IBM_WATSONX_URL}, "
            f"cors_origins={self.CORS_ORIGINS}, "
            f"stt_available={self.WATSON_STT_AVAILABLE})"
        )


# ---------------------------------------------------------------------------
# Shared singleton — import this everywhere instead of constructing Config().
# ---------------------------------------------------------------------------
config = Config()
