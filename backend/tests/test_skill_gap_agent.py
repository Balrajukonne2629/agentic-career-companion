"""
tests/test_skill_gap_agent.py
==============================
Unit tests for agents/skill_gap_agent.py.
"""

import sys
import os
import types
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
from agents import skill_gap_agent as sga

PATCH_KB = "agents.skill_gap_agent.get_career_by_id"

# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

_CAREER_KB = {
    "career_id":           "full-stack-developer",
    "title":               "Full Stack Developer",
    "required_skills":     ["HTML", "CSS", "JavaScript", "React", "Node.js", "SQL", "REST API", "Git"],
    "nice_to_have_skills": ["TypeScript", "Docker", "Redis"],
    "core_tools":          ["VS Code", "GitHub", "Postman", "Chrome DevTools"],
}

_TOP_REC = {
    "career_id": "full-stack-developer",
    "title":     "Full Stack Developer",
}

def _make_profile(skills=None):
    return {
        "name":   "TestStudent",
        "skills": skills if skills is not None else ["React", "SQL"],
    }


# ===========================================================================
# TestComputeGaps
# ===========================================================================

class TestComputeGaps:
    def test_student_has_some_skills_correctly_split(self):
        profile = _make_profile(skills=["React", "SQL"])
        gaps    = sga._compute_gaps(profile, _CAREER_KB)
        assert "React" in gaps["skills_already_have"]
        assert "SQL"   in gaps["skills_already_have"]
        assert "HTML"  in gaps["required_gap"]
        assert "CSS"   in gaps["required_gap"]

    def test_case_insensitive_matching(self):
        profile = _make_profile(skills=["react", "sql"])   # lowercase
        gaps    = sga._compute_gaps(profile, _CAREER_KB)
        assert "React" in gaps["skills_already_have"]
        assert "SQL"   in gaps["skills_already_have"]

    def test_zero_gap_when_student_has_all_required(self):
        all_required = _CAREER_KB["required_skills"]
        profile      = _make_profile(skills=all_required)
        gaps         = sga._compute_gaps(profile, _CAREER_KB)
        assert gaps["required_gap"]        == []
        assert gaps["skills_already_have"] == all_required

    def test_beneficial_gap_correct(self):
        profile = _make_profile(skills=["React"])
        gaps    = sga._compute_gaps(profile, _CAREER_KB)
        assert "TypeScript" in gaps["beneficial_gap"]
        assert "Docker"     in gaps["beneficial_gap"]

    def test_tools_gap_correct(self):
        profile = _make_profile(skills=["React"])
        gaps    = sga._compute_gaps(profile, _CAREER_KB)
        assert "VS Code"   in gaps["tools_gap"]
        assert "Postman"   in gaps["tools_gap"]

    def test_tools_already_in_skills_not_in_gap(self):
        profile = _make_profile(skills=["React", "GitHub"])
        gaps    = sga._compute_gaps(profile, _CAREER_KB)
        assert "GitHub" not in gaps["tools_gap"]

    def test_empty_student_skills(self):
        profile = _make_profile(skills=[])
        gaps    = sga._compute_gaps(profile, _CAREER_KB)
        assert gaps["skills_already_have"] == []
        assert len(gaps["required_gap"]) == len(_CAREER_KB["required_skills"])

    def test_career_with_no_tools_empty_tools_gap(self):
        career  = dict(_CAREER_KB, core_tools=[])
        profile = _make_profile(skills=[])
        gaps    = sga._compute_gaps(profile, career)
        assert gaps["tools_gap"] == []


# ===========================================================================
# TestComputeSummary
# ===========================================================================

class TestComputeSummary:
    def test_counts_correct(self):
        skills = [
            {"skill": "A", "priority": "Critical",   "reason": "r"},
            {"skill": "B", "priority": "Critical",   "reason": "r"},
            {"skill": "C", "priority": "Important",  "reason": "r"},
            {"skill": "D", "priority": "Beneficial", "reason": "r"},
        ]
        tools = [
            {"tool": "X", "priority": "Important", "reason": "r"},
            {"tool": "Y", "priority": "Important", "reason": "r"},
        ]
        summary = sga._compute_summary(skills, tools)
        assert summary["critical_count"]   == 2
        assert summary["important_count"]  == 1
        assert summary["beneficial_count"] == 1
        assert summary["tools_count"]      == 2
        assert summary["total_gap_items"]  == 6

    def test_empty_inputs(self):
        summary = sga._compute_summary([], [])
        assert summary["total_gap_items"] == 0

    def test_total_equals_sum_of_parts(self):
        skills = [{"priority": "Critical", "skill": "A", "reason": "r"}] * 3
        tools  = [{"tool": "T", "priority": "Important", "reason": "r"}] * 2
        summary = sga._compute_summary(skills, tools)
        assert summary["total_gap_items"] == (
            summary["critical_count"] + summary["important_count"]
            + summary["beneficial_count"] + summary["tools_count"]
        )


