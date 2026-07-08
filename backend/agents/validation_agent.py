"""
agents/validation_agent.py
==========================
Agent 1: Validation Agent

Entry point of the five-agent pipeline.  Receives raw speech transcript or
typed text and produces a validated, normalized, 9-field student profile.

Architecture (from approved design spec)
-----------------------------------------
Pass 1 — Granite granite-3-8b-instruct
    Extract all detectable fields from the transcript as a JSON object.
    Returns null for fields not mentioned.  One call per validation request
    (two on retry with a modified prompt).

Pass 2 — Python only
    - Merge extracted fields with any prior partial_profile.
    - Apply deterministic normalizers (normalize_cgpa, normalize_year,
      normalize_skills, extract_availability) from validation_utils.py.
    - Infer interests via INTEREST_KEYWORD_MAP in interest_map.py.
    - Infer learning style via LEARNING_STYLE_KEYWORD_MAP.
    - Apply defaults for preferred_learning_style and availability_per_week.
    - Detect missing hard-required fields with Python set comparison.
    - Return complete / incomplete / error response.

Session safety contract
-----------------------
session["student_profile"] is written ONLY when status == "complete".
On status "incomplete" or "error" the session is never modified by this agent.
Session writes happen in routes/pipeline.py, not here.

Determinism guarantee
---------------------
All scoring, normalization, gap detection, and defaulting is pure Python.
Granite is used exclusively for natural language extraction.

Output contracts
----------------
Complete:
    { "status": "complete", "profile": { ...9 fields... } }

Incomplete:
    {
        "status": "incomplete",
        "missing_fields": ["cgpa", ...],
        "missing_labels": { "cgpa": "What is your current CGPA?", ... },
        "partial_profile": { ...fields extracted so far... }
    }

Error (Granite failure after retries):
    { "status": "error", "message": "...", "fallback": True }
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from agents.validation_utils import (
    extract_availability,
    normalize_cgpa,
    normalize_skills,
    normalize_year,
)
from errors import GraniteCallError, GraniteParseError
from logger import get_logger
from utils.career_loader import get_interest_categories, get_skills_vocabulary, get_all_careers
from utils.granite_client import call_granite_fast
from utils.interest_map import infer_interests, infer_learning_style
from utils.json_parser import parse_granite_json

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Hard-required fields and their human-readable follow-up questions
# ---------------------------------------------------------------------------

HARD_REQUIRED: Dict[str, str] = {
    "name":        "What is your full name?",
    "branch":      "What is your degree and branch? (e.g. B.Tech Information Technology)",
    "year":        "Which year of your degree are you currently in?",
    "cgpa":        "What is your current CGPA?",
    "skills":      "Which technical skills do you currently know?",
    "interests":   "What topics or areas interest you most?",
    "career_goal": "What career path or job role do you want to pursue?",
}

# Defaulted fields — never surfaced to the student as missing
DEFAULTED_FIELDS: Dict[str, Any] = {
    "preferred_learning_style": "mixed",
    "availability_per_week":    10,
}

VALID_LEARNING_STYLES = frozenset(
    {"project-based", "video-based", "reading-based", "mixed"}
)

# ---------------------------------------------------------------------------
# Pass-1 Granite extraction prompt
# ---------------------------------------------------------------------------

_EXTRACTION_SCHEMA = """\
{
  "name": <string or null>,
  "branch": <string or null>,
  "year": <string or null>,
  "cgpa": <string or null>,
  "skills": <array of strings or null>,
  "interests": <array of strings or null>,
  "career_goal": <string or null>,
  "preferred_learning_style": <string or null>,
  "availability_per_week": <string or null>
}"""

_EXTRACTION_EXAMPLE = """\
{
  "name": "Balraju",
  "branch": "B.Tech Information Technology",
  "year": "second",
  "cgpa": "8.58",
  "skills": ["Java", "C++", "React"],
  "interests": ["web development", "full stack"],
  "career_goal": "Full Stack Developer",
  "preferred_learning_style": null,
  "availability_per_week": null
}"""

_FIELD_GUIDANCE = """\
Field extraction guidance:
- name: The student's first or full name. Look for "I am", "My name is", "I'm".
- branch: Degree and branch. Look for B.Tech, B.E., BSc, MCA, followed by a subject.
- year: Current year of study. Look for "first year", "2nd year", "third year", "final year".
- cgpa: Academic score. Look for CGPA, GPA, percentage, score. Return the raw value as a string.
- skills: Programming languages, frameworks, tools mentioned. Return as an array.
- interests: Topics, domains, or areas the student enjoys or wants to explore. Return as an array.
- career_goal: Target job role or career path. Look for "want to become", "goal is", "interested in becoming".
- preferred_learning_style: How they prefer to learn (hands-on, videos, reading). May be null.
- availability_per_week: Hours per week available to study. Look for numeric statements. Return as a string."""

_BASE_PROMPT_TEMPLATE = """\
You are a student profile extraction assistant.

