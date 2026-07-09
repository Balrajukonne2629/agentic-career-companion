"""
agents/roadmap_agent.py
=======================
Agent 5: Roadmap Agent

Responsibilities
----------------
- Python: Load certifications, suggested_projects, learning_prerequisites
  from career_data.json for the target career (via career_loader.py).
- Granite: Generate structured 30/60/90-day learning plan text (focus, weekly_goals, resources).
- Python: Select certifications from KB (not Granite-generated).
- Python: Select projects from KB (not Granite-generated).
- Modulation: profile_tier → starting difficulty for project/cert selection.
- Modulation: availability_per_week → weekly goal count (see table below).
- Modulation: preferred_learning_style → resource type hints injected into prompt.
- Write result to Flask session["roadmap"].

Availability → weekly goal count mapping
-----------------------------------------
    < 8 hrs/week  → 1–2 goals per week   (pace="slow")
    8–14 hrs/week → 2–3 goals per week   (pace="normal")
    ≥ 15 hrs/week → 3–4 goals per week   (pace="fast")

Certification selection by profile_tier
----------------------------------------
    strong            → prefer "intermediate" or "advanced" certs first
    moderate          → prefer "beginner" or "intermediate" certs first
    needs-development → prefer "beginner" certs first

Project selection by profile_tier
-----------------------------------
    strong            → pick intermediate + advanced projects
    moderate          → pick beginner + intermediate projects
    needs-development → pick beginner project first

Learning style → resource hints
--------------------------------
    visual   → "video tutorials, YouTube, LinkedIn Learning"
    reading  → "official documentation, MDN, technical books"
    hands-on → "coding challenges, project-based courses, hackathons"
    mixed    → "combination of video tutorials, official docs, and hands-on projects"

Models used
-----------
    call_granite_strong (granite-13b-instruct-v2)
"""

import math
from typing import Any, Dict, List, Optional, Tuple

from errors import GraniteCallError, GraniteParseError
from logger import get_logger
from utils.career_loader import get_career_by_id
from utils.granite_client import call_granite_strong
from utils.json_parser import parse_granite_json

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Learning style → resource hint text
# ---------------------------------------------------------------------------

_STYLE_HINTS: Dict[str, str] = {
    "visual":   "video tutorials, YouTube channels, LinkedIn Learning, and visual walkthroughs",
    "reading":  "official documentation, MDN Web Docs, technical books, and written guides",
    "hands-on": "coding challenges, project-based courses, hackathons, and hands-on labs",
    "mixed":    "a combination of video tutorials, official documentation, and hands-on projects",
}

# ---------------------------------------------------------------------------
# Career-specific fallback skill sequences
# Used when Granite is unavailable — maps career_id / title keywords → steps
# ---------------------------------------------------------------------------

_CAREER_FALLBACK_SKILLS: Dict[str, List[str]] = {
    "ml_engineer":         ["Python", "TensorFlow", "PyTorch", "scikit-learn", "MLOps", "Model Deployment", "Data Pipelines", "Model Evaluation"],
    "data_scientist":      ["Python", "Pandas", "NumPy", "Statistics", "Machine Learning", "Data Visualization", "SQL", "Jupyter Notebooks"],
    "data_analyst":        ["SQL", "Excel", "Power BI", "Tableau", "Data Visualization", "Python", "Statistical Analysis", "Dashboard Design"],
    "backend_developer":   ["REST APIs", "Databases", "Authentication", "Docker", "Deployment", "System Design", "Caching", "Microservices"],
    "frontend_developer":  ["HTML/CSS", "JavaScript", "React", "TypeScript", "State Management", "Testing", "Accessibility", "Performance Optimization"],
    "fullstack_developer": ["React", "Node.js", "REST APIs", "Databases", "Authentication", "Docker", "Deployment", "System Design"],
    "devops_engineer":     ["Linux", "Docker", "Kubernetes", "CI/CD Pipelines", "Terraform", "Monitoring", "Cloud Platforms", "Security"],
    "cloud_architect":     ["Cloud Platforms", "Networking", "Security", "Microservices", "Serverless", "Cost Optimization", "IaC", "Multi-Cloud"],
    "cybersecurity":       ["Networking", "Linux", "Ethical Hacking", "OWASP", "Penetration Testing", "SIEM Tools", "Incident Response", "Compliance"],
    "mobile_developer":    ["React Native", "Flutter", "REST APIs", "State Management", "App Store Deployment", "Performance", "UI/UX", "Push Notifications"],
    "default":             ["Core Fundamentals", "Version Control (Git)", "Problem Solving", "Project Building", "Documentation", "Testing", "Deployment", "Portfolio"],
}

