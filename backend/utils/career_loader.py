"""
utils/career_loader.py
======================
Knowledge base loader and serialiser for the Career Recommendation Agent.

Responsibilities
----------------
1. Load career_data.json exactly once and cache it in memory.
2. Provide typed accessor functions for agent use.
3. Produce a compact, token-budget-respecting text block for Granite prompts.
4. Validate schema version on load so agents never run against stale data.

Token budget
------------
The Career Recommendation Agent is allocated a maximum of 1,200 tokens
for the career context block injected into its Granite prompt. The
serialize_careers_for_prompt() function enforces this by including only
title, required_skills, and suitable_for_interests — not full career objects.
"""

import json
from typing import Any, Dict, List, Optional

from config import config
from errors import KnowledgeBaseError
from logger import get_logger

log = get_logger(__name__)

SUPPORTED_SCHEMA_VERSION = "1.0"

# In-memory cache — loaded once per process lifetime
_career_data: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Internal loader
# ---------------------------------------------------------------------------

def _load() -> Dict[str, Any]:
    """Load and cache career_data.json. Validates schema version."""
    global _career_data
    if _career_data is not None:
        return _career_data

    try:
        with open(config.CAREER_DATA_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise KnowledgeBaseError(
            f"career_data.json not found at: {config.CAREER_DATA_PATH}"
        )
    except json.JSONDecodeError as exc:
        raise KnowledgeBaseError(
            "career_data.json contains invalid JSON.",
            detail=str(exc),
        )

    version = data.get("version")
    if version != SUPPORTED_SCHEMA_VERSION:
        raise KnowledgeBaseError(
            f"career_data.json schema version '{version}' is not supported. "
            f"Expected '{SUPPORTED_SCHEMA_VERSION}'. "
            "Update the knowledge base or bump SUPPORTED_SCHEMA_VERSION."
        )

    _career_data = data
    log.info(
        "Knowledge base loaded: %d careers (schema v%s)",
        len(data.get("careers", [])),
        version,
    )
    return _career_data


# ---------------------------------------------------------------------------
# Public accessors
# ---------------------------------------------------------------------------

def get_all_careers() -> List[Dict[str, Any]]:
    """Return the full list of career objects."""
    return _load().get("careers", [])


def get_career_by_id(career_id: str) -> Optional[Dict[str, Any]]:
    """
    Return a single career object by career_id, or None if not found.

    Parameters
    ----------
    career_id : str
        Kebab-case career identifier (e.g. "full-stack-developer").
    """
    for career in get_all_careers():
        if career.get("career_id") == career_id:
            return career
    log.warning("Career not found in knowledge base: '%s'", career_id)
    return None


def get_interest_categories() -> List[str]:
    """Return the master interest categories list from the envelope."""
    return _load().get("interest_categories", [])


def get_skills_vocabulary() -> List[str]:
    """Return the canonical skills vocabulary list from the envelope."""
    return _load().get("skills_vocabulary", [])


def get_tools_vocabulary() -> List[str]:
    """Return the canonical tools vocabulary list from the envelope."""
    return _load().get("tools_vocabulary", [])


# ---------------------------------------------------------------------------
# Prompt serialiser
# ---------------------------------------------------------------------------

def serialize_careers_for_prompt() -> str:
    """
    Produce a compact, Granite-prompt-safe text block summarising all careers.

    Includes only the fields the Career Recommendation Agent needs for
    matching: title, required_skills, and suitable_for_interests.
    Keeps the total output well within the 1,200-token budget.

    Returns
    -------
    str
        Multi-line string with one career summary block per career.

    Example output block
    --------------------
        Career: Full Stack Developer
        Required Skills: HTML, CSS, JavaScript, React, Node.js, Express.js, SQL, REST API, Git
        Suitable For: Web Development, Full Stack Development, Frontend Development, Backend Development, Problem Solving
    """
    careers = get_all_careers()
    lines: List[str] = []

    for career in careers:
        title = career.get("title", "")
        skills = ", ".join(career.get("required_skills", []))
        interests = ", ".join(career.get("suitable_for_interests", []))
        career_id = career.get("career_id", "")
        difficulty = career.get("difficulty_level", "")

        lines.append(f"Career: {title}")
        lines.append(f"ID: {career_id}")
        lines.append(f"Difficulty: {difficulty}")
        lines.append(f"Required Skills: {skills}")
        lines.append(f"Suitable For Interests: {interests}")
        lines.append("")  # blank separator between entries

    return "\n".join(lines).strip()