Your task is to extract information from the student introduction below and return it as a JSON object.

RULES:
1. Return ONLY a JSON object. No explanation. No markdown fences. No extra text.
2. If a field is not mentioned in the introduction, set its value to null.
3. Do not invent or guess any information.
4. Return skills and interests as arrays. All other fields are strings.

{field_guidance}

The expected JSON schema is:
{schema}

Example output:
{example}

Extract from the student introduction below and return the JSON object:
STUDENT_INTRODUCTION_START
{transcript}
STUDENT_INTRODUCTION_END

JSON:"""

_RETRY_PROMPT_TEMPLATE = """\
You are a student profile extraction assistant.

Your previous response was not valid JSON. Please try again.

STRICT RULES:
1. Return ONLY a valid JSON object — start with {{ and end with }}.
2. Do not include any text, explanation, or markdown before or after the JSON.
3. Every field must be present. Use null for fields not mentioned.
4. Skills and interests must be JSON arrays (e.g. ["Java", "Python"]).

The expected JSON schema is:
{schema}

Extract from the student introduction below:
STUDENT_INTRODUCTION_START
{transcript}
STUDENT_INTRODUCTION_END

Respond with only the JSON object starting with {{:"""


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(
    transcript: str,
    partial_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run the Validation Agent on a raw transcript.

    Parameters
    ----------
    transcript : str
        Raw text from Web Speech API STT or direct text input.
        Minimum 30 characters enforced upstream in the route.
    partial_profile : dict, optional
        Previously extracted partial profile from a prior incomplete call.
        Fields from this dict are merged with the new extraction; new values
        override old ones, except skills/interests which are unioned.

    Returns
    -------
    dict
        One of the three output contracts documented in the module docstring:
        ``{ "status": "complete", "profile": {...} }``
        ``{ "status": "incomplete", "missing_fields": [...], ... }``
        ``{ "status": "error", "message": "...", "fallback": True }``
    """
    log.info("ValidationAgent.run | transcript_chars=%d", len(transcript))

    # -----------------------------------------------------------------------
    # Step 1 — Granite Pass-1: extract fields from transcript
    # -----------------------------------------------------------------------
    try:
        extracted = _granite_extract(transcript)
    except (GraniteCallError, GraniteParseError) as exc:
        log.warning("Granite unavailable — using deterministic fallback")
        extracted = _regex_extract(transcript)

    # -----------------------------------------------------------------------
    # Step 2 — Merge with partial_profile (union for arrays, override otherwise)
    # -----------------------------------------------------------------------
    merged = _merge(partial_profile or {}, extracted)

    # -----------------------------------------------------------------------
    # Step 3 — Python normalisation
    # -----------------------------------------------------------------------
    _apply_normalizations(merged, transcript)

    # -----------------------------------------------------------------------
    # Step 4 — Apply defaults for the two defaulted fields
    # -----------------------------------------------------------------------
    _apply_defaults(merged)

    # -----------------------------------------------------------------------
    # Step 5 — Pass-2: Python gap detection on 7 hard-required fields
    # -----------------------------------------------------------------------
    missing = _detect_missing(merged)

    if missing:
        log.info(
            "ValidationAgent: incomplete profile | missing=%s", missing
        )
        return {
            "status": "incomplete",
            "missing_fields": missing,
            "missing_labels": {f: HARD_REQUIRED[f] for f in missing},
            "partial_profile": merged,
        }

    # -----------------------------------------------------------------------
    # Step 6 — Enforce session schema invariants before writing
    # -----------------------------------------------------------------------
    _enforce_invariants(merged)

    log.info(
        "ValidationAgent: complete profile | name=%s skills=%d",
        merged.get("name"),
        len(merged.get("skills", [])),
    )
    return {"status": "complete", "profile": merged}


# ---------------------------------------------------------------------------
# Granite extraction (Pass 1) with one retry
# ---------------------------------------------------------------------------

def _granite_extract(transcript: str) -> Dict[str, Any]:
    """
    Call Granite granite-3-8b-instruct to extract profile fields.

    Attempts the base extraction prompt first.  On JSON parse failure, retries
    once with a stricter prompt and 20 % more max_new_tokens.

    Parameters
    ----------
    transcript : str
        Raw student transcript.

    Returns
    -------
    dict
        Raw extracted fields (values may be None / empty).

    Raises
    ------
    GraniteCallError
        If the Granite API call fails on both attempts.
    GraniteParseError
        If both JSON parse attempts fail.
    """
    prompt = _BASE_PROMPT_TEMPLATE.format(
        field_guidance=_FIELD_GUIDANCE,
        schema=_EXTRACTION_SCHEMA,
        example=_EXTRACTION_EXAMPLE,
        transcript=transcript,
    )

    raw = call_granite_fast(prompt)

    try:
        result = parse_granite_json(raw)
        return _coerce_to_dict(result)
    except GraniteParseError:
        log.warning(
            "ValidationAgent: Pass-1 JSON parse failed — retrying with strict prompt"
        )

    # Retry with modified prompt and more tokens
    retry_prompt = _RETRY_PROMPT_TEMPLATE.format(
        schema=_EXTRACTION_SCHEMA,
        transcript=transcript,
    )
    raw_retry = call_granite_fast(
        retry_prompt,
        params={"max_new_tokens": int(1024 * 1.2)},
    )

    # Let GraniteParseError propagate on second failure
    result = parse_granite_json(raw_retry)
    return _coerce_to_dict(result)


def _coerce_to_dict(value: Any) -> Dict[str, Any]:
    """
    Ensure the parsed Granite response is a dict.

    Granite occasionally wraps the JSON object in a list.  If it returns a
    single-element list containing a dict, unwrap it.  Anything else that is
    not a dict is treated as a parse failure.

    Raises
    ------
    GraniteParseError
    """
    if isinstance(value, dict):
        return value
    if isinstance(value, list) and len(value) == 1 and isinstance(value[0], dict):
        return value[0]
    raise GraniteParseError(
        "Granite extraction returned an unexpected type. Expected a JSON object.",
        detail=repr(value)[:200],
    )


def _regex_extract(transcript: str) -> Dict[str, Any]:
    """
    Fallback regex-based profile extraction when Granite is unavailable.
    Extracts name, branch, year, cgpa, skills, interests, career_goal,
    preferred_learning_style, and availability_per_week using patterns.
    """
    log.info("ValidationAgent: Using regex fallback extraction")
    profile: Dict[str, Any] = {
        "name": None,
        "branch": None,
        "year": None,
        "cgpa": None,
        "skills": [],
        "interests": [],
        "career_goal": None,
        "preferred_learning_style": None,
        "availability_per_week": None,
    }

    # 1. Name
    name_patterns = [
        r"\bmy\s+name\s+is\s+([a-zA-Z\s]+?)(?:\s+and|\s+i\s+am|\s+i'm|\s+a\s+|\s+student|\bmy\b|\bbranch\b|\.|,|$)",
        r"\bi'm\s+([a-zA-Z\s]+?)(?:\s+and|\s+i\s+am|\s+a\s+|\s+student|\bmy\b|\bbranch\b|\.|,|$)",
        r"\bi\s+am\s+([a-zA-Z\s]+?)(?:\s+and|\s+a\s+|\s+student|\bmy\b|\bbranch\b|\.|,|$)",
        r"\bthis\s+is\s+([a-zA-Z\s]+?)(?:\s+and|\s+a\s+|\s+student|\bmy\b|\bbranch\b|\.|,|$)"
    ]
    for pat in name_patterns:
        m = re.search(pat, transcript, re.IGNORECASE)
        if m:
            name_val = m.group(1).strip()
            if name_val and len(name_val.split()) <= 3:
                profile["name"] = name_val.title()
                break

    # 2. Branch
    branch_patterns = [
        r"\b(b\.?tech(?:\s+(?:in\s+)?(?:it|cse|ece|information\s+technology|computer\s+science(?:\s+and\s+engineering)?|[a-zA-Z\s]+))?)\b",
        r"\b(m\.?tech(?:\s+(?:in\s+)?(?:it|cse|ece|information\s+technology|computer\s+science(?:\s+and\s+engineering)?|[a-zA-Z\s]+))?)\b",
        r"\b(b\.?e\.?(?:\s+(?:in\s+)?(?:it|cse|ece|information\s+technology|computer\s+science(?:\s+and\s+engineering)?|[a-zA-Z\s]+))?)\b",
        r"\b(b\.?sc(?:\s+(?:in\s+)?(?:it|cse|ece|information\s+technology|computer\s+science(?:\s+and\s+engineering)?|[a-zA-Z\s]+))?)\b",
        r"\b(m\.?c\.?a\.?)\b",
        r"\b(b\.?c\.?a\.?)\b",
        r"\b(degree\s+in\s+[a-zA-Z\s]+?)(?:\s+with|\s+and|\.|,|$)",
        r"\b(studying\s+[a-zA-Z\s]+?)(?:\s+with|\s+and|\.|,|$)"
    ]
    for pat in branch_patterns:
        m = re.search(pat, transcript, re.IGNORECASE)
        if m:
            branch_val = m.group(1).strip()
            if branch_val:
                profile["branch"] = branch_val
                break

    # 3. Year
    year_val = normalize_year(transcript)
    if year_val is not None:
        profile["year"] = str(year_val)

    # 4. CGPA
    cgpa_val = normalize_cgpa(transcript)
    if cgpa_val is not None:
        profile["cgpa"] = str(cgpa_val)

    # 5. Skills
    vocab = get_skills_vocabulary()
    extracted_skills = []
    if vocab:
        lower_transcript = transcript.lower()
        for skill in vocab:
            pattern = r"\b" + re.escape(skill.lower()) + r"\b"
            if re.search(pattern, lower_transcript):
                extracted_skills.append(skill)
    profile["skills"] = extracted_skills

    # 6. Interests
    profile["interests"] = infer_interests(transcript)

    # 7. Career Goal
    careers = get_all_careers()
    lower_transcript = transcript.lower()
    found_goal = None
    if careers:
        for career in careers:
            title = career.get("title", "")
            if title and re.search(r"\b" + re.escape(title.lower()) + r"\b", lower_transcript):
                found_goal = title
                break
    if not found_goal:
        goal_patterns = [
            r"\b(?:want\s+to\s+become|goal\s+is\s+to\s+be|career\s+goal\s+is|aim\s+to\s+be|aspire\s+to\s+be|aspiring)\s+(?:a\s+|an\s+)?([a-zA-Z\s\-]+?)(?:\s+using|\s+with|\s+and|\s+in|\.|,|$)",
            r"\b(?:interested\s+in\s+pursuing)\s+(?:a\s+|an\s+)?([a-zA-Z\s\-]+?)(?:\s+as\s+a|\.|,|$)"
        ]
        for pat in goal_patterns:
            m = re.search(pat, transcript, re.IGNORECASE)
            if m:
                found_goal = m.group(1).strip().title()
                break
    profile["career_goal"] = found_goal

    # 8. Learning style
    profile["preferred_learning_style"] = infer_learning_style(transcript)

    # 9. Availability
    avail_val = extract_availability(transcript)
    if avail_val is not None:
        profile["availability_per_week"] = str(avail_val)

    return profile


# ---------------------------------------------------------------------------
# Merge: partial_profile (existing) + newly extracted (new)
# ---------------------------------------------------------------------------

def _merge(
    existing: Dict[str, Any],
    extracted: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Merge an existing partial profile with newly extracted fields.

    Rules:
    - For scalar fields: extracted value wins over existing when non-None/non-empty.
    - For list fields (skills, interests): union of both lists (deduplication later).
    - If extracted has a null/empty value, the existing value is kept.

    Parameters
    ----------
    existing : dict
        Previously extracted partial profile (may be empty).
    extracted : dict
        Freshly extracted fields from the latest transcript.

    Returns
    -------
    dict
        Merged profile dict.
    """
    merged: Dict[str, Any] = dict(existing)

    _LIST_FIELDS = {"skills", "interests"}
    _ALL_FIELDS = set(HARD_REQUIRED) | set(DEFAULTED_FIELDS)

    for field in _ALL_FIELDS:
        new_val = extracted.get(field)
        old_val = merged.get(field)

        if field in _LIST_FIELDS:
            old_list = old_val if isinstance(old_val, list) else []
            new_list = new_val if isinstance(new_val, list) else []
            # Flatten and combine — deduplication happens in normalize_skills
            merged[field] = old_list + new_list
        else:
            # Non-empty new value always wins
            if _is_present(new_val):
                merged[field] = new_val
            elif old_val is None:
                merged[field] = None

    return merged


# ---------------------------------------------------------------------------
# Normalisation (Step 3)
# ---------------------------------------------------------------------------

def _apply_normalizations(merged: Dict[str, Any], transcript: str) -> None:
    """
    Apply all deterministic normalisers to the merged profile dict in-place.

    Also applies Python-side interest and learning style inference, which runs
    regardless of what Granite extracted.

    Parameters
    ----------
    merged : dict
        The merged profile dict (modified in-place).
    transcript : str
        Full transcript used for availability extraction and keyword inference.
    """
    vocab = get_skills_vocabulary()
    interest_cats = get_interest_categories()

    # --- CGPA ---
    merged["cgpa"] = normalize_cgpa(merged.get("cgpa"))

    # --- Year ---
    merged["year"] = normalize_year(merged.get("year"))

    # --- Skills ---
    raw_skills = merged.get("skills") or []
    if isinstance(raw_skills, str):
        # Granite occasionally returns a comma-separated string
        raw_skills = [s.strip() for s in raw_skills.split(",") if s.strip()]
    merged["skills"] = normalize_skills(raw_skills, vocab)

    # --- Interests: union of Granite-extracted (canonicalized) + Python-inferred ---
    granite_interests = merged.get("interests") or []
    if isinstance(granite_interests, str):
        granite_interests = [i.strip() for i in granite_interests.split(",") if i.strip()]

    canonical_granite = _canonicalize_interests(granite_interests, interest_cats)
    python_inferred   = infer_interests(transcript)

    combined: List[str] = []
    seen: set = set()
    for interest in canonical_granite + python_inferred:
        if interest not in seen:
            combined.append(interest)
            seen.add(interest)
    merged["interests"] = combined

    # --- Learning style ---
    raw_style = merged.get("preferred_learning_style")
    if isinstance(raw_style, str) and raw_style.lower().strip() in VALID_LEARNING_STYLES:
        merged["preferred_learning_style"] = raw_style.lower().strip()
    else:
        inferred_style = infer_learning_style(transcript)
        merged["preferred_learning_style"] = inferred_style  # None → default applied later

    # --- Availability ---
    raw_avail = merged.get("availability_per_week")
    extracted_from_merged = _parse_availability_field(raw_avail)
    extracted_from_transcript = extract_availability(transcript)

    if extracted_from_merged is not None:
        merged["availability_per_week"] = extracted_from_merged
    elif extracted_from_transcript is not None:
        merged["availability_per_week"] = extracted_from_transcript
    else:
        merged["availability_per_week"] = None  # default applied next step

    # --- Name / branch / career_goal: strip whitespace ---
    for scalar_field in ("name", "branch", "career_goal"):
        val = merged.get(scalar_field)
        if isinstance(val, str):
            stripped = val.strip()
            merged[scalar_field] = stripped if stripped else None


def _canonicalize_interests(
    raw: List[Any],
    canonical_list: List[str],
) -> List[str]:
    """
    Map raw interest strings from Granite to canonical interest category names.

    Performs case-insensitive exact match. Strings that do not match any
    canonical category are discarded (prevents hallucinated categories from
    entering the profile).

    Parameters
    ----------
    raw : list
        Raw interest strings from Granite extraction.
    canonical_list : list
        The authoritative interest_categories list from career_data.json.

    Returns
    -------
    list
        Matched canonical category strings only.
    """
    lower_map = {c.lower(): c for c in canonical_list}
    result: List[str] = []
    seen: set = set()

    for item in raw:
        if not isinstance(item, str):
            continue
        key = item.lower().strip()
        canonical = lower_map.get(key)
        if canonical and canonical not in seen:
            result.append(canonical)
            seen.add(canonical)

    return result


def _parse_availability_field(value: Any) -> Optional[int]:
    """
    Parse the raw availability_per_week field from the Granite-extracted dict.

    Granite may return this as a string ("15"), an int (15), or null.
    Validates bounds: 1–80.

    Parameters
    ----------
    value : any
        Raw value from the merged profile dict.

    Returns
    -------
    int | None
    """
    if value is None:
        return None
    try:
        hours = int(str(value).strip())
        return hours if 1 <= hours <= 80 else None
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Defaults (Step 4)
# ---------------------------------------------------------------------------

def _apply_defaults(merged: Dict[str, Any]) -> None:
    """
    Apply default values for the two defaulted fields in-place.

    Called after normalization.  Never adds these fields to missing_fields.

    Parameters
    ----------
    merged : dict
        Profile dict (modified in-place).
    """
    if not merged.get("preferred_learning_style"):
        merged["preferred_learning_style"] = DEFAULTED_FIELDS["preferred_learning_style"]

    if merged.get("availability_per_week") is None:
        merged["availability_per_week"] = DEFAULTED_FIELDS["availability_per_week"]


# ---------------------------------------------------------------------------
# Gap detection (Pass 2 / Step 5)
# ---------------------------------------------------------------------------

def _detect_missing(merged: Dict[str, Any]) -> List[str]:
    """
    Return a list of field names that are missing from the profile.

    Only checks the 7 hard-required fields.  The 2 defaulted fields are
    never included in the result.

    A field is considered present when:
      name, branch, career_goal  — non-empty string
      year                       — integer 1–6
      cgpa                       — float 0.0–10.0
      skills                     — list with ≥1 item
      interests                  — list with ≥1 item

    Parameters
    ----------
    merged : dict
        Fully normalized and merged profile dict.

    Returns
    -------
    list
        Ordered list of missing field name strings.
        Empty list means the profile is complete.
    """
    missing: List[str] = []

    for field in HARD_REQUIRED:
        val = merged.get(field)

        if field in ("name", "branch", "career_goal"):
            if not isinstance(val, str) or not val.strip():
                missing.append(field)

        elif field == "year":
            if not isinstance(val, int) or not (1 <= val <= 6):
                missing.append(field)

        elif field == "cgpa":
            if not isinstance(val, float) or not (0.0 <= val <= 10.0):
                missing.append(field)

        elif field in ("skills", "interests"):
            if not isinstance(val, list) or len(val) == 0:
                missing.append(field)

    return missing


# ---------------------------------------------------------------------------
# Session schema invariant check (Step 6)
# ---------------------------------------------------------------------------

def _enforce_invariants(profile: Dict[str, Any]) -> None:
    """
    Verify all 8 session schema invariants before the profile is returned.

    This is a defence-in-depth check.  It should never trigger in normal
    operation — a failure here indicates a bug in the normalization or
    gap-detection logic.

    Raises
    ------
    ValueError
        If any invariant is violated.
    """
    name  = profile.get("name")
    year  = profile.get("year")
    cgpa  = profile.get("cgpa")
    style = profile.get("preferred_learning_style")
    avail = profile.get("availability_per_week")
    skls  = profile.get("skills")
    ints  = profile.get("interests")
    goal  = profile.get("career_goal")

    violations: List[str] = []

    if not isinstance(name, str) or not name.strip():
        violations.append("I1: name must be a non-empty string")
    if not isinstance(year, int) or not (1 <= year <= 6):
        violations.append(f"I2: year must be int 1-6, got {year!r}")
    if not isinstance(cgpa, float) or not (0.0 <= cgpa <= 10.0):
        violations.append(f"I3: cgpa must be float 0-10, got {cgpa!r}")
    if not isinstance(skls, list) or len(skls) == 0:
        violations.append("I4: skills must be a non-empty list")
    if not isinstance(ints, list) or len(ints) == 0:
        violations.append("I5: interests must be a non-empty list")
    if not isinstance(goal, str) or not goal.strip():
        violations.append("I6: career_goal must be a non-empty string")
    if style not in VALID_LEARNING_STYLES:
        violations.append(f"I7: preferred_learning_style invalid: {style!r}")
    if not isinstance(avail, int) or not (1 <= avail <= 80):
        violations.append(f"I8: availability_per_week must be int 1-80, got {avail!r}")

    if violations:
        msg = "Session schema invariant violation(s): " + "; ".join(violations)
        log.error("ValidationAgent invariant check failed: %s", msg)
        raise ValueError(msg)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_present(value: Any) -> bool:
    """
    Return True if value is non-None and non-empty (string, list, or number).

    Parameters
    ----------
    value : Any

    Returns
    -------
    bool
    """
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, (int, float)):
        return True
    return bool(value)