# ---------------------------------------------------------------------------
# Availability → pace table
# ---------------------------------------------------------------------------

def _pace_from_availability(hours: int) -> Tuple[str, int, int]:
    """
    Returns (pace_label, min_goals_per_week, max_goals_per_week).
    """
    if hours < 8:
        return ("slow", 1, 2)
    if hours >= 15:
        return ("fast", 3, 4)
    return ("normal", 2, 3)

# ---------------------------------------------------------------------------
# KB selectors
# ---------------------------------------------------------------------------

def _select_certifications(
    career_kb: Dict[str, Any],
    profile_tier: str,
    max_count: int = 2,
) -> List[Dict[str, str]]:
    """
    Pick the most appropriate certifications from the KB entry.

    Returns a list of {name, provider, url} dicts.
    """
    certs = career_kb.get("certifications", [])
    if not certs:
        return []

    # Preferred level ordering by tier
    level_order: Dict[str, List[str]] = {
        "strong":            ["intermediate", "advanced", "beginner"],
        "moderate":          ["beginner", "intermediate", "advanced"],
        "needs-development": ["beginner", "intermediate", "advanced"],
    }
    preferred = level_order.get(profile_tier, ["beginner", "intermediate", "advanced"])

    def _level_rank(cert: Dict[str, Any]) -> int:
        lvl = cert.get("level", "intermediate")
        try:
            return preferred.index(lvl)
        except ValueError:
            return len(preferred)

    sorted_certs = sorted(certs, key=_level_rank)

    return [
        {
            "name":     c["name"],
            "provider": c.get("provider", ""),
            "url":      c.get("url", ""),
        }
        for c in sorted_certs[:max_count]
    ]


def _select_projects(
    career_kb: Dict[str, Any],
    profile_tier: str,
    phase: str,  # "first_project" or "portfolio_project"
) -> Dict[str, str]:
    """
    Pick a project from the KB for a given phase.

    first_project    → pick easiest project appropriate for tier
    portfolio_project → pick hardest project appropriate for tier
    """
    projects = career_kb.get("suggested_projects", [])
    if not projects:
        return {
            "title":       "Build a Project",
            "description": f"Apply your new skills by building a real-world {career_kb.get('title', 'career')} project.",
        }

    diff_rank = {"beginner": 0, "intermediate": 1, "advanced": 2}

    if phase == "first_project":
        # Prefer easier projects
        target_diff = {"strong": "intermediate", "moderate": "beginner", "needs-development": "beginner"}
        pref = target_diff.get(profile_tier, "beginner")
        fallback_order = ["beginner", "intermediate", "advanced"]
    else:
        # Portfolio: prefer harder
        target_diff = {"strong": "advanced", "moderate": "intermediate", "needs-development": "intermediate"}
        pref = target_diff.get(profile_tier, "intermediate")
        fallback_order = ["advanced", "intermediate", "beginner"]

    # Try exact match first, then fall back
    for level in ([pref] + [l for l in fallback_order if l != pref]):
        for proj in projects:
            if proj.get("difficulty") == level:
                return {"title": proj["title"], "description": proj["description"]}

    # Return first available
    return {"title": projects[0]["title"], "description": projects[0]["description"]}


# ---------------------------------------------------------------------------
# Granite prompt template
# ---------------------------------------------------------------------------

_ROADMAP_PROMPT_TEMPLATE = """\
You are a senior career development coach. Create a personalized 30/60/90-day learning roadmap for the following student.

Student Profile:
- Name: {name}
- Target Career: {target_career}
- Profile Tier: {profile_tier}
- Skills Already Have: {skills_have}
- Skills to Learn (Critical first): {skills_to_learn}
- Availability: {availability} hours per week ({pace} pace — {min_goals}–{max_goals} goals per week)
- Preferred Learning Style: {learning_style} (use {style_hint})

Instructions:
- Return ONLY valid JSON with exactly this structure.
- Each phase must have: "focus" (string), "weekly_goals" (array of arrays of strings), "resources" (array of strings).
- "weekly_goals" must have exactly {weeks_30} sub-arrays for 30-day, {weeks_60} for 60-day, {weeks_90} for 90-day.
- Each sub-array represents one week's goals — {min_goals} to {max_goals} goal strings per week.
- "resources" must be 2–4 specific resource names (course names, docs sites, etc.).
- 30-day: Focus on foundational skills. No projects yet.
- 60-day: Introduce intermediate skills + first project (provided separately — just reference "work on first project").
- 90-day: Advanced skills + certifications + portfolio project (provided separately — just reference "complete portfolio project").
- Do NOT generate certification or project details — those are injected separately.
- Do NOT add any text outside the JSON object.

Output JSON with ONLY these keys at the top level: "30_day", "60_day", "90_day":
"""

