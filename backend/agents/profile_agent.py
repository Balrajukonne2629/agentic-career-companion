"""
agents/profile_agent.py
=======================
Agent 2: Student Profile Agent

Responsibilities
----------------
- Granite: Generate a 2-3 sentence narrative summary, a strengths array,
  and a development_areas array from the validated student profile.
- Python: Compute profile_tier using rule-based CGPA + skill-count thresholds.
- Python: Compute career_readiness_score (0–100) via a deterministic formula.
- Python: Assign score_band label from career_readiness_score.
- Python: Estimate time-to-ready (months) from score + availability_per_week.

Profile Tier Rules
------------------
    strong            : cgpa >= 8.0  AND  skill_count >= 5
    moderate          : cgpa >= 6.5  AND  skill_count >= 3   (or cgpa >= 8.0)
    needs-development : everything else

Career Readiness Score Formula (0–100, integers)
-------------------------------------------------
    cgpa_component        = min(cgpa / 10.0, 1.0) * 35        # 35 pts max
    skill_component       = min(skill_count / 8.0, 1.0) * 40  # 40 pts max
    interest_component    = min(len(interests) / 3.0, 1.0) * 15  # 15 pts max
    goal_component        = 10 if career_goal else 0            # 10 pts max
    score = int(cgpa_component + skill_component + interest_component + goal_component)

Score Bands
-----------
    >= 80  : "Career Ready"
    >= 60  : "On Track"
    >= 40  : "Developing"
    < 40   : "Foundational"

Estimated Time-to-Ready (months)
---------------------------------
    base_months = ceil((100 - score) / 10)     # each 10-point gap = 1 month
    availability_factor:
        < 8 hrs/week   → multiply by 1.5
        8–14 hrs/week  → multiply by 1.0
        >= 15 hrs/week → multiply by 0.7
    result = max(1, round(base_months * factor))

Models used
-----------
    call_granite_fast (granite-3-8b-instruct)
"""

import math
from typing import Any, Dict, List

from errors import GraniteCallError, GraniteParseError
from logger import get_logger
from utils.granite_client import call_granite_fast
from utils.json_parser import parse_granite_json

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Score / tier thresholds
# ---------------------------------------------------------------------------

_TIER_STRONG_CGPA      = 8.0
_TIER_STRONG_SKILLS    = 5
_TIER_MODERATE_CGPA    = 6.5
_TIER_MODERATE_SKILLS  = 3

_BAND_CAREER_READY = 80
_BAND_ON_TRACK     = 60
_BAND_DEVELOPING   = 40

# ---------------------------------------------------------------------------
# Granite prompt template
# ---------------------------------------------------------------------------

_PROFILE_PROMPT_TEMPLATE = """\
You are an expert career counselor. Analyze the following student profile and return a JSON object with exactly these keys:

- "summary": A 2-3 sentence professional narrative about the student, mentioning their academic standing, skills, and career goal.
- "strengths": An array of 3-5 specific strength strings (e.g., "Strong Java and C++ background").
- "development_areas": An array of 2-4 specific areas the student should improve (e.g., "Limited web development experience").

Rules:
- Output ONLY valid JSON. No markdown, no explanation, no extra text.
- Be specific, not generic. Reference actual skills and goals from the profile.
- "development_areas" should be honest, constructive gaps — not repetitions of strengths.

Student Profile:
- Name: {name}
- Branch: {branch}
- Year: Year {year}
- CGPA: {cgpa}
- Skills: {skills}
- Interests: {interests}
- Career Goal: {career_goal}

Output JSON:
"""


# ---------------------------------------------------------------------------
# Deterministic Python computation
# ---------------------------------------------------------------------------

def _compute_tier(cgpa: float, skill_count: int) -> str:
    """Return profile tier string based on CGPA and skill count."""
    if cgpa >= _TIER_STRONG_CGPA and skill_count >= _TIER_STRONG_SKILLS:
        return "strong"
    if cgpa >= _TIER_MODERATE_CGPA and skill_count >= _TIER_MODERATE_SKILLS:
        return "moderate"
    if cgpa >= _TIER_STRONG_CGPA:
        # High CGPA but fewer skills — still moderate
        return "moderate"
    return "needs-development"


def _compute_score(
    cgpa: float,
    skill_count: int,
    interest_count: int,
    has_career_goal: bool,
) -> int:
    """
    Compute the career_readiness_score (0–100, integer).

    See module-level formula docstring.
    """
    cgpa_component     = min(cgpa / 10.0, 1.0) * 35.0
    skill_component    = min(skill_count / 8.0, 1.0) * 40.0
    interest_component = min(interest_count / 3.0, 1.0) * 15.0
    goal_component     = 10.0 if has_career_goal else 0.0
    return int(cgpa_component + skill_component + interest_component + goal_component)


def _score_band(score: int) -> str:
    """Map a readiness score to a human-readable band label."""
    if score >= _BAND_CAREER_READY:
        return "Career Ready"
    if score >= _BAND_ON_TRACK:
        return "On Track"
    if score >= _BAND_DEVELOPING:
        return "Developing"
    return "Foundational"


def _estimate_time_to_ready(score: int, availability_per_week: int) -> int:
    """
    Estimate months until career-ready.

    Returns minimum 1.
    """
    gap = max(0, 100 - score)
    base_months = math.ceil(gap / 10.0)

    if availability_per_week < 8:
        factor = 1.5
    elif availability_per_week >= 15:
        factor = 0.7
    else:
        factor = 1.0

    return max(1, round(base_months * factor))


# ---------------------------------------------------------------------------
# Granite call with fallback
# ---------------------------------------------------------------------------

