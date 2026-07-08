"""
agents/career_recommendation_agent.py
======================================
Agent 3: Career Recommendation Agent

Responsibilities
----------------
- Python: Load career_data.json via career_loader.py.
- Python: Compute deterministic confidence score per career (skill overlap + interest overlap).
- Python: Apply difficulty_level vs profile_tier penalty.
- Granite: Generate concise reasoning strings for the top-3 careers.
- Python: Fallback keyword matcher if Granite call fails (uses pre-ranked results).
- Write result to Flask session["recommendations"].

Confidence Score Formula (0–100, per career)
--------------------------------------------
    skill_overlap     = |student_skills ∩ required_skills| / max(|required_skills|, 1)
    interest_overlap  = |student_interests ∩ suitable_for_interests| / max(|suitable_for_interests|, 1)
    base_score        = (skill_overlap * 0.70 + interest_overlap * 0.30) * 100

    goal_boost:  +10 if career title or career_id appears in student career_goal (case-insensitive)
    bonus_skills: +5  if student has any nice_to_have_skills for the career

    raw = min(int(base_score + goal_boost + bonus_skills), 100)

Difficulty Penalty
------------------
    profile_tier vs career difficulty_level:
        strong   + advanced          → 0
        strong   + moderate          → 0
        strong   + beginner-friendly → 0
        moderate + advanced          → -5
        moderate + moderate          → 0
        moderate + beginner-friendly → 0
        needs-development + advanced → -10
        needs-development + moderate → -5
        needs-development + beginner-friendly → 0

    confidence_percent = max(0, raw - penalty)

Top-3 Selection
---------------
    Sort all careers descending by confidence_percent.
    Take top 3. If fewer than 3 careers score > 0, pad with the next non-zero entries.
    If still fewer than 3, duplicate the last entry with decremented confidence.

Models used
-----------
    call_granite_strong (granite-13b-instruct-v2)
"""

from typing import Any, Dict, List, Optional, Tuple

from errors import GraniteCallError, GraniteParseError
from logger import get_logger
from utils.career_loader import get_all_careers, get_career_by_id, serialize_careers_for_prompt
from utils.granite_client import call_granite_strong
from utils.json_parser import parse_granite_json

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Difficulty penalty table
# ---------------------------------------------------------------------------

_DIFFICULTY_PENALTY: Dict[Tuple[str, str], int] = {
    ("strong",            "advanced"):          0,
    ("strong",            "moderate"):          0,
    ("strong",            "beginner-friendly"): 0,
    ("moderate",          "advanced"):         -5,
    ("moderate",          "moderate"):          0,
    ("moderate",          "beginner-friendly"): 0,
    ("needs-development", "advanced"):        -10,
    ("needs-development", "moderate"):         -5,
    ("needs-development", "beginner-friendly"): 0,
}


# ---------------------------------------------------------------------------
# Granite prompt template
# ---------------------------------------------------------------------------

_RECOMMEND_PROMPT_TEMPLATE = """\
You are an expert career counselor. Based on the student profile and the ranked career recommendations below, write a short, specific 2-sentence reasoning for each of the top 3 careers explaining WHY this career is a good match for THIS specific student.

Rules:
- Output ONLY a valid JSON array of exactly 3 objects.
- Each object must have exactly two keys: "career_id" (string) and "reasoning" (string).
- The reasoning must reference the student's actual skills, interests, and career goal.
- Do NOT repeat information from the career description verbatim.
- Do NOT add any text outside the JSON array.

Student Profile:
- Name: {name}
- Skills: {skills}
- Interests: {interests}
- Career Goal: {career_goal}
- Profile Tier: {profile_tier}

Top 3 Career Candidates (pre-ranked by skill match):
{career_candidates}

Output JSON array:
"""


# ---------------------------------------------------------------------------
# Deterministic scoring
# ---------------------------------------------------------------------------

def _normalise_set(items: List[str]) -> set:
    """Lower-case a list of strings into a set for case-insensitive comparison."""
    return {s.lower().strip() for s in items if s and s.strip()}