# ---------------------------------------------------------------------------
# Granite call with fallback
# ---------------------------------------------------------------------------

def _call_granite_for_roadmap(
    student_profile: Dict[str, Any],
    profile_analysis: Dict[str, Any],
    skill_gap: Dict[str, Any],
    target_career: str,
    pace_info: Tuple[str, int, int],
) -> Optional[Dict[str, Any]]:
    """
    Ask Granite to generate the 30/60/90-day roadmap structure.

    Returns parsed dict or None on failure.
    """
    pace_label, min_goals, max_goals = pace_info
    availability = int(student_profile.get("availability_per_week") or 10)
    learning_style = (student_profile.get("preferred_learning_style") or "mixed").lower()
    style_hint = _STYLE_HINTS.get(learning_style, _STYLE_HINTS["mixed"])

    skills_have = ", ".join(skill_gap.get("skills_already_have", [])) or "none yet"
    critical_skills = [
        s["skill"] for s in skill_gap.get("skills_to_learn", [])
        if s.get("priority") == "Critical"
    ]
    important_skills = [
        s["skill"] for s in skill_gap.get("skills_to_learn", [])
        if s.get("priority") == "Important"
    ]
    all_gap_skills = critical_skills + important_skills
    skills_to_learn_str = ", ".join(all_gap_skills[:8]) or "core fundamentals"

    # Weeks per phase based on pace
    weeks_30 = min(4, max(2, 4 if pace_label == "slow" else 4))
    weeks_60 = min(4, max(2, 4 if pace_label == "slow" else 4))
    weeks_90 = min(4, max(2, 4 if pace_label == "slow" else 4))

    prompt = _ROADMAP_PROMPT_TEMPLATE.format(
        name            = student_profile.get("name", "Student"),
        target_career   = target_career,
        profile_tier    = profile_analysis.get("profile_tier", "moderate"),
        skills_have     = skills_have,
        skills_to_learn = skills_to_learn_str,
        availability    = availability,
        pace            = pace_label,
        min_goals       = min_goals,
        max_goals       = max_goals,
        learning_style  = learning_style,
        style_hint      = style_hint,
        weeks_30        = weeks_30,
        weeks_60        = weeks_60,
        weeks_90        = weeks_90,
    )

    print("==================================================")
    print("ROADMAP AGENT")
    print("==================================================")
    print("Prompt Sent:")
    print(prompt)
    print()

    try:
        raw    = call_granite_strong(prompt, params={"max_new_tokens": 1200})
        
        print("Granite Response:")
        print(raw)
        print("==================================================")
        print()

        parsed = parse_granite_json(raw)

        print("-------------------------------------------------")
        print("Parsed Granite Response (roadmap):")
        import json as _json
        try:
            print(_json.dumps(parsed, indent=2, default=str))
        except Exception:
            print(parsed)
        print("-------------------------------------------------")

        if not isinstance(parsed, dict):
            log.warning("Roadmap Agent: Granite returned non-dict — using fallback.")
            print("[PARSE RESULT] Granite returned non-dict type:", type(parsed).__name__, "— using fallback.")
            return None

        # Validate presence of all three phases
        for phase in ("30_day", "60_day", "90_day"):
            if phase not in parsed or not isinstance(parsed[phase], dict):
                log.warning("Roadmap Agent: missing phase '%s' in Granite output — fallback.", phase)
                print(f"[PARSE RESULT] Missing or invalid phase '{phase}' in Granite output — using fallback.")
                return None

        print("[PARSE RESULT] All three phases present. Granite roadmap accepted.")
        for phase in ("30_day", "60_day", "90_day"):
            focus = parsed[phase].get("focus", "⚠️ MISSING")
            goals_count = len(parsed[phase].get("weekly_goals", []))
            resources_count = len(parsed[phase].get("resources", []))
            print(f"  {phase}: focus='{focus}' | weekly_goals weeks={goals_count} | resources={resources_count}")

        log.info("Roadmap Agent: Granite roadmap generated successfully.")
        return parsed

    except (GraniteCallError, GraniteParseError) as exc:
        log.warning("Granite unavailable — using deterministic fallback")
        print("Granite Response: [Failed — using deterministic fallback]")
        print("==================================================")
        print()
        return None


