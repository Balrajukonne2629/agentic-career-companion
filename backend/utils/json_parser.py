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


def _score_candidate(obj: Any) -> int:
    """Score a parsed JSON object based on its populated contents."""
    if not obj:
        return 0
    score = 0
    if isinstance(obj, dict):
        for k, v in obj.items():
            if v:  # key has a value
                score += 10
                if isinstance(v, (dict, list)):
                    score += _score_candidate(v)
                elif isinstance(v, str) and len(v.strip()) > 0:
                    score += 5
    elif isinstance(obj, list):
        score += len(obj) * 5
        for item in obj:
            score += _score_candidate(item)
    return score


def parse_granite_json(raw: str) -> Any:
    """
    Extract and parse a JSON value from a Granite model response string.

    Scans the response for all candidate JSON structures (fences, matching brackets)
    and returns the one with the highest populated content score. This robustly
    handles cases where the model prints an empty template before outputting the real data.

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
        If all parse strategies fail to produce valid JSON.
    """
    if not raw or not raw.strip():
        raise GraniteParseError(
            "Granite returned an empty response.",
            detail=repr(raw),
        )

    stripped = raw.strip()
    candidates = []

    # Strategy 1 — Try the raw stripped string directly
    try:
        val = json.loads(stripped)
        candidates.append(val)
    except json.JSONDecodeError:
        pass

    # Strategy 2 — Extract from all markdown code fences
    for match in _FENCE_RE.finditer(stripped):
        content = match.group(1).strip()
        try:
            val = json.loads(content)
            candidates.append(val)
        except json.JSONDecodeError:
            pass

    # Strategy 3 — Find all start brackets and parse matching spans
    start_positions = [m.start() for m in _JSON_START_RE.finditer(stripped)]
    for pos in start_positions:
        candidate_str = stripped[pos:]
        # Try to parse incremental prefixes to find matching closing bracket
        try:
            val = json.loads(candidate_str)
            candidates.append(val)
        except json.JSONDecodeError as e:
            # If it failed due to extra trailing characters, try parsing with JSONDecoder.raw_decode
            try:
                decoder = json.JSONDecoder()
                val, _ = decoder.raw_decode(candidate_str)
                candidates.append(val)
            except json.JSONDecodeError:
                pass

    if candidates:
        # Sort candidates by their population score desc, returning the highest-scored one
        best_candidate = max(candidates, key=_score_candidate)
        print("-------------------------------------------------")
        print(f"Parsed Granite response (selected from {len(candidates)} candidates):")
        print(json.dumps(best_candidate, indent=2))
        print("-------------------------------------------------")
        return best_candidate

    log.error("All JSON parse strategies failed for Granite response (chars=%d)", len(raw))
    raise GraniteParseError(
        "Granite returned a response that could not be parsed as JSON. "
        "The prompt may need refinement or the model may have returned "
        "unexpected output.",
        detail=raw[:500],  # Log first 500 chars for debugging
    )