def _score_career(
    career: Dict[str, Any],
    student_skills_lc: set,
    student_interests_lc: set,
    career_goal_lc: str,
    profile_tier: str,
) -> int:
    """
    Compute confidence_percent for a single career entry.

    Returns int 0–100.
    """
    required_skills     = career.get("required_skills", [])
    nice_to_have_skills = career.get("nice_to_have_skills", [])
    suitable_interests  = career.get("suitable_for_interests", [])
    career_title_lc     = career.get("title", "").lower()
    career_id_lc        = career.get("career_id", "").lower()
    difficulty          = career.get("difficulty_level", "moderate")

    req_lc  = _normalise_set(required_skills)
    ntha_lc = _normalise_set(nice_to_have_skills)
    int_lc  = _normalise_set(suitable_interests)

    # Skill and interest overlaps
    skill_overlap    = len(student_skills_lc & req_lc) / max(len(req_lc), 1)
    interest_overlap = len(student_interests_lc & int_lc) / max(len(int_lc), 1)

    base_score = (skill_overlap * 0.70 + interest_overlap * 0.30) * 100.0

    # Goal boost
    goal_boost = 10 if (career_title_lc in career_goal_lc or career_id_lc in career_goal_lc) else 0

    # Bonus for nice-to-have skills
    bonus = 5 if (student_skills_lc & ntha_lc) else 0

    raw = min(int(base_score + goal_boost + bonus), 100)

    # Difficulty penalty
    penalty = _DIFFICULTY_PENALTY.get((profile_tier, difficulty), 0)
    return max(0, raw + penalty)  # penalty values are negative


