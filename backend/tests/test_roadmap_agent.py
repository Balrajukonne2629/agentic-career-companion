"""
tests/test_roadmap_agent.py
============================
Unit tests for agents/roadmap_agent.py.

All Granite calls and KB loading are mocked.

Test scope:
  - _pace_from_availability: all three pace buckets
  - _select_certifications: tier-based level ordering, max_count respected
  - _select_certifications: empty certs list → empty result
  - _select_projects: first_project vs portfolio_project tier preferences
  - _select_projects: empty projects list → default project dict
  - _build_fallback_roadmap: all three phases present, weekly_goals non-empty
  - run() output contract: all required top-level keys and phase sub-keys
  - run() KB certs and projects always injected (never from Granite)
  - run() Granite success: focus/weekly_goals/resources from Granite
  - run() Granite failure (GraniteCallError): fallback roadmap used
  - run() Granite returns non-dict: fallback roadmap used
  - run() Granite missing phase: fallback roadmap used
  - run() tools_to_set_up: comes from core_tools (max 4)

Run with:
    python -m pytest tests/test_roadmap_agent.py -v
    (from the backend/ directory)
"""

import sys
import os
import types
import json
from unittest.mock import patch, MagicMock

# SDK mocking
for _mod in [
    "ibm_watsonx_ai", "ibm_watsonx_ai.foundation_models",
    "ibm_watsonx_ai.metanames", "ibm_cloud_sdk_core",
    "ibm_cloud_sdk_core.authenticators", "ibm_watson",
]:
    sys.modules[_mod] = types.ModuleType(_mod)

sys.modules["ibm_watsonx_ai"].APIClient   = type("A", (), {})
sys.modules["ibm_watsonx_ai"].Credentials = type("C", (), {})
sys.modules["ibm_watsonx_ai.foundation_models"].ModelInference = type("M", (), {})
sys.modules["ibm_watsonx_ai.metanames"].GenTextParamsMetaNames = type(
    "G", (), {"MAX_NEW_TOKENS": "max_new_tokens", "TEMPERATURE": "temperature",
              "REPETITION_PENALTY": "repetition_penalty"}
)
sys.modules["ibm_cloud_sdk_core.authenticators"].IAMAuthenticator = type("I", (), {})
sys.modules["ibm_watson"].SpeechToTextV1 = type("S", (), {})

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("IBM_API_KEY",      "test_key")
os.environ.setdefault("IBM_PROJECT_ID",   "test_project")
os.environ.setdefault("IBM_WATSONX_URL",  "https://us-south.ml.cloud.ibm.com")
os.environ.setdefault("FLASK_SECRET_KEY", "test_secret_abc")

import pytest
from agents import roadmap_agent as ra
from errors import GraniteCallError, GraniteParseError

PATCH_GRANITE = "agents.roadmap_agent.call_granite_strong"
PATCH_KB      = "agents.roadmap_agent.get_career_by_id"

# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

_CAREER_KB = {
    "career_id": "full-stack-developer",
    "title":     "Full Stack Developer",
    "core_tools": ["VS Code", "GitHub", "Postman", "Chrome DevTools", "npm"],
    "certifications": [
        {"name": "IBM Full Stack Certificate", "provider": "IBM", "level": "beginner",     "url": "https://ibm.com/cert1"},
        {"name": "Meta Front-End Certificate", "provider": "Meta","level": "intermediate", "url": "https://meta.com/cert2"},
        {"name": "AWS Developer Associate",    "provider": "AWS", "level": "advanced",     "url": "https://aws.com/cert3"},
    ],
    "suggested_projects": [
        {"title": "Portfolio Website",  "description": "A beginner portfolio.",  "difficulty": "beginner"},
        {"title": "Blog Application",   "description": "An intermediate blog.",  "difficulty": "intermediate"},
        {"title": "E-Commerce App",     "description": "An advanced app.",       "difficulty": "advanced"},
    ],
}

def _make_profile(availability=10, learning_style="mixed", skills=None):
    return {
        "name":                   "TestStudent",
        "skills":                 skills or ["React", "SQL"],
        "interests":              ["Web Development"],
        "career_goal":            "Full Stack Developer",
        "availability_per_week":  availability,
        "preferred_learning_style": learning_style,
    }

def _make_analysis(tier="moderate"):
    return {"profile_tier": tier}

