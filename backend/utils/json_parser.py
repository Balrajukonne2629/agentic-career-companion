"""
utils/json_parser.py
====================
Robust JSON extraction from Granite model responses.

Problem
-------
Granite models frequently wrap JSON output in markdown fences:

    ```json
    { "key": "value" }
    ```

Or include preamble text before the JSON object:

    "Here is the extracted profile:\n{ \"name\": \"Balraju\" }"

parse_granite_json() strips all known wrapper patterns and returns a
parsed Python object. If parsing still fails after stripping, it raises
GraniteParseError so the calling agent can trigger a retry.

Usage
-----
    from utils.json_parser import parse_granite_json
    result = parse_granite_json(granite_response_text)
"""

import json
import re
from typing import Any

from errors import GraniteParseError
from logger import get_logger

log = get_logger(__name__)

# Regex to extract content from ```json ... ``` or ``` ... ``` fences
_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)

# Regex to find the first { or [ that starts a JSON value
_JSON_START_RE = re.compile(r"[{\[]")


def parse_granite_json(raw: str) -> Any:
    """
    Extract and parse a JSON value from a Granite model response string.

    Attempts the following strategies in order:
    1. Direct json.loads on the stripped raw string.
    2. Extract content from a markdown code fence and parse.
    3. Find the first '{' or '[' character and parse from there.

    Parameters
    ----------
    raw : str
        The raw text string returned by call_granite_fast() or
        call_granite_strong().

    Returns
    -------
    Any
        The parsed Python object (dict, list, etc.).

    Raises
    ------
    GraniteParseError
        If all three strategies fail to produce valid JSON.
    """
    if not raw or not raw.strip():
        raise GraniteParseError(
            "Granite returned an empty response.",
            detail=repr(raw),
        )

    stripped = raw.strip()

    # Strategy 1 — try the raw stripped string directly
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Strategy 2 — extract from markdown code fence
    fence_match = _FENCE_RE.search(stripped)
    if fence_match:
        fence_content = fence_match.group(1).strip()
        try:
            return json.loads(fence_content)
        except json.JSONDecodeError:
            pass

    # Strategy 3 — find first JSON delimiter and parse from there
    start_match = _JSON_START_RE.search(stripped)
    if start_match:
        candidate = stripped[start_match.start():]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    log.error("All JSON parse strategies failed for Granite response (chars=%d)", len(raw))
    raise GraniteParseError(
        "Granite returned a response that could not be parsed as JSON. "
        "The prompt may need refinement or the model may have returned "
        "unexpected output.",
        detail=raw[:500],  # Log first 500 chars for debugging
    )
