"""
agents/validation_utils.py
==========================
Deterministic normalisation utilities for the Validation Agent.

All functions in this module are:
  - Pure Python — no Granite, no Flask, no session dependencies
  - Deterministic — same input always produces same output
  - Independently testable — no side effects, no global state mutations
  - Safe to call in any order

These utilities handle the data-cleaning work that must NOT be delegated
to the Granite model:
  - CGPA: handles floats, written numbers, percentages, 4-point GPA
  - Year: handles integers and ordinal words/abbreviations
  - Skills: canonicalises against the vocabulary, deduplicates, preserves unknowns
  - Availability: extracts study hours per week via regex patterns

Import pattern (inside Validation Agent)
-----------------------------------------
    from agents.validation_utils import (
        normalize_cgpa,
        normalize_year,
        normalize_skills,
        extract_availability,
    )

All public functions use underscores to indicate they are internal to the
agents package. They are named without a leading underscore so that the test
module can import them directly without triggering linter warnings about
accessing private members.
"""

from __future__ import annotations

import re
from typing import List, Optional

# ---------------------------------------------------------------------------
# Word-to-digit mapping — used by CGPA and year normalisation
# ---------------------------------------------------------------------------

_WORD_TO_DIGIT: dict[str, int] = {
    "zero":    0, "one":    1, "two":    2,  "three": 3,
    "four":    4, "five":   5, "six":    6,  "seven": 7,
    "eight":   8, "nine":   9, "ten":   10,
    # Ordinal forms (year extraction)
    "first":   1, "second": 2, "third":  3,  "fourth": 4,
    "fifth":   5, "sixth":  6,
    # Common ordinal abbreviations (without suffix — suffix stripped before lookup)
    "1st": 1, "2nd": 2, "3rd": 3, "4th": 4, "5th": 5, "6th": 6,
}

# Pre-built regex for written-number CGPA detection
# Matches patterns like "eight point five eight", "seven point five"
_WRITTEN_CGPA_RE = re.compile(
    r"\b(zero|one|two|three|four|five|six|seven|eight|nine|ten)"
    r"\s+point\s+"
    r"(zero|one|two|three|four|five|six|seven|eight|nine)"
    r"(?:\s+(zero|one|two|three|four|five|six|seven|eight|nine))?",
    re.IGNORECASE,
)

# 4-point GPA patterns: "3.9/4", "3.9/4.0", "3.9 out of 4", "3.9 on a 4 point scale"
_FOUR_POINT_RE = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*(?:/\s*4(?:\.0)?|out\s+of\s+4(?:\.0)?|on\s+a\s+4)",
    re.IGNORECASE,
)

# Percentage patterns: "85%", "85 percent", "85.5%"
# Note: no trailing \b — the % symbol is non-word so \b would not match after it.
_PERCENT_RE = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*(?:%|percent(?:\b|$))",
    re.IGNORECASE,
)

# Decimal/plain number patterns: "8.58", "8.5", "9"
_DECIMAL_RE = re.compile(r"\b(\d+(?:\.\d+)?)\b")

# ---------------------------------------------------------------------------
# Availability regex patterns (ordered by specificity — most specific first)
# ---------------------------------------------------------------------------