def _make_skill_gap(critical_skills=None, important_skills=None):
    skills = []
    for s in (critical_skills or ["HTML", "JavaScript"]):
        skills.append({"skill": s, "priority": "Critical", "reason": "r"})
    for s in (important_skills or ["CSS"]):
        skills.append({"skill": s, "priority": "Important", "reason": "r"})
    return {
        "skills_already_have": ["React", "SQL"],
        "skills_to_learn": skills,
        "tools_to_learn": [{"tool": "GitHub", "priority": "Important", "reason": "r"}],
    }

def _make_rec():
    return {"career_id": "full-stack-developer", "title": "Full Stack Developer"}


def _good_granite_roadmap():
    return json.dumps({
        "30_day": {
            "focus":        "Learn foundational HTML and CSS.",
            "weekly_goals": [["Learn HTML basics", "Style a page"], ["Practice flexbox"]],
            "resources":    ["MDN Web Docs", "freeCodeCamp"],
        },
        "60_day": {
            "focus":        "Build intermediate skills in JavaScript.",
            "weekly_goals": [["Learn ES6+", "DOM manipulation"], ["Work on first project"]],
            "resources":    ["JavaScript.info", "Eloquent JavaScript"],
        },
        "90_day": {
            "focus":        "Complete React and get certified.",
            "weekly_goals": [["Advanced React hooks", "Complete portfolio project"], ["Prepare for certification"]],
            "resources":    ["React docs", "Coursera IBM certificate"],
        },
    })


# ---------------------------------------------------------------------------
# Unit: _pace_from_availability
# ---------------------------------------------------------------------------

class TestPaceFromAvailability:
    def test_slow_pace(self):
        pace, min_g, max_g = ra._pace_from_availability(5)
        assert pace == "slow"
        assert min_g == 1 and max_g == 2

    def test_normal_pace_lower_bound(self):
        pace, min_g, max_g = ra._pace_from_availability(8)
        assert pace == "normal"
        assert min_g == 2 and max_g == 3

    def test_normal_pace_upper_bound(self):
        pace, _, _ = ra._pace_from_availability(14)
        assert pace == "normal"

    def test_fast_pace(self):
        pace, min_g, max_g = ra._pace_from_availability(15)
        assert pace == "fast"
        assert min_g == 3 and max_g == 4

    def test_very_high_availability_fast(self):
        pace, _, _ = ra._pace_from_availability(40)
        assert pace == "fast"


# ---------------------------------------------------------------------------
# Unit: _select_certifications
# ---------------------------------------------------------------------------

class TestSelectCertifications:
    def test_moderate_tier_prefers_beginner_first(self):
        certs = ra._select_certifications(_CAREER_KB, "moderate", max_count=2)
        assert len(certs) == 2
        assert certs[0]["name"] == "IBM Full Stack Certificate"  # beginner first

    def test_strong_tier_prefers_intermediate_first(self):
        certs = ra._select_certifications(_CAREER_KB, "strong", max_count=2)
        assert certs[0]["name"] == "Meta Front-End Certificate"  # intermediate first

    def test_needs_dev_tier_prefers_beginner(self):
        certs = ra._select_certifications(_CAREER_KB, "needs-development", max_count=1)
        assert certs[0]["name"] == "IBM Full Stack Certificate"

    def test_max_count_respected(self):
        certs = ra._select_certifications(_CAREER_KB, "moderate", max_count=1)
        assert len(certs) == 1

    def test_empty_certs_returns_empty(self):
        career = dict(_CAREER_KB, certifications=[])
        certs  = ra._select_certifications(career, "moderate")
        assert certs == []

    def test_cert_has_name_provider_url(self):
        certs = ra._select_certifications(_CAREER_KB, "moderate")
        for cert in certs:
            assert "name" in cert and "provider" in cert and "url" in cert


# ---------------------------------------------------------------------------
# Unit: _select_projects
# ---------------------------------------------------------------------------

class TestSelectProjects:
    def test_first_project_moderate_prefers_beginner(self):
        proj = ra._select_projects(_CAREER_KB, "moderate", "first_project")
        assert proj["title"] == "Portfolio Website"

    def test_first_project_strong_prefers_intermediate(self):
        proj = ra._select_projects(_CAREER_KB, "strong", "first_project")
        assert proj["title"] == "Blog Application"

    def test_portfolio_strong_prefers_advanced(self):
        proj = ra._select_projects(_CAREER_KB, "strong", "portfolio_project")
        assert proj["title"] == "E-Commerce App"

    def test_portfolio_moderate_prefers_intermediate(self):
        proj = ra._select_projects(_CAREER_KB, "moderate", "portfolio_project")
        assert proj["title"] == "Blog Application"

    def test_empty_projects_returns_default(self):
        career = dict(_CAREER_KB, suggested_projects=[])
        proj   = ra._select_projects(career, "moderate", "first_project")
        assert "title" in proj and "description" in proj

    def test_project_has_title_and_description(self):
        proj = ra._select_projects(_CAREER_KB, "moderate", "first_project")
        assert "title" in proj and "description" in proj


