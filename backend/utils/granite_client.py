"""
utils/granite_client.py
=======================
IBM watsonx.ai Granite model interface.

Provides two pre-configured callable functions that agents import directly:

    call_granite_fast(prompt)   — granite-3-8b-instruct
    call_granite_strong(prompt) — granite-13b-instruct-v2

Design decisions
----------------
- A single WatsonXAI client instance is created lazily on first call and
  reused for all subsequent calls (connection pooling).
- Retry logic is built in: up to MAX_RETRIES attempts with exponential backoff.
- Both functions raise typed exceptions from errors.py — never raw SDK errors.
- Token generation parameters are set to conservative defaults suitable for
  structured JSON extraction. Agents may override via the params argument.

Parameters reference (TextGenParameters)
-----------------------------------------
    max_new_tokens : int   Maximum tokens in the response (default 1024)
    temperature    : float Sampling temperature — 0.0 = deterministic (default)
    repetition_penalty : float Penalise repeated tokens (default 1.1)
"""

import time
from typing import Any, Dict, Optional

from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from config import config
from errors import GraniteCallError, GraniteParseError
from logger import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_RETRIES: int = 2
RETRY_DELAY_SECONDS: float = 2.0

# Default generation parameters — JSON-extraction optimised
_DEFAULT_PARAMS: Dict[str, Any] = {
    GenParams.MAX_NEW_TOKENS: 1024,
    GenParams.TEMPERATURE: 0.0,
    GenParams.REPETITION_PENALTY: 1.1,
}

# ---------------------------------------------------------------------------
# Lazy client initialisation
# ---------------------------------------------------------------------------
_api_client: Optional[APIClient] = None


def _get_client() -> APIClient:
    """
    Return the shared WatsonXAI APIClient, initialising it on first call.

    Raises
    ------
    GraniteCallError
        If credentials are missing or the SDK raises during initialisation.
    """
    global _api_client
    if _api_client is not None:
        return _api_client

    try:
        credentials = Credentials(
            url=config.IBM_WATSONX_URL,
            api_key=config.IBM_API_KEY,
        )
        _api_client = APIClient(credentials)
        log.info("IBM watsonx.ai APIClient initialised (url=%s)", config.IBM_WATSONX_URL)
        return _api_client
    except Exception as exc:
        raise GraniteCallError(
            "Failed to initialise IBM watsonx.ai client. "
            "Check IBM_API_KEY and IBM_WATSONX_URL in your .env file.",
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# Core call function
# ---------------------------------------------------------------------------

def _call_granite(
    model_id: str,
    prompt: str,
    params: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Send a prompt to a Granite model and return the generated text.

    Parameters
    ----------
    model_id : str
        The IBM model identifier string.
    prompt : str
        The fully assembled prompt to send.
    params : dict, optional
        Override generation parameters. Merged with _DEFAULT_PARAMS.

    Returns
    -------
    str
        The stripped generated text from the model.

    Raises
    ------
    GraniteCallError
        On API errors, authentication failures, or quota exhaustion.
    GraniteParseError
        If the response structure is unexpected and text cannot be extracted.
    """
    merged_params = {**_DEFAULT_PARAMS, **(params or {})}
    client = _get_client()

    attempt = 0
    last_exc: Optional[Exception] = None

    while attempt <= MAX_RETRIES:
        try:
            model = ModelInference(
                model_id=model_id,
                api_client=client,
                project_id=config.IBM_PROJECT_ID,
                params=merged_params,
            )
            response = model.generate_text(prompt=prompt)

            # The SDK returns a plain string from generate_text()
            if not isinstance(response, str):
                raise GraniteParseError(
                    f"Unexpected response type from Granite model {model_id}: "
                    f"{type(response).__name__}",
                    detail=repr(response),
                )

            text = response.strip()
            log.debug(
                "Granite %s | prompt_chars=%d | response_chars=%d",
                model_id,
                len(prompt),
                len(text),
            )
            log.info("Granite response received")
            return text

        except (GraniteCallError, GraniteParseError):
            raise  # Already typed — re-raise immediately

        except Exception as exc:
            last_exc = exc
            attempt += 1
            if attempt <= MAX_RETRIES:
                log.warning(
                    "Granite %s call failed (attempt %d/%d): %s — retrying in %.1fs",
                    model_id,
                    attempt,
                    MAX_RETRIES + 1,
                    str(exc),
                    RETRY_DELAY_SECONDS,
                )
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                log.error(
                    "Granite %s call failed after %d attempts: %s",
                    model_id,
                    MAX_RETRIES + 1,
                    str(exc),
                )

    raise GraniteCallError(
        f"Granite model {model_id} failed after {MAX_RETRIES + 1} attempts. "
        "The IBM watsonx.ai service may be unavailable.",
        detail=str(last_exc),
    )


# ---------------------------------------------------------------------------
# Public API — imported by agents
# ---------------------------------------------------------------------------

def call_granite_fast(
    prompt: str,
    params: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Call granite-3-8b-instruct.

    Use for: Validation Agent, Profile Agent.
    Optimised for: speed, structured JSON extraction.

    Parameters
    ----------
    prompt : str
        Fully assembled prompt string.
    params : dict, optional
        Override specific generation parameters.

    Returns
    -------
    str
        Stripped model response text.
    """
    log.debug("call_granite_fast | model=%s", config.GRANITE_FAST_MODEL)
    return _call_granite(config.GRANITE_FAST_MODEL, prompt, params)


def call_granite_strong(
    prompt: str,
    params: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Call granite-13b-instruct-v2.

    Use for: Career Recommendation Agent, Skill Gap Agent, Roadmap Agent.
    Optimised for: reasoning quality, complex structured generation.

    Parameters
    ----------
    prompt : str
        Fully assembled prompt string.
    params : dict, optional
        Override specific generation parameters.

    Returns
    -------
    str
        Stripped model response text.
    """
    log.debug("call_granite_strong | model=%s", config.GRANITE_STRONG_MODEL)
    return _call_granite(config.GRANITE_STRONG_MODEL, prompt, params)