# ===========================================================================
# TestFallbackPriority
# ===========================================================================

class TestFallbackPriority:
    def test_unknown_skill_returns_critical(self):
        result = sga._fallback_priority("Kubernetes", {"python", "flask"})
        assert result == "Critical"

    def test_adjacent_skill_returns_important(self):
        result = sga._fallback_priority("node.js", {"node", "react"})
        assert result == "Important"

    def test_returns_string(self):
        result = sga._fallback_priority("Docker", set())
        assert isinstance(result, str)


# ===========================================================================
# TestRunOutputContract
# ===========================================================================

class TestRunOutputContract:
    def test_all_required_top_level_keys(self):
        with patch(PATCH_KB, return_value=_CAREER_KB):
            result = sga.run(_make_profile(skills=["React", "SQL"]), _TOP_REC)
        for key in ("target_career", "target_career_id", "skills_already_have",
                    "skills_to_learn", "tools_to_learn", "gap_summary"):
            assert key in result, f"Missing key: {key}"

    def test_gap_summary_has_all_keys(self):
        with patch(PATCH_KB, return_value=_CAREER_KB):
            result = sga.run(_make_profile(), _TOP_REC)
        for key in ("critical_count", "important_count", "beneficial_count",
                    "tools_count", "total_gap_items"):
            assert key in result["gap_summary"]

    def test_target_career_set_correctly(self):
        with patch(PATCH_KB, return_value=_CAREER_KB):
            result = sga.run(_make_profile(), _TOP_REC)
        assert result["target_career"]    == "Full Stack Developer"
        assert result["target_career_id"] == "full-stack-developer"

    def test_skills_to_learn_items_have_correct_keys(self):
        with patch(PATCH_KB, return_value=_CAREER_KB):
            result = sga.run(_make_profile(skills=["React"]), _TOP_REC)
        for item in result["skills_to_learn"]:
            assert "skill"    in item
            assert "priority" in item
            assert "reason"   in item

    def test_tools_to_learn_items_have_correct_keys(self):
        with patch(PATCH_KB, return_value=_CAREER_KB):
            result = sga.run(_make_profile(skills=[]), _TOP_REC)
        for item in result["tools_to_learn"]:
            assert "tool"     in item
            assert "priority" in item
            assert "reason"   in item

    def test_tools_always_important_priority(self):
        with patch(PATCH_KB, return_value=_CAREER_KB):
            result = sga.run(_make_profile(skills=[]), _TOP_REC)
        for item in result["tools_to_learn"]:
            assert item["priority"] == "Important"

    def test_beneficial_items_always_beneficial(self):
        with patch(PATCH_KB, return_value=_CAREER_KB):
            result = sga.run(_make_profile(skills=[]), _TOP_REC)
        for item in result["skills_to_learn"]:
            if item["skill"] in _CAREER_KB["nice_to_have_skills"]:
                assert item["priority"] == "Beneficial"


# ===========================================================================
# TestRunGapScenarios
# ===========================================================================

class TestRunGapScenarios:
    def test_zero_gap_student(self):
        all_req = _CAREER_KB["required_skills"]
        with patch(PATCH_KB, return_value=_CAREER_KB):
            result = sga.run(_make_profile(skills=all_req), _TOP_REC)
        assert result["skills_to_learn"] == [] or all(
            item["priority"] == "Beneficial" for item in result["skills_to_learn"]
        )
        assert result["gap_summary"]["critical_count"] == 0
        assert result["gap_summary"]["important_count"] == 0

    def test_all_required_in_gap_when_no_skills(self):
        with patch(PATCH_KB, return_value=_CAREER_KB):
            result = sga.run(_make_profile(skills=[]), _TOP_REC)
        gap_skills = {item["skill"] for item in result["skills_to_learn"]
                      if item["priority"] != "Beneficial"}
        req = set(_CAREER_KB["required_skills"])
        assert req == gap_skills

    def test_unknown_career_id_does_not_crash(self):
        rec = {"career_id": "nonexistent-career", "title": "Unknown Career"}
        with patch(PATCH_KB, return_value=None):
            result = sga.run(_make_profile(), rec)
        assert "gap_summary" in result