# ---------------------------------------------------------------------------
# Unit: _build_fallback_roadmap
# ---------------------------------------------------------------------------

class TestBuildFallbackRoadmap:
    def test_all_three_phases_present(self):
        result = ra._build_fallback_roadmap(
            _make_profile(), _make_skill_gap(), "Full Stack Developer", ("normal", 2, 3)
        )
        assert "30_day" in result
        assert "60_day" in result
        assert "90_day" in result

    def test_each_phase_has_required_keys(self):
        result = ra._build_fallback_roadmap(
            _make_profile(), _make_skill_gap(), "Full Stack Developer", ("normal", 2, 3)
        )
        for phase in ("30_day", "60_day", "90_day"):
            assert "focus"        in result[phase]
            assert "weekly_goals" in result[phase]
            assert "resources"    in result[phase]

    def test_weekly_goals_non_empty(self):
        result = ra._build_fallback_roadmap(
            _make_profile(), _make_skill_gap(), "Full Stack Developer", ("normal", 2, 3)
        )
        for phase in ("30_day", "60_day", "90_day"):
            assert len(result[phase]["weekly_goals"]) > 0

    def test_empty_skill_gap_does_not_crash(self):
        empty_gap = {"skills_already_have": [], "skills_to_learn": [], "tools_to_learn": []}
        result = ra._build_fallback_roadmap(
            _make_profile(), empty_gap, "Full Stack Developer", ("slow", 1, 2)
        )
        assert "30_day" in result


# ---------------------------------------------------------------------------
# Integration: run() output contract
# ---------------------------------------------------------------------------

class TestRunOutputContract:
    def test_top_level_keys_present(self):
        with patch(PATCH_KB, return_value=_CAREER_KB), \
             patch(PATCH_GRANITE, return_value=_good_granite_roadmap()):
            result = ra.run(_make_profile(), _make_analysis(), _make_skill_gap(), _make_rec())
        for key in ("target_career", "profile_tier", "availability_per_week",
                    "preferred_learning_style", "30_day", "60_day", "90_day"):
            assert key in result, f"Missing key: {key}"

    def test_30_day_phase_keys(self):
        with patch(PATCH_KB, return_value=_CAREER_KB), \
             patch(PATCH_GRANITE, return_value=_good_granite_roadmap()):
            result = ra.run(_make_profile(), _make_analysis(), _make_skill_gap(), _make_rec())
        for key in ("focus", "weekly_goals", "resources"):
            assert key in result["30_day"]

    def test_60_day_phase_keys(self):
        with patch(PATCH_KB, return_value=_CAREER_KB), \
             patch(PATCH_GRANITE, return_value=_good_granite_roadmap()):
            result = ra.run(_make_profile(), _make_analysis(), _make_skill_gap(), _make_rec())
        for key in ("focus", "weekly_goals", "resources", "tools_to_set_up", "first_project"):
            assert key in result["60_day"], f"Missing key in 60_day: {key}"

    def test_90_day_phase_keys(self):
        with patch(PATCH_KB, return_value=_CAREER_KB), \
             patch(PATCH_GRANITE, return_value=_good_granite_roadmap()):
            result = ra.run(_make_profile(), _make_analysis(), _make_skill_gap(), _make_rec())
        for key in ("focus", "weekly_goals", "resources", "certifications", "portfolio_project"):
            assert key in result["90_day"], f"Missing key in 90_day: {key}"

    def test_availability_passed_through(self):
        with patch(PATCH_KB, return_value=_CAREER_KB), \
             patch(PATCH_GRANITE, return_value=_good_granite_roadmap()):
            result = ra.run(_make_profile(availability=15), _make_analysis(), _make_skill_gap(), _make_rec())
        assert result["availability_per_week"] == 15

    def test_learning_style_passed_through(self):
        with patch(PATCH_KB, return_value=_CAREER_KB), \
             patch(PATCH_GRANITE, return_value=_good_granite_roadmap()):
            result = ra.run(_make_profile(learning_style="visual"), _make_analysis(), _make_skill_gap(), _make_rec())
        assert result["preferred_learning_style"] == "visual"


