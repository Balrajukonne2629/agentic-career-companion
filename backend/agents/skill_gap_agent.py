"""
agents/skill_gap_agent.py
=========================
Agent 4: Skill Gap Agent

Responsibilities
----------------
- Python: Set-difference for skills_to_learn (required_skills − student_skills).
- Python: Set-difference for nice_to_have gaps (always "Beneficial" priority).
- Python: Set-difference for tools_to_learn (core_tools − student_tools).
- Granite: Prioritise and explain each skills_to_learn item.
- Python: tools_to_learn items always carry "Important" priority with generic reasons.
- Python: Compute gap_summary counts.
- Python: Handle zero-gap edge case gracefully.
- All skill comparisons are case-insensitive.

Skill Priority Mapping (Granite responsibility)
-----------------------------------------------
    Critical   : skill is in required_skills AND student has zero overlapping related skills
    Important  : skill is in required_skills but student has adjacent knowledge
    Beneficial : skill is in nice_to_have_skills only

Python fallback priority assignment when Granite fails
------------------------------------------------------
    required_skills gap items → "Critical" by default
    nice_to_have gap items    → "Beneficial" always

Models used
-----------
    call_granite_strong (granite-13b-instruct-v2)
"""

from typing import Any, Dict, List, Optional

from logger import get_logger
from utils.career_loader import get_career_by_id

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Granite prompt template
# ---------------------------------------------------------------------------

# Skill Gap Agent uses pure Python rules and heuristics only.


# ---------------------------------------------------------------------------
# Deterministic set-difference computation
# ---------------------------------------------------------------------------

def _normalise_set(items: List[str]) -> set:
    return {s.lower().strip() for s in items if s}