def _build_fallback_roadmap(
    student_profile: Dict[str, Any],
    skill_gap: Dict[str, Any],
    target_career: str,
    pace_info: Tuple[str, int, int],
    target_career_id: str = "",
) -> Dict[str, Any]:
    """
    Build a deterministic roadmap without Granite.

    Used when the Granite call fails or returns malformed output.
    Uses career-specific skill sequences when available, falls back to
    skill-gap data otherwise.
    """
    pace_label, min_goals, max_goals = pace_info

    # Prefer career-specific skill sequences over gap-derived skills
    career_key = target_career_id.lower().strip()
    career_title_lc = target_career.lower()

    # Try to match by career_id first, then by title keyword
    fallback_skills: List[str] = []
    for key, skills in _CAREER_FALLBACK_SKILLS.items():
        if key == career_key or key in career_title_lc or any(word in career_title_lc for word in key.split("_")):
            fallback_skills = skills
            break

    # If no career-specific match, derive from skill gap
    if not fallback_skills:
        critical_skills = [
            s["skill"] for s in skill_gap.get("skills_to_learn", [])
            if s.get("priority") == "Critical"
        ]
        important_skills = [
            s["skill"] for s in skill_gap.get("skills_to_learn", [])
            if s.get("priority") == "Important"
        ]
        fallback_skills = (critical_skills + important_skills) or _CAREER_FALLBACK_SKILLS["default"]

    # Distribute skills across weeks (4 weeks per phase)
    def _chunk_goals(skills: List[str], weeks: int, goals_per_week: int) -> List[List[str]]:
        chunks = []
        idx = 0
        for week in range(weeks):
            week_goals = []
            for _ in range(goals_per_week):
                if idx < len(skills):
                    week_goals.append(f"Learn {skills[idx]}")
                    idx += 1
            if not week_goals:
                week_goals = [f"Review and practise {target_career} fundamentals"]
            chunks.append(week_goals)
        return chunks

    phase_30_skills = fallback_skills[:4 * max_goals]
    phase_60_skills = fallback_skills[4 * max_goals:8 * max_goals]

    return {
        "30_day": {
            "focus": f"Build foundational skills required for {target_career}.",
            "weekly_goals": _chunk_goals(phase_30_skills or [f"Study {target_career} fundamentals"], 4, max_goals),
            "resources": ["freeCodeCamp", "MDN Web Docs", "official documentation"],
        },
        "60_day": {
            "focus": f"Deepen intermediate skills and start your first {target_career} project.",
            "weekly_goals": _chunk_goals(
                phase_60_skills or [f"Build project features", "Write tests", "Add documentation"],
                4, max_goals
            ),
            "resources": ["YouTube tutorials", "The Odin Project", "official documentation"],
        },
        "90_day": {
            "focus": f"Complete certifications and build a portfolio-quality {target_career} project.",
            "weekly_goals": _chunk_goals(
                [f"Work on portfolio project", "Prepare for certification", "Deploy project", "Write README"],
                4, max_goals
            ),
            "resources": ["IBM SkillsBuild", "Coursera", "official certification guide"],
        },
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(
    student_profile: Dict[str, Any],
    profile_analysis: Dict[str, Any],
    skill_gap: Dict[str, Any],
    top_recommendation: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run the Roadmap Agent.

    Parameters
    ----------
    student_profile : dict
        Validated 9-field student profile.
    profile_analysis : dict
        Profile Agent output including profile_tier.
    skill_gap : dict
        Skill Gap Agent output including skills_to_learn and tools_to_learn.
    top_recommendation : dict
        First item from Career Recommendation Agent output (target career).

    Returns
    -------
    dict
        {
            "target_career": str,
            "profile_tier": str,
            "availability_per_week": int,
            "preferred_learning_style": str,
            "30_day": { "focus": str, "weekly_goals": [[str]], "resources": [str] },
            "60_day": { "focus": str, "weekly_goals": [[str]], "tools_to_set_up": [str],
                        "first_project": {"title": str, "description": str}, "resources": [str] },
            "90_day": { "focus": str, "weekly_goals": [[str]],
                        "certifications": [{"name": str, "provider": str, "url": str}],
                        "portfolio_project": {"title": str, "description": str}, "resources": [str] }
        }
    """
    target_career    = top_recommendation.get("title", "")
    target_career_id = top_recommendation.get("career_id", "")
    profile_tier     = profile_analysis.get("profile_tier", "moderate")
    availability     = int(student_profile.get("availability_per_week") or 10)
    learning_style   = student_profile.get("preferred_learning_style") or "mixed"

    log.info(
        "Roadmap Agent: starting for '%s' → '%s' (tier=%s avail=%d)",
        student_profile.get("name"), target_career, profile_tier, availability,
    )

    # Step 1 — Load KB data for the target career
    career_kb = get_career_by_id(target_career_id) or {}

    # Step 2 — Determine pace
    pace_info = _pace_from_availability(availability)
    log.info("Roadmap Agent: pace=%s (%d–%d goals/week)", *pace_info)

    # Step 3 — Select certs and projects from KB (deterministic, never Granite)
    certifications = _select_certifications(career_kb, profile_tier, max_count=2)
    first_project  = _select_projects(career_kb, profile_tier, "first_project")
    portfolio_proj = _select_projects(career_kb, profile_tier, "portfolio_project")
    tools_to_set_up = career_kb.get("core_tools", [])[:4]  # top 4 core tools

    # Step 4 — Granite roadmap generation (with fallback)
    granite_roadmap = _call_granite_for_roadmap(
        student_profile,
        profile_analysis,
        skill_gap,
        target_career,
        pace_info,
    )

    granite_used = granite_roadmap is not None

    if not granite_used:
        granite_roadmap = _build_fallback_roadmap(
            student_profile, skill_gap, target_career, pace_info, target_career_id
        )
        log.info("Roadmap Agent: using fallback roadmap.")

    # Step 5 — Merge KB-sourced data into Granite phases
    phase_30 = dict(granite_roadmap.get("30_day", {}))
    phase_60 = dict(granite_roadmap.get("60_day", {}))
    phase_90 = dict(granite_roadmap.get("90_day", {}))

    # Ensure all phases have the required keys
    phase_30.setdefault("focus",        f"Build foundational skills for {target_career}.")
    phase_30.setdefault("weekly_goals", [])
    phase_30.setdefault("resources",    ["official documentation", "freeCodeCamp"])

    phase_60.setdefault("focus",        f"Develop intermediate skills and build your first project.")
    phase_60.setdefault("weekly_goals", [])
    phase_60.setdefault("resources",    ["YouTube tutorials", "The Odin Project"])
    phase_60["tools_to_set_up"] = tools_to_set_up
    phase_60["first_project"]   = first_project

    phase_90.setdefault("focus",        f"Complete certifications and build a portfolio-quality project.")
    phase_90.setdefault("weekly_goals", [])
    phase_90.setdefault("resources",    ["IBM SkillsBuild", "Coursera"])
    phase_90["certifications"]     = certifications
    phase_90["portfolio_project"]  = portfolio_proj

    result = {
        "target_career":          target_career,
        "profile_tier":           profile_tier,
        "availability_per_week":  availability,
        "preferred_learning_style": learning_style,
        "granite_status":         "granite" if granite_used else "fallback",
        "30_day":                 phase_30,
        "60_day":                 phase_60,
        "90_day":                 phase_90,
    }

    # Final result structure debug log
    print("==================================================")
    print("ROADMAP AGENT — FINAL RESULT STRUCTURE")
    print("==================================================")
    print(f"  target_career: {result['target_career']}")
    print(f"  profile_tier: {result['profile_tier']}")
    print(f"  availability_per_week: {result['availability_per_week']}")
    print(f"  preferred_learning_style: {result['preferred_learning_style']}")
    for phase_key in ("30_day", "60_day", "90_day"):
        ph = result[phase_key]
        focus = ph.get("focus", "⚠️ MISSING")
        goals = ph.get("weekly_goals", [])
        resources = ph.get("resources", [])
        extra_keys = [k for k in ph.keys() if k not in ("focus", "weekly_goals", "resources")]
        print(f"  {phase_key}:")
        print(f"    focus: '{focus}'")
        print(f"    weekly_goals: {len(goals)} week(s) defined")
        print(f"    resources: {resources}")
        if extra_keys:
            print(f"    extra_keys: {extra_keys}")
    print("==================================================")
    print("(Frontend normaliseRoadmapSteps reads results.roadmap['30_day'].focus etc.)")
    print("==================================================")

    log.info("Roadmap Agent: complete for '%s'", student_profile.get("name"))
    return result