def _rank_careers(
    student_profile: Dict[str, Any],
    profile_analysis: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Score and sort all careers, returning a list of dicts with career data +
    confidence_percent + matching_skills injected.
    """
    student_skills    = student_profile.get("skills", [])
    student_interests = student_profile.get("interests", [])
    career_goal       = (student_profile.get("career_goal") or "").lower()
    profile_tier      = (profile_analysis.get("profile_tier") or "moderate")

    student_skills_lc    = _normalise_set(student_skills)
    student_interests_lc = _normalise_set(student_interests)

    scored: List[Tuple[int, Dict[str, Any]]] = []
    for career in get_all_careers():
        score = _score_career(
            career,
            student_skills_lc,
            student_interests_lc,
            career_goal,
            profile_tier,
        )
        # Compute matching_skills for the output
        req_lc  = _normalise_set(career.get("required_skills", []))
        matched = [s for s in student_skills if s.lower().strip() in req_lc]

        enriched = dict(career)
        enriched["confidence_percent"] = score
        enriched["matching_skills"]    = matched
        scored.append((score, enriched))

    scored.sort(key=lambda t: t[0], reverse=True)
    return [item for _, item in scored]


def _build_top3(ranked: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract the top-3 careers from a ranked list.

    Guarantees exactly 3 items are returned (duplicates last if needed).
    """
    top = [c for c in ranked[:3] if c["confidence_percent"] > 0]

    # If fewer than 3 scored > 0, fill with the next zero-score entries
    if len(top) < 3:
        for c in ranked[len(top):]:
            top.append(c)
            if len(top) == 3:
                break

    # If the KB has fewer than 3 careers at all, duplicate last
    while len(top) < 3 and top:
        last = dict(top[-1])
        last["confidence_percent"] = max(0, last["confidence_percent"] - 5)
        top.append(last)

    return top[:3]


# ---------------------------------------------------------------------------
# Granite reasoning generation
# ---------------------------------------------------------------------------

def _build_candidate_block(top3: List[Dict[str, Any]]) -> str:
    """Produce the career_candidates text block for the Granite prompt."""
    lines = []
    for rank, career in enumerate(top3, 1):
        matching = ", ".join(career.get("matching_skills", [])) or "none yet"
        lines.append(
            f"{rank}. {career['title']} (ID: {career['career_id']}, "
            f"Confidence: {career['confidence_percent']}%, "
            f"Matching Skills: {matching})"
        )
    return "\n".join(lines)


def _call_granite_for_reasoning(
    student_profile: Dict[str, Any],
    profile_analysis: Dict[str, Any],
    top3: List[Dict[str, Any]],
) -> List[Optional[str]]:
    """
    Call Granite to generate reasoning strings for each of the top-3 careers.

    Returns a list of 3 reasoning strings (or None placeholders that the
    caller replaces with fallback text).
    """
    skills_str    = ", ".join(student_profile.get("skills", [])) or "none listed"
    interests_str = ", ".join(student_profile.get("interests", [])) or "not specified"

    prompt = _RECOMMEND_PROMPT_TEMPLATE.format(
        name             = student_profile.get("name", "Student"),
        skills           = skills_str,
        interests        = interests_str,
        career_goal      = student_profile.get("career_goal", "not specified"),
        profile_tier     = profile_analysis.get("profile_tier", "moderate"),
        career_candidates = _build_candidate_block(top3),
    )

    try:
        raw = call_granite_strong(prompt, params={"max_new_tokens": 600})
        parsed = parse_granite_json(raw)

        if not isinstance(parsed, list):
            log.warning("Career Agent: Granite returned non-list JSON — using fallback reasoning.")
            return [None, None, None]

        # Map career_id → reasoning from Granite output
        reasoning_map: Dict[str, str] = {}
        for item in parsed:
            if isinstance(item, dict):
                cid = item.get("career_id", "")
                rsn = item.get("reasoning", "")
                if cid and rsn:
                    reasoning_map[cid] = str(rsn).strip()

        results = []
        for career in top3:
            rsn = reasoning_map.get(career["career_id"])
            results.append(rsn if rsn else None)

        log.info("Career Agent: Granite reasoning generated for %d careers.", sum(1 for r in results if r))
        return results

    except (GraniteCallError, GraniteParseError) as exc:
        log.warning("Granite unavailable — using deterministic fallback")
        return [None, None, None]


def _fallback_reasoning(career: Dict[str, Any], student_profile: Dict[str, Any]) -> str:
    """Generate a deterministic fallback reasoning string when Granite fails."""
    matched = career.get("matching_skills", [])
    title   = career.get("title", "this career")
    goal    = student_profile.get("career_goal", "")

    if matched:
        skill_part = f"Your existing skills in {', '.join(matched[:3])} provide a strong starting foundation."
    else:
        skill_part = "This career aligns with your stated interests and academic background."

    goal_part = (
        f" It directly aligns with your goal of becoming a {goal}."
        if goal else " It is a strong match for your profile."
    )

    return skill_part + goal_part


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(
    student_profile: Dict[str, Any],
    profile_analysis: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Run the Career Recommendation Agent.

    Parameters
    ----------
    student_profile : dict
        Validated 9-field student profile.
    profile_analysis : dict
        Output from the Profile Agent including profile_tier.

    Returns
    -------
    list
        Exactly 3 career recommendation objects:
        [
            {
                "career_id": str,
                "title": str,
                "confidence_percent": int,
                "reasoning": str,
                "matching_skills": [str, ...],
                "industry_sector": str
            },
            ...
        ]
    """
    log.info(
        "Career Recommendation Agent: starting for '%s'",
        student_profile.get("name"),
    )

    # Step 1 — Deterministic ranking
    ranked = _rank_careers(student_profile, profile_analysis)
    top3   = _build_top3(ranked)

    log.info(
        "Career Agent: top-3 by score → %s",
        [(c["title"], c["confidence_percent"]) for c in top3],
    )

    # Step 2 — Granite reasoning (with per-career fallback)
    reasoning_list = _call_granite_for_reasoning(student_profile, profile_analysis, top3)

    # Step 3 — Assemble output
    results = []
    for career, reasoning in zip(top3, reasoning_list):
        if not reasoning:
            reasoning = _fallback_reasoning(career, student_profile)

        results.append({
            "career_id":         career["career_id"],
            "title":             career["title"],
            "confidence_percent": career["confidence_percent"],
            "reasoning":         reasoning,
            "matching_skills":   career["matching_skills"],
            "industry_sector":   career.get("industry_sector", ""),
        })

    log.info(
        "Career Recommendation Agent: complete — top career='%s' (%d%%)",
        results[0]["title"] if results else "none",
        results[0]["confidence_percent"] if results else 0,
    )
    return results
