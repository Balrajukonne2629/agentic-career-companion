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
# Per-skill readiness score
# ---------------------------------------------------------------------------

# Keyword groups that share a conceptual domain.
# If a student has ANY skill in a group, they get partial credit toward
# others in the same group.
_SKILL_DOMAINS: List[List[str]] = [
    ["python", "pandas", "numpy", "scikit-learn", "matplotlib", "seaborn", "jupyter"],
    ["tensorflow", "pytorch", "keras", "deep learning", "neural", "transformer"],
    ["nlp", "natural language processing", "hugging face", "spacy", "nltk", "bert"],
    ["mlops", "model deployment", "mlflow", "bentoml", "seldon", "kubeflow", "airflow"],
    ["sql", "mysql", "postgresql", "sqlite", "database", "query"],
    ["javascript", "typescript", "node.js", "express.js", "react", "vue", "angular", "next.js"],
    ["html", "css", "sass", "tailwind", "bootstrap", "frontend", "ui"],
    ["rest api", "graphql", "api", "http", "fetch", "axios"],
    ["docker", "kubernetes", "ci/cd", "devops", "jenkins", "github actions"],
    ["aws", "azure", "google cloud", "cloud", "s3", "ec2", "lambda"],
    ["linux", "bash", "shell", "terminal", "networking"],
    ["java", "spring", "maven", "gradle", "jvm"],
    ["c++", "c", "c#", ".net", "unreal"],
    ["git", "github", "version control", "gitlab"],
    ["machine learning", "feature engineering", "model evaluation", "scikit", "xgboost"],
    ["data visualization", "tableau", "power bi", "looker", "matplotlib", "seaborn"],
    ["data engineering", "etl", "spark", "kafka", "airflow", "dbt", "snowflake"],
    ["cybersecurity", "penetration testing", "ethical hacking", "owasp", "siem"],
    ["react native", "flutter", "mobile", "android", "ios", "swift", "kotlin", "dart"],
    ["figma", "ux", "ui design", "wireframe", "prototype", "usability"],
    ["system design", "architecture", "microservices", "distributed"],
]


def _related_skill_overlap(skill: str, student_skills_lc: set) -> float:
    """
    Return a 0.0-1.0 overlap score:
    how many skills in the same domain as `skill` does the student already know?
    """
    skill_lc = skill.lower()
    for domain in _SKILL_DOMAINS:
        if any(kw in skill_lc or skill_lc in kw for kw in domain):
            known = sum(1 for kw in domain if any(kw in s or s in kw for s in student_skills_lc))
            overlap = known / max(len(domain), 1)
            return min(overlap, 1.0)
    return 0.0


_PRIORITY_BASE: Dict[str, int] = {
    "Critical":   18,   # Student has almost none of the prerequisite knowledge
    "Important":  42,   # Student has some adjacent knowledge
    "Beneficial": 62,   # Nice-to-have — student can manage without it
}


def _compute_readiness_score(
    skill: str,
    priority: str,
    student_skills_lc: set,
    cgpa: float,
    skill_index: int,
    total_skills: int,
) -> int:
    """
    Compute a realistic readiness percentage (0-100) for a single gap skill.

    Formula
    -------
    base        = priority bucket (Critical 18 / Important 42 / Beneficial 62)
    overlap     = +0..25 from related skills the student already knows
    cgpa_bonus  = +0..10 based on CGPA (higher CGPA → picks up skills faster)
    position    = -0..8 light penalty: harder / less-common skills rank lower
    jitter      = ±3 deterministic pseudo-randomness to avoid identical values
    """
    base = _PRIORITY_BASE.get(priority, 30)
    overlap = _related_skill_overlap(skill, student_skills_lc)
    overlap_bonus = round(overlap * 25)
    cgpa_bonus = round(min(max(cgpa - 5.0, 0) / 5.0, 1.0) * 10)
    position_penalty = round((skill_index / max(total_skills, 1)) * 8)
    # Deterministic jitter using character sum so same skill always gets same delta
    jitter = (sum(ord(c) for c in skill.lower()) % 7) - 3
    score = base + overlap_bonus + cgpa_bonus - position_penalty + jitter
    return max(10, min(95, score))


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

    # Step 2 — Prioritise required_gap via Python logic
    skills_to_learn: List[Dict[str, Any]] = []
    cgpa = float(student_profile.get("cgpa") or 0.0)
    all_gap_skills_ordered = gaps["required_gap"] + gaps["beneficial_gap"]
    total_gap = len(all_gap_skills_ordered)

    for idx, skill in enumerate(gaps["required_gap"]):
        priority = _fallback_priority(skill, student_skills_lc)
        readiness = _compute_readiness_score(
            skill, priority, student_skills_lc, cgpa, idx, total_gap
        )
        skills_to_learn.append({
            "skill":           skill,
            "priority":        priority,
            "reason":          f"Required skill for {target_career} not yet in your toolkit.",
            "readiness_score": readiness,
        })

    # Append beneficial (nice-to-have) gaps — always "Beneficial" priority
    for idx, skill in enumerate(gaps["beneficial_gap"]):
        global_idx = len(gaps["required_gap"]) + idx
        readiness = _compute_readiness_score(
            skill, "Beneficial", student_skills_lc, cgpa, global_idx, total_gap
        )
        skills_to_learn.append({
            "skill":           skill,
            "priority":        "Beneficial",
            "reason":          f"Nice-to-have for {target_career} that improves employability.",
            "readiness_score": readiness,
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

    # Top missing skills sorted by readiness_score ascending (biggest gaps first)
    critical_and_important = [
        s for s in skills_to_learn if s["priority"] in ("Critical", "Important")
    ]
    top_missing_skills = [
        s["skill"]
        for s in sorted(critical_and_important, key=lambda x: x["readiness_score"])
    ]

    result = {
        "target_career":      target_career,
        "target_career_id":   target_career_id,
        "skills_already_have": gaps["skills_already_have"],
        "skills_to_learn":    skills_to_learn,
        "tools_to_learn":     tools_to_learn,
        "top_missing_skills": top_missing_skills,
        "gap_summary":        summary,
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