_AVAILABILITY_PATTERNS: list[re.Pattern[str]] = [
    # "15 hours a week", "10 hours per week"
    re.compile(r"\b(\d+)\s*hours?\s+(?:a|per)\s+week\b", re.IGNORECASE),
    # "15 hrs a week", "10 hrs/week", "10 hrs per week"
    re.compile(r"\b(\d+)\s*hrs?\s*(?:/|(?:a|per)\s+)week\b", re.IGNORECASE),
    # "15h a week", "10h per week"
    re.compile(r"\b(\d+)\s*h\s+(?:a|per)\s+week\b", re.IGNORECASE),
    # "15 hours weekly", "10 hours every week"
    re.compile(r"\b(\d+)\s*hours?\s+(?:weekly|every\s+week)\b", re.IGNORECASE),
    # "study for 15 hours" (weekly implied by context — least specific, last)
    re.compile(r"\bstudy\s+(?:for\s+)?(\d+)\s*hours?\b", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# Year ordinal patterns
# ---------------------------------------------------------------------------

_ORDINAL_SUFFIX_RE = re.compile(r"^(\d+)(?:st|nd|rd|th)$", re.IGNORECASE)
_YEAR_WORD_RE = re.compile(
    r"\b(first|second|third|fourth|fifth|sixth|1st|2nd|3rd|4th|5th|6th)(?:\s+|-)+year\b",
    re.IGNORECASE,
)
_YEAR_INT_RE = re.compile(r"\b([1-6])\s*(?:st|nd|rd|th)?(?:\s+|-)+year\b", re.IGNORECASE)

# ---------------------------------------------------------------------------
# CGPA NORMALISATION
# ---------------------------------------------------------------------------


def normalize_cgpa(value: object) -> Optional[float]:
    """
    Normalise a raw CGPA value to a float on the 10-point scale (0.0–10.0).

    Handles the following input formats:
      - Float or int already on 10-point scale: 8.58, 8, 9.5
      - String decimal on 10-point scale: "8.58", "8.5"
      - Written number form: "eight point five eight"
      - Percentage (0–100): "85%", "85 percent", "85.5%"
      - 4-point GPA: "3.9/4", "3.9 out of 4", "3.9/4.0"
      - None / empty string / whitespace-only string → returns None

    Parameters
    ----------
    value : object
        Raw CGPA value extracted from transcript or JSON. May be str, int,
        float, or None.

    Returns
    -------
    float | None
        Normalised CGPA on the 10-point scale, rounded to 2 decimal places.
        Returns None if the value cannot be parsed or is out of bounds.

    Examples
    --------
    >>> normalize_cgpa("8.58")
    8.58
    >>> normalize_cgpa("eight point five eight")
    8.58
    >>> normalize_cgpa("85%")
    8.5
    >>> normalize_cgpa("3.9/4")
    9.75
    >>> normalize_cgpa(None)
    None
    >>> normalize_cgpa("twelve")
    None
    """
    # --- Handle None / non-string non-numeric types ---
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return _clamp_cgpa(float(value))

    text = str(value).strip()
    if not text:
        return None

    # --- Strategy 1: Percentage — checked FIRST because "85%" is unambiguous.
    #     Must run before plain decimal (Strategy 4) which would otherwise
    #     extract "85" from "85%" and treat it as a 10-point CGPA. ---
    m = _PERCENT_RE.search(text)
    if m:
        raw = float(m.group(1))
        converted = raw / 10.0
        return _clamp_cgpa(converted)

    # --- Strategy 2: 4-point GPA (check before plain decimal to avoid
    #     misinterpreting "3.9/4" as "3.9") ---
    m = _FOUR_POINT_RE.search(text)
    if m:
        raw = float(m.group(1))
        converted = (raw / 4.0) * 10.0
        return _clamp_cgpa(converted)

    # --- Strategy 3: Written number form ---
    m = _WRITTEN_CGPA_RE.search(text.lower())
    if m:
        integer_word = m.group(1).lower()
        decimal_word1 = m.group(2).lower()
        decimal_word2 = m.group(3).lower() if m.group(3) else None

        integer_part = _WORD_TO_DIGIT.get(integer_word)
        d1 = _WORD_TO_DIGIT.get(decimal_word1)
        if integer_part is None or d1 is None:
            return None

        if decimal_word2 is not None:
            d2 = _WORD_TO_DIGIT.get(decimal_word2)
            if d2 is None:
                decimal_str = str(d1)
            else:
                decimal_str = f"{d1}{d2}"
        else:
            decimal_str = str(d1)

        try:
            result = float(f"{integer_part}.{decimal_str}")
            return _clamp_cgpa(result)
        except ValueError:
            return None

    # --- Strategy 4: Plain decimal or integer string ---
    m = _DECIMAL_RE.search(text)
    if m:
        try:
            raw = float(m.group(1))
            return _clamp_cgpa(raw)
        except ValueError:
            return None

    return None


def _clamp_cgpa(value: float) -> Optional[float]:
    """
    Return value rounded to 2 decimal places if within [0.0, 10.0], else None.

    Parameters
    ----------
    value : float
        The candidate CGPA value.

    Returns
    -------
    float | None
    """
    rounded = round(value, 2)
    if 0.0 <= rounded <= 10.0:
        return rounded
    return None


# ---------------------------------------------------------------------------
# YEAR NORMALISATION
# ---------------------------------------------------------------------------


def normalize_year(value: object) -> Optional[int]:
    """
    Normalise a raw academic year value to an integer in the range [1, 6].

    Handles the following input formats:
      - Integer: 2, 3
      - String integer: "2", "3"
      - Ordinal abbreviation: "1st", "2nd", "3rd", "4th", "5th", "6th"
      - Ordinal word: "first", "second", "third", "fourth", "fifth", "sixth"
      - Compound phrase: "second year", "3rd year", "final year" (→ 4 for UG)
      - None or empty → returns None

    Parameters
    ----------
    value : object
        Raw year value from transcript extraction. May be str, int, or None.

    Returns
    -------
    int | None
        Academic year as an integer in [1, 6], or None if unparseable or
        out of bounds.

    Notes
    -----
    "final year" is treated as year 4 (the standard final year for a
    4-year undergraduate degree). This default suits the primary audience
    but may be adjusted if the student's `branch` indicates a different
    programme length.

    Examples
    --------
    >>> normalize_year(2)
    2
    >>> normalize_year("third")
    3
    >>> normalize_year("2nd")
    2
    >>> normalize_year("final year")
    4
    >>> normalize_year(7)
    None
    >>> normalize_year(None)
    None
    """
    if value is None:
        return None

    if isinstance(value, int):
        return value if 1 <= value <= 6 else None

    if isinstance(value, float):
        int_val = int(value)
        return int_val if 1 <= int_val <= 6 else None

    text = str(value).strip().lower()
    if not text:
        return None

    # Special case: "final year" → 4 (standard UG final year)
    if "final" in text and "year" in text:
        return 4

    # Try ordinal word + "year" compound: "second year", "3rd year"
    m = _YEAR_WORD_RE.search(text)
    if m:
        token = m.group(1).lower()
        result = _WORD_TO_DIGIT.get(token)
        return result if result is not None and 1 <= result <= 6 else None

    m = _YEAR_INT_RE.search(text)
    if m:
        val = int(m.group(1))
        return val if 1 <= val <= 6 else None

    # Strip ordinal suffix and try digit lookup: "2nd" → 2
    m = _ORDINAL_SUFFIX_RE.match(text)
    if m:
        val = int(m.group(1))
        return val if 1 <= val <= 6 else None

    # Ordinal word alone: "second"
    result = _WORD_TO_DIGIT.get(text)
    if result is not None:
        return result if 1 <= result <= 6 else None

    # Plain integer string: "2"
    try:
        val = int(text)
        return val if 1 <= val <= 6 else None
    except ValueError:
        pass

    return None


# ---------------------------------------------------------------------------
# SKILLS NORMALISATION
# ---------------------------------------------------------------------------


def normalize_skills(
    skills: List[object],
    vocabulary: Optional[List[str]] = None,
) -> List[str]:
    """
    Canonicalise a list of skill strings against the skills vocabulary,
    deduplicate, and preserve unknown skills as-is.

    Canonicalisation is performed via:
      1. Case-insensitive exact match against the vocabulary.
      2. Prefix match (first 4+ characters) against the vocabulary, used to
         handle minor variations like "javascript" → "JavaScript",
         "react.js" → "React".
      3. If neither match succeeds, the original skill is kept (lowercased
         and title-cased) to preserve legitimate skills not in the vocabulary.

    Deduplication is performed after canonicalisation so that "JS" and
    "JavaScript" both resolve to "JavaScript" and appear only once.

    Parameters
    ----------
    skills : list
        Raw list of skill strings extracted from a Granite response or user
        input. Non-string items are silently skipped.
    vocabulary : list of str, optional
        The canonical skills vocabulary. If None, the function operates in
        passthrough mode — it still deduplicates and cleans the input but
        does not attempt canonicalisation. This allows the utility to be
        used without a KB connection in unit tests.

    Returns
    -------
    list of str
        Cleaned, canonicalised, deduplicated list of skill strings.
        Preserves insertion order (first occurrence wins on duplicate).

    Notes
    -----
    Unknown skills are deliberately preserved because:
    - The Skill Gap Agent uses set intersection — unknown skills simply fail
      to match any required skill and are ignored without causing errors.
    - Discarding them would silently remove legitimate skills from the profile.

    Examples
    --------
    >>> normalize_skills(["javascript", "React.js", "node"], ["JavaScript", "React", "Node.js"])
    ['JavaScript', 'React', 'Node.js']
    >>> normalize_skills(["Python", "python", "PYTHON"], ["Python"])
    ['Python']
    >>> normalize_skills(["Selenium", "pytest"], ["Python"])  # unknowns preserved
    ['Selenium', 'Pytest']
    >>> normalize_skills([])
    []
    """
    if not skills:
        return []

    # Build lookup structures from vocabulary
    vocab_lower_exact: dict[str, str] = {}   # "javascript" → "JavaScript"
    vocab_prefix: list[tuple[str, str]] = []  # [("javasc", "JavaScript"), ...]

    if vocabulary:
        for canonical in vocabulary:
            key = canonical.lower()
            vocab_lower_exact[key] = canonical
            # Only index prefix if the canonical name is 4+ characters
            if len(key) >= 4:
                vocab_prefix.append((key, canonical))
        # Sort prefix list longest-first so "express.js" matches before "express"
        vocab_prefix.sort(key=lambda t: len(t[0]), reverse=True)

    seen_lower: set[str] = set()
    result: List[str] = []

    for raw in skills:
        if not isinstance(raw, str):
            continue
        cleaned = raw.strip()
        if not cleaned:
            continue

        canonical = _canonicalize_skill(cleaned, vocab_lower_exact, vocab_prefix)

        dedup_key = canonical.lower()
        if dedup_key not in seen_lower:
            seen_lower.add(dedup_key)
            result.append(canonical)

    return result


def _canonicalize_skill(
    raw: str,
    exact_map: dict[str, str],
    prefix_list: list[tuple[str, str]],
) -> str:
    """
    Return the canonical form of a single skill string.

    Parameters
    ----------
    raw : str
        The raw skill string from extraction (e.g. "javascript", "React.js").
    exact_map : dict
        Lowercase → canonical mapping built from the vocabulary.
    prefix_list : list of (prefix, canonical) tuples
        Sorted longest-first for prefix matching.

    Returns
    -------
    str
        Canonical skill name from vocabulary, or a cleaned version of the
        input if no match is found.
    """
    raw_lower = raw.lower().strip()

    # Strategy 1: exact case-insensitive match
    if raw_lower in exact_map:
        return exact_map[raw_lower]

    # Strategy 2: prefix match — raw starts with a known vocab prefix
    for vocab_lower, canonical in prefix_list:
        if raw_lower.startswith(vocab_lower[:4]):
            # Extra check: lengths are similar (within 5 chars) to avoid
            # "java" matching "JavaScript" when the student said "Java"
            if abs(len(raw_lower) - len(vocab_lower)) <= 5:
                return canonical

    # Strategy 3: reverse prefix — a vocabulary word starts with the raw skill
    # Handles "node" → "Node.js", "express" → "Express.js"
    for vocab_lower, canonical in prefix_list:
        if vocab_lower.startswith(raw_lower) and len(raw_lower) >= 4:
            return canonical

    # No match — return cleaned title-case of the raw skill
    return raw.strip().title()


# ---------------------------------------------------------------------------
# AVAILABILITY EXTRACTION
# ---------------------------------------------------------------------------


def extract_availability(transcript: str) -> Optional[int]:
    """
    Extract study hours per week from a transcript string using regex patterns.

    Tries patterns in order from most specific to least specific. Returns
    the first successful match as an integer.

    Does NOT apply the default value (10 hours) — that is the Validation
    Agent's responsibility. This function returns None when no match is found,
    allowing the caller to apply whatever default is appropriate.

    Validity bounds: 1 ≤ hours ≤ 80.
    Values outside this range are treated as implausible and return None.

    Parameters
    ----------
    transcript : str
        The raw input transcript text. May be empty.

    Returns
    -------
    int | None
        Extracted hours per week as an integer, or None if no credible
        availability statement is found.

    Examples
    --------
    >>> extract_availability("I can study 15 hours a week")
    15
    >>> extract_availability("I have 10 hrs per week available")
    10
    >>> extract_availability("available 8h per week")
    8
    >>> extract_availability("I study 12 hours weekly")
    12
    >>> extract_availability("I study for 20 hours")
    20
    >>> extract_availability("I have very limited time")
    None
    >>> extract_availability("")
    None
    >>> extract_availability("I can study 200 hours a week")
    None
    """
    if not transcript or not transcript.strip():
        return None

    for pattern in _AVAILABILITY_PATTERNS:
        m = pattern.search(transcript)
        if m:
            try:
                hours = int(m.group(1))
                if 1 <= hours <= 80:
                    return hours
                # Out-of-bounds value found — keep trying other patterns
                # (unlikely to be a better match, but be safe)
            except (ValueError, IndexError):
                continue

    return None