def _compute_gaps(
    student_profile: Dict[str, Any],
    career: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Pure-Python gap computation.

    Returns
    -------
    dict with keys:
        skills_already_have : list of canonical skill strings (case from KB)
        required_gap        : list of canonical required skill strings student is missing
        beneficial_gap      : list of canonical nice-to-have skill strings student is missing
        tools_gap           : list of canonical core_tool strings student is missing
    """
    student_skills = student_profile.get("skills", [])
    student_lc     = _normalise_set(student_skills)

    required_skills = career.get("required_skills", [])
    nice_to_have    = career.get("nice_to_have_skills", [])
    core_tools      = career.get("core_tools", [])

    req_lc  = _normalise_set(required_skills)
    ntha_lc = _normalise_set(nice_to_have)
    tool_lc = _normalise_set(core_tools)

    # Preserve canonical casing from KB
    skills_have  = [s for s in required_skills if s.lower().strip() in student_lc]
    req_gap      = [s for s in required_skills if s.lower().strip() not in student_lc]
    bene_gap     = [s for s in nice_to_have   if s.lower().strip() not in student_lc]
    tools_gap    = [t for t in core_tools     if t.lower().strip() not in student_lc]

    return {
        "skills_already_have": skills_have,
        "required_gap":        req_gap,
        "beneficial_gap":      bene_gap,
        "tools_gap":           tools_gap,
    }




def _fallback_priority(skill: str, student_skills_lc: set) -> str:
    """
    Assign a default priority without Granite.

    Heuristic: if the student has ANY skill that starts with the same first
    word as the gap skill (e.g., student has "Node.js", gap is "Express.js"),
    call it "Important". Otherwise "Critical".
    """
    skill_word = skill.lower().split()[0] if skill else ""
    for s in student_skills_lc:
        if s.startswith(skill_word) or skill_word.startswith(s.split()[0]):
            return "Important"
    return "Critical"


# ---------------------------------------------------------------------------
# Gap summary counter
# ---------------------------------------------------------------------------

def _compute_summary(
    skills_to_learn: List[Dict[str, Any]],
    tools_to_learn:  List[Dict[str, Any]],
) -> Dict[str, int]:
    critical   = sum(1 for s in skills_to_learn if s["priority"] == "Critical")
    important  = sum(1 for s in skills_to_learn if s["priority"] == "Important")
    beneficial = sum(1 for s in skills_to_learn if s["priority"] == "Beneficial")
    tools_cnt  = len(tools_to_learn)
    return {
        "critical_count":   critical,
        "important_count":  important,
        "beneficial_count": beneficial,
        "tools_count":      tools_cnt,
        "total_gap_items":  critical + important + beneficial + tools_cnt,
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(
    student_profile: Dict[str, Any],
    top_recommendation: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run the Skill Gap Agent.

    Parameters
    ----------
    student_profile : dict
        Validated 9-field student profile.
    top_recommendation : dict
        The first item from the Career Recommendation Agent output.

    Returns
    -------
    dict
        {
            "target_career": str,
            "target_career_id": str,
            "skills_already_have": [str, ...],
            "skills_to_learn": [
                {"skill": str, "priority": "Critical"|"Important"|"Beneficial", "reason": str}
            ],
            "tools_to_learn": [
                {"tool": str, "priority": "Important", "reason": str}
            ],
            "gap_summary": {
                "critical_count": int,
                "important_count": int,
                "beneficial_count": int,
                "tools_count": int,
                "total_gap_items": int
            }
        }
    """
    target_career    = top_recommendation.get("title", "")
    target_career_id = top_recommendation.get("career_id", "")

    log.info(
        "Skill Gap Agent: starting for '%s' → '%s'",
        student_profile.get("name"), target_career,
    )

    # Load full career data from KB
    career_kb = get_career_by_id(target_career_id)
    if career_kb is None:
        log.warning(
            "Skill Gap Agent: career_id '%s' not found in KB — using recommendation data only.",
            target_career_id,
        )
        # Build a minimal career dict from the recommendation
        career_kb = {
            "career_id":        target_career_id,
            "title":            target_career,
            "required_skills":  [],
            "nice_to_have_skills": [],
            "core_tools":       [],
        }

    # Step 1 — Deterministic set-difference
    gaps = _compute_gaps(student_profile, career_kb)
    student_skills     = student_profile.get("skills", [])
    student_skills_lc  = _normalise_set(student_skills)

    # Step 2 — Prioritise required_gap via Python logic (Skill Gap Agent does NOT call Granite)
    skills_to_learn: List[Dict[str, Any]] = []
    for skill in gaps["required_gap"]:
        priority = _fallback_priority(skill, student_skills_lc)
        skills_to_learn.append({
            "skill":    skill,
            "priority": priority,
            "reason":   f"Required skill for {target_career} not yet in your toolkit.",
        })

    # Append beneficial (nice-to-have) gaps — always "Beneficial" priority
    for skill in gaps["beneficial_gap"]:
        skills_to_learn.append({
            "skill":    skill,
            "priority": "Beneficial",
            "reason":   f"Nice-to-have for {target_career} that improves employability.",
        })

    # Step 3 — tools_to_learn (purely deterministic, always "Important")
    tools_to_learn: List[Dict[str, Any]] = []
    for tool in gaps["tools_gap"]:
        tools_to_learn.append({
            "tool":     tool,
            "priority": "Important",
            "reason":   f"Core tool used by {target_career}s in day-to-day work.",
        })

    # Step 4 — Gap summary
    summary = _compute_summary(skills_to_learn, tools_to_learn)

    result = {
        "target_career":    target_career,
        "target_career_id": target_career_id,
        "skills_already_have": gaps["skills_already_have"],
        "skills_to_learn":  skills_to_learn,
        "tools_to_learn":   tools_to_learn,
        "gap_summary":      summary,
    }

    # Calculate readiness score deterministically
    cgpa = float(student_profile.get("cgpa") or 0.0)
    skill_count = len(student_skills)
    interest_count = len(student_profile.get("interests", []))
    has_career_goal = bool(student_profile.get("career_goal"))
    cgpa_component     = min(cgpa / 10.0, 1.0) * 35.0
    skill_component    = min(skill_count / 8.0, 1.0) * 40.0
    interest_component = min(interest_count / 3.0, 1.0) * 15.0
    goal_component     = 10.0 if has_career_goal else 0.0
    readiness_score = int(cgpa_component + skill_component + interest_component + goal_component)

    # Print SKILL GAP AGENT stage log
    print("==================================================")
    print("SKILL GAP AGENT")
    print("==================================================")
    print("Current Skills:")
    print(gaps["skills_already_have"])
    print()
    print("Missing Skills:")
    print([s["skill"] for s in skills_to_learn if s["priority"] in ("Critical", "Important")])
    print()
    print("Readiness Score:")
    print(readiness_score)
    print()

    log.info(
        "Skill Gap Agent: complete — critical=%d important=%d beneficial=%d tools=%d",
        summary["critical_count"], summary["important_count"],
        summary["beneficial_count"], summary["tools_count"],
    )
    return result