# ---------------------------------------------------------------------------
# Integration: run() — KB injection tests
# ---------------------------------------------------------------------------

class TestRunKBInjection:
    def test_certs_come_from_kb_not_granite(self):
        """Granite output does NOT contain certifications — they must come from KB."""
        with patch(PATCH_KB, return_value=_CAREER_KB), \
             patch(PATCH_GRANITE, return_value=_good_granite_roadmap()):
            result = ra.run(_make_profile(), _make_analysis(), _make_skill_gap(), _make_rec())
        certs = result["90_day"]["certifications"]
        assert len(certs) > 0
        cert_names = [c["name"] for c in certs]
        assert any("IBM" in name or "Meta" in name or "AWS" in name for name in cert_names)

    def test_first_project_comes_from_kb(self):
        with patch(PATCH_KB, return_value=_CAREER_KB), \
             patch(PATCH_GRANITE, return_value=_good_granite_roadmap()):
            result = ra.run(_make_profile(), _make_analysis(), _make_skill_gap(), _make_rec())
        proj = result["60_day"]["first_project"]
        assert "title" in proj and "description" in proj

    def test_portfolio_project_comes_from_kb(self):
        with patch(PATCH_KB, return_value=_CAREER_KB), \
             patch(PATCH_GRANITE, return_value=_good_granite_roadmap()):
            result = ra.run(_make_profile(), _make_analysis(), _make_skill_gap(), _make_rec())
        proj = result["90_day"]["portfolio_project"]
        assert "title" in proj and "description" in proj

    def test_tools_to_set_up_max_4(self):
        with patch(PATCH_KB, return_value=_CAREER_KB), \
             patch(PATCH_GRANITE, return_value=_good_granite_roadmap()):
            result = ra.run(_make_profile(), _make_analysis(), _make_skill_gap(), _make_rec())
        assert len(result["60_day"]["tools_to_set_up"]) <= 4

    def test_empty_kb_gracefully_handled(self):
        with patch(PATCH_KB, return_value=None), \
             patch(PATCH_GRANITE, return_value=_good_granite_roadmap()):
            result = ra.run(_make_profile(), _make_analysis(), _make_skill_gap(), _make_rec())
        assert "90_day" in result


# ---------------------------------------------------------------------------
# Integration: run() — Granite failure paths
# ---------------------------------------------------------------------------

class TestRunGraniteFallbacks:
    def test_granite_call_error_uses_fallback(self):
        with patch(PATCH_KB, return_value=_CAREER_KB), \
             patch(PATCH_GRANITE, side_effect=GraniteCallError("API down")):
            result = ra.run(_make_profile(), _make_analysis(), _make_skill_gap(), _make_rec())
        assert "30_day" in result and "60_day" in result and "90_day" in result

    def test_granite_parse_error_uses_fallback(self):
        with patch(PATCH_KB, return_value=_CAREER_KB), \
             patch(PATCH_GRANITE, side_effect=GraniteParseError("bad JSON")):
            result = ra.run(_make_profile(), _make_analysis(), _make_skill_gap(), _make_rec())
        # KB injection still present even in fallback
        assert "certifications" in result["90_day"]
        assert "first_project"  in result["60_day"]

    def test_granite_returns_non_dict_uses_fallback(self):
        with patch(PATCH_KB, return_value=_CAREER_KB), \
             patch(PATCH_GRANITE, return_value='["list", "not", "dict"]'):
            result = ra.run(_make_profile(), _make_analysis(), _make_skill_gap(), _make_rec())
        assert "90_day" in result

    def test_granite_missing_90_day_uses_fallback(self):
        # Granite returns object missing "90_day" key
        incomplete = json.dumps({"30_day": {"focus": "f", "weekly_goals": [[]], "resources": []},
                                  "60_day": {"focus": "f", "weekly_goals": [[]], "resources": []}})
        with patch(PATCH_KB, return_value=_CAREER_KB), \
             patch(PATCH_GRANITE, return_value=incomplete):
            result = ra.run(_make_profile(), _make_analysis(), _make_skill_gap(), _make_rec())
        assert "90_day" in result

    def test_fallback_certs_still_injected_when_granite_fails(self):
        with patch(PATCH_KB, return_value=_CAREER_KB), \
             patch(PATCH_GRANITE, side_effect=GraniteCallError("down")):
            result = ra.run(_make_profile(), _make_analysis(), _make_skill_gap(), _make_rec())
        assert len(result["90_day"]["certifications"]) > 0