def _call_granite_for_narrative(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call Granite to generate summary, strengths, and development_areas.

    Falls back to sensible generic defaults if the call fails or produces
    invalid JSON, so the rest of the pipeline is never blocked.

    Returns
    -------
    dict
        Keys: summary (str), strengths (list[str]), development_areas (list[str])
    """
    skills_str    = ", ".join(profile.get("skills", [])) or "none listed"
    interests_str = ", ".join(profile.get("interests", [])) or "not specified"

    prompt = _PROFILE_PROMPT_TEMPLATE.format(
        name        = profile.get("name", "Student"),
        branch      = profile.get("branch", "Engineering"),
        year        = profile.get("year", "?"),
        cgpa        = profile.get("cgpa", "N/A"),
        skills      = skills_str,
        interests   = interests_str,
        career_goal = profile.get("career_goal", "not specified"),
    )

    try:
        raw = call_granite_fast(prompt, params={"max_new_tokens": 512})
        parsed = parse_granite_json(raw)

        if not isinstance(parsed, dict):
            raise GraniteParseError(
                "Profile Agent: Granite returned non-dict JSON.",
                detail=repr(parsed),
            )

        summary = parsed.get("summary", "")
        strengths = parsed.get("strengths", [])
        dev_areas = parsed.get("development_areas", [])

        # Validate types — fall through to fallback if malformed
        if (
            isinstance(summary, str) and summary.strip()
            and isinstance(strengths, list) and len(strengths) >= 1
            and isinstance(dev_areas, list) and len(dev_areas) >= 1
        ):
            log.info("Profile Agent: Granite narrative generated successfully.")
            return {
                "summary": summary.strip(),
                "strengths": [str(s).strip() for s in strengths if str(s).strip()],
                "development_areas": [str(d).strip() for d in dev_areas if str(d).strip()],
            }

        log.warning("Profile Agent: Granite returned incomplete narrative — using fallback.")

    except (GraniteCallError, GraniteParseError) as exc:
        log.warning("Granite unavailable — using deterministic fallback")

    return _build_fallback_narrative(profile)


def _build_fallback_narrative(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a deterministic summary/strengths/development_areas without Granite.

    Called when the Granite call fails or returns malformed output.
    """
    name        = profile.get("name", "The student")
    branch      = profile.get("branch", "Engineering")
    year        = profile.get("year", "?")
    cgpa        = profile.get("cgpa", 0.0)
    skills      = profile.get("skills", [])
    career_goal = profile.get("career_goal", "a software career")

    summary = (
        f"{name} is a Year {year} {branch} student with a CGPA of {cgpa}. "
        f"They have practical exposure to {', '.join(skills[:3]) if skills else 'programming fundamentals'}. "
        f"Their stated career goal is to become a {career_goal}."
    )

    strengths = []
    if cgpa >= 8.0:
        strengths.append(f"Strong academic performance (CGPA {cgpa})")
    elif cgpa >= 7.0:
        strengths.append(f"Solid academic standing (CGPA {cgpa})")
    if skills:
        strengths.append(f"Practical skills in {', '.join(skills[:4])}")
    if career_goal:
        strengths.append(f"Clear career direction towards {career_goal}")
    if not strengths:
        strengths.append("Motivated to pursue a technology career")

    dev_areas = []
    if len(skills) < 4:
        dev_areas.append("Expand technical skill set with additional tools and frameworks")
    if cgpa < 7.5:
        dev_areas.append("Strengthen academic performance and theoretical fundamentals")
    dev_areas.append("Build project experience to demonstrate practical abilities")
    if len(dev_areas) < 2:
        dev_areas.append("Pursue industry certifications to validate skills")

    return {
        "summary": summary,
        "strengths": strengths,
        "development_areas": dev_areas,
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(student_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Profile Agent.

    Parameters
    ----------
    student_profile : dict
        Validated 9-field student profile from the Validation Agent.

    Returns
    -------
    dict
        {
            "summary": str,
            "strengths": [str, ...],
            "development_areas": [str, ...],
            "profile_tier": "strong" | "moderate" | "needs-development",
            "career_readiness_score": int,
            "score_band": str,
            "estimated_time_to_ready_months": int,
            "learning_style": str
        }
    """
    log.info("Profile Agent: starting for '%s'", student_profile.get("name"))

    cgpa              = float(student_profile.get("cgpa") or 0.0)
    skills: List[str] = student_profile.get("skills") or []
    interests: List[str] = student_profile.get("interests") or []
    career_goal       = student_profile.get("career_goal", "")
    availability      = int(student_profile.get("availability_per_week") or 10)
    learning_style    = student_profile.get("preferred_learning_style") or "mixed"

    skill_count    = len(skills)
    interest_count = len(interests)

    # --- Deterministic Python computations ---
    tier       = _compute_tier(cgpa, skill_count)
    score      = _compute_score(cgpa, skill_count, interest_count, bool(career_goal))
    band       = _score_band(score)
    time_ready = _estimate_time_to_ready(score, availability)

    log.info(
        "Profile Agent: tier=%s score=%d band=%s time_to_ready=%d months",
        tier, score, band, time_ready,
    )

    # --- Granite narrative generation (with fallback) ---
    narrative = _call_granite_for_narrative(student_profile)

    result = {
        "summary":                      narrative["summary"],
        "strengths":                    narrative["strengths"],
        "development_areas":            narrative["development_areas"],
        "profile_tier":                 tier,
        "career_readiness_score":       score,
        "score_band":                   band,
        "estimated_time_to_ready_months": time_ready,
        "learning_style":               learning_style,
    }

    log.info("Profile Agent: complete for '%s'", student_profile.get("name"))
    return result
