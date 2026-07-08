"""
errors.py
=========
Application-wide exception classes and a centralised error-response builder.

Design principles
-----------------
- Every agent raises a typed exception from this module.
- The Flask error handlers in app.py convert these into consistent JSON
  responses without leaking stack traces to the client.
- HTTP status codes are embedded in the exception, not scattered across routes.

Exception hierarchy
-------------------
    AppError (base)
    ├── ConfigurationError    — missing env vars, bad config (500)
    ├── KnowledgeBaseError    — career_data.json load / parse failure (500)
    ├── GraniteCallError      — IBM watsonx.ai API failure (502)
    ├── GraniteParseError     — Granite returned unparseable JSON (502)
    ├── ValidationError       — agent input validation failed (400)
    └── SessionError          — Flask session missing expected key (400)
"""

from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Base exception
# ---------------------------------------------------------------------------

class AppError(Exception):
    """
    Base class for all application-level exceptions.

    Parameters
    ----------
    message : str
        Human-readable error description (safe to return to the client).
    status_code : int
        HTTP status code to use in the JSON response.
    detail : Any, optional
        Additional structured detail logged server-side but NOT returned to
        the client in production mode.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to the standard error envelope returned to the client."""
        return {
            "error": True,
            "message": self.message,
            "type": self.__class__.__name__,
        }


# ---------------------------------------------------------------------------
# Typed subclasses
# ---------------------------------------------------------------------------

class ConfigurationError(AppError):
    """Missing or invalid environment variable / config value."""
    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(message, status_code=500, detail=detail)


class KnowledgeBaseError(AppError):
    """career_data.json could not be loaded or parsed."""
    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(message, status_code=500, detail=detail)


class GraniteCallError(AppError):
    """IBM watsonx.ai / Granite API call failed (network, auth, quota)."""
    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(message, status_code=502, detail=detail)


class GraniteParseError(AppError):
    """Granite returned a response that could not be parsed as valid JSON."""
    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(message, status_code=502, detail=detail)


class ValidationError(AppError):
    """Agent input failed validation (missing required fields, wrong types)."""
    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(message, status_code=400, detail=detail)


class SessionError(AppError):
    """Expected session key is absent — pipeline likely called out of order."""
    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(
            message,
            status_code=400,
            detail=detail,
        )
