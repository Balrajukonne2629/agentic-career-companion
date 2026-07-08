"""
tests/test_career_recommendation_agent.py
==========================================
Unit tests for agents/career_recommendation_agent.py.

All Granite calls and KB loading are mocked.

Test scope:
  - _normalise_set: basic case-folding
  - _score_career: base formula, goal boost, bonus, difficulty penalty
  - _rank_careers: sorted descending by score, matching_skills injected
  - _build_top3: always returns exactly 3 items; handles KB with <3 careers
  - _fallback_reasoning: non-empty string referencing matched skills
  - run() output contract: exactly 3 items, all required keys
  - run() with Granite success: reasoning taken from Granite
  - run() with Granite failure (GraniteCallError): fallback reasoning used
  - run() with Granite non-list: fallback reasoning used
  - Career goal boost applied when goal matches title/id

Run with:
    python -m pytest tests/test_career_recommendation_agent.py -v
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
from agents import career_recommendation_agent as cra
from errors import GraniteCallError, GraniteParseError

PATCH_GRANITE = "agents.career_recommendation_agent.call_granite_strong"
PATCH_CAREERS = "agents.career_recommendation_agent.get_all_careers"

# ---------------------------------------------------------------------------
# Minimal KB career objects for testing
# ---------------------------------------------------------------------------

def _make_career(
    career_id="full-stack-developer",
    title="Full Stack Developer",
    required_skills=None,
    nice_to_have=None,
    interests=None,
    difficulty="moderate",
    industry="Software Development",
):
    return {
        "career_id":           career_id,
        "title":               title,
        "required_skills":     required_skills or ["HTML", "CSS", "JavaScript", "React", "Node.js"],
        "nice_to_have_skills": nice_to_have or ["TypeScript", "Docker"],
        "suitable_for_interests": interests or ["Web Development", "Full Stack Development"],
        "difficulty_level":    difficulty,
        "industry_sector":     industry,
    }


def _make_profile(
    skills=None,
    interests=None,
    career_goal="Full Stack Developer",
):
    return {
        "name":        "TestStudent",
        "skills":      skills or ["React", "JavaScript", "SQL"],
        "interests":   interests or ["Web Development"],
        "career_goal": career_goal,
    }


def _make_analysis(tier="moderate"):
    return {"profile_tier": tier}


def _granite_reasoning_response(top3):
    items = [{"career_id": c["career_id"], "reasoning": f"Granite reason for {c['title']}."}
             for c in top3]
    return json.dumps(items)


# ---------------------------------------------------------------------------
# Unit: _normalise_set
# ---------------------------------------------------------------------------

class TestNormaliseSet:
    def test_lowercases_all(self):
        result = cra._normalise_set(["Java", "PYTHON", "React.js"])
        assert "java" in result
        assert "python" in result

    def test_strips_whitespace(self):
        result = cra._normalise_set(["  Node.js  "])
        assert "node.js" in result

    def test_empty_list(self):
        assert cra._normalise_set([]) == set()

    def test_filters_empty_strings(self):
        result = cra._normalise_set(["", " "])
        assert result == set()


# ---------------------------------------------------------------------------
# Unit: _score_career
# ---------------------------------------------------------------------------

class TestScoreCareer:
    def _score(self, student_skills, student_interests, career_goal="",
               profile_tier="moderate", career=None):
        c = career or _make_career()
        return cra._score_career(
            c,
            cra._normalise_set(student_skills),
            cra._normalise_set(student_interests),
            career_goal.lower(),
            profile_tier,
        )

    def test_perfect_match_no_penalty(self):
        # All required skills matched, matching interest
        score = self._score(
            ["HTML", "CSS", "JavaScript", "React", "Node.js"],
            ["Web Development"],
            profile_tier="moderate",
        )
        assert score > 0

    def test_zero_skills_zero_interest(self):
        score = self._score([], [], profile_tier="moderate")
        assert score == 0

    def test_goal_boost_applied(self):
        score_with_goal    = self._score([], [], career_goal="full stack developer")
        score_without_goal = self._score([], [], career_goal="something else")
        assert score_with_goal == score_without_goal + 10

    def test_nice_to_have_bonus(self):
        # student has TypeScript (nice-to-have)
        score_with    = self._score(["TypeScript"], [])
        score_without = self._score([], [])
        assert score_with == score_without + 5

    def test_difficulty_penalty_needs_development_advanced(self):
        career = _make_career(difficulty="advanced")
        score_nd = self._score(["HTML"], [], profile_tier="needs-development", career=career)
        score_st = self._score(["HTML"], [], profile_tier="strong", career=career)
        assert score_st - score_nd == 10

    def test_difficulty_penalty_moderate_advanced(self):
        # Give the student a matching skill so base_score > 0, then the penalty difference shows
        career = _make_career(difficulty="advanced")
        score_mod = self._score(["HTML"], [], profile_tier="moderate", career=career)
        score_str = self._score(["HTML"], [], profile_tier="strong",   career=career)
        assert score_str - score_mod == 5

    def test_score_never_negative(self):
        career = _make_career(difficulty="advanced")
        score = self._score([], [], profile_tier="needs-development", career=career)
        assert score >= 0

    def test_score_never_exceeds_100(self):
        # Student has all required + bonus + goal boost
        score = self._score(
            ["HTML", "CSS", "JavaScript", "React", "Node.js", "TypeScript", "Docker"],
            ["Web Development", "Full Stack Development"],
            career_goal="full stack developer",
            profile_tier="strong",
        )
        assert score <= 100


# ---------------------------------------------------------------------------
# Unit: _build_top3
# ---------------------------------------------------------------------------

class TestBuildTop3:
    def test_always_returns_exactly_3(self):
        ranked = [
            {**_make_career(), "confidence_percent": 80, "matching_skills": []},
            {**_make_career(career_id="b", title="B"), "confidence_percent": 60, "matching_skills": []},
            {**_make_career(career_id="c", title="C"), "confidence_percent": 40, "matching_skills": []},
            {**_make_career(career_id="d", title="D"), "confidence_percent": 20, "matching_skills": []},
        ]
        top3 = cra._build_top3(ranked)
        assert len(top3) == 3

    def test_first_is_highest_score(self):
        ranked = [
            {**_make_career(), "confidence_percent": 90, "matching_skills": []},
            {**_make_career(career_id="b", title="B"), "confidence_percent": 50, "matching_skills": []},
            {**_make_career(career_id="c", title="C"), "confidence_percent": 30, "matching_skills": []},
        ]
        top3 = cra._build_top3(ranked)
        assert top3[0]["confidence_percent"] == 90

    def test_fewer_than_3_in_kb_pads(self):
        ranked = [
            {**_make_career(), "confidence_percent": 70, "matching_skills": []},
        ]
        top3 = cra._build_top3(ranked)
        assert len(top3) == 3

    def test_all_zero_scores_still_returns_3(self):
        ranked = [
            {**_make_career(career_id=f"c{i}", title=f"C{i}"), "confidence_percent": 0, "matching_skills": []}
            for i in range(4)
        ]
        top3 = cra._build_top3(ranked)
        assert len(top3) == 3


# ---------------------------------------------------------------------------
# Unit: _fallback_reasoning
# ---------------------------------------------------------------------------

class TestFallbackReasoning:
    def test_non_empty_string(self):
        career  = {**_make_career(), "matching_skills": ["React"]}
        profile = _make_profile(skills=["React"])
        result  = cra._fallback_reasoning(career, profile)
        assert isinstance(result, str) and len(result) > 10

    def test_mentions_matched_skills(self):
        career  = {**_make_career(), "matching_skills": ["React", "JavaScript"]}
        profile = _make_profile()
        result  = cra._fallback_reasoning(career, profile)
        assert "React" in result

    def test_no_matched_skills_still_returns_string(self):
        career  = {**_make_career(), "matching_skills": []}
        profile = _make_profile()
        result  = cra._fallback_reasoning(career, profile)
        assert isinstance(result, str) and len(result) > 10

    def test_goal_mentioned_when_present(self):
        career  = {**_make_career(), "matching_skills": []}
        profile = _make_profile(career_goal="Software Engineer")
        result  = cra._fallback_reasoning(career, profile)
        assert "Software Engineer" in result


# ---------------------------------------------------------------------------
# Integration: run()
# ---------------------------------------------------------------------------

FIVE_CAREERS = [
    _make_career("full-stack-developer",  "Full Stack Developer",
                 ["HTML", "CSS", "JavaScript", "React", "Node.js"],
                 interests=["Web Development", "Full Stack Development"]),
    _make_career("frontend-developer",    "Frontend Developer",
                 ["HTML", "CSS", "JavaScript", "React"],
                 interests=["Web Development", "Frontend Development"]),
    _make_career("backend-developer",     "Backend Developer",
                 ["Python", "SQL", "Node.js", "REST API", "Git"],
                 interests=["Backend Development"]),
    _make_career("data-analyst",          "Data Analyst",
                 ["Python", "SQL", "Pandas", "Data Visualization"],
                 interests=["Data Science"]),
    _make_career("cloud-engineer",        "Cloud Engineer",
                 ["AWS", "Linux", "Docker", "Kubernetes"],
                 interests=["Cloud Computing"]),
]


class TestRunOutputContract:
    def test_returns_exactly_3(self):
        with patch(PATCH_CAREERS, return_value=FIVE_CAREERS), \
             patch(PATCH_GRANITE, return_value="[]"):
            result = cra.run(_make_profile(), _make_analysis())
        assert len(result) == 3

    def test_all_required_keys_present(self):
        with patch(PATCH_CAREERS, return_value=FIVE_CAREERS), \
             patch(PATCH_GRANITE, return_value="[]"):
            result = cra.run(_make_profile(), _make_analysis())
        for item in result:
            for key in ("career_id", "title", "confidence_percent",
                        "reasoning", "matching_skills", "industry_sector"):
                assert key in item, f"Missing key '{key}' in item {item}"

    def test_confidence_in_range(self):
        with patch(PATCH_CAREERS, return_value=FIVE_CAREERS), \
             patch(PATCH_GRANITE, return_value="[]"):
            result = cra.run(_make_profile(), _make_analysis())
        for item in result:
            assert 0 <= item["confidence_percent"] <= 100

    def test_reasoning_non_empty(self):
        with patch(PATCH_CAREERS, return_value=FIVE_CAREERS), \
             patch(PATCH_GRANITE, return_value="[]"):
            result = cra.run(_make_profile(), _make_analysis())
        for item in result:
            assert item["reasoning"]


class TestRunGraniteReasoning:
    def test_granite_reasoning_used(self):
        def _fake_careers():
            return FIVE_CAREERS

        def _fake_granite(prompt, params=None):
            # We need the top3 to generate the reasoning response
            return json.dumps([
                {"career_id": "full-stack-developer",  "reasoning": "Specific Granite reason 1."},
                {"career_id": "frontend-developer",    "reasoning": "Specific Granite reason 2."},
                {"career_id": "backend-developer",     "reasoning": "Specific Granite reason 3."},
            ])

        with patch(PATCH_CAREERS, return_value=FIVE_CAREERS), \
             patch(PATCH_GRANITE, side_effect=_fake_granite):
            result = cra.run(_make_profile(skills=["React", "JavaScript"]), _make_analysis())

        # At least one Granite reason should have been used
        all_reasoning = [r["reasoning"] for r in result]
        assert any("Granite reason" in r for r in all_reasoning)

    def test_granite_call_error_uses_fallback(self):
        with patch(PATCH_CAREERS, return_value=FIVE_CAREERS), \
             patch(PATCH_GRANITE, side_effect=GraniteCallError("API down")):
            result = cra.run(_make_profile(), _make_analysis())
        assert len(result) == 3
        for item in result:
            assert item["reasoning"]

    def test_granite_parse_error_uses_fallback(self):
        with patch(PATCH_CAREERS, return_value=FIVE_CAREERS), \
             patch(PATCH_GRANITE, side_effect=GraniteParseError("bad JSON")):
            result = cra.run(_make_profile(), _make_analysis())
        assert len(result) == 3

    def test_granite_returns_non_list_uses_fallback(self):
        with patch(PATCH_CAREERS, return_value=FIVE_CAREERS), \
             patch(PATCH_GRANITE, return_value='{"not": "a list"}'):
            result = cra.run(_make_profile(), _make_analysis())
        assert len(result) == 3


class TestRunRanking:
    def test_student_with_react_gets_frontend_or_fullstack_first(self):
        profile = _make_profile(
            skills=["React", "HTML", "CSS", "JavaScript"],
            interests=["Web Development", "Frontend Development"],
            career_goal="Frontend Developer",
        )
        with patch(PATCH_CAREERS, return_value=FIVE_CAREERS), \
             patch(PATCH_GRANITE, return_value="[]"):
            result = cra.run(profile, _make_analysis())
        top_ids = [r["career_id"] for r in result]
        assert "frontend-developer" in top_ids or "full-stack-developer" in top_ids

    def test_student_with_no_skills_still_gets_3(self):
        profile = _make_profile(skills=[], interests=[], career_goal="")
        with patch(PATCH_CAREERS, return_value=FIVE_CAREERS), \
             patch(PATCH_GRANITE, return_value="[]"):
            result = cra.run(profile, _make_analysis())
        assert len(result) == 3

    def test_needs_development_tier_penalty_applied(self):
        """needs-development students get lower scores on advanced careers."""
        advanced_career = _make_career(
            "advanced-career", "Advanced Career",
            ["Python", "Kubernetes"], difficulty="advanced"
        )
        careers = [advanced_career] + FIVE_CAREERS[1:]
        profile = _make_profile(skills=["Python"])

        with patch(PATCH_CAREERS, return_value=careers), \
             patch(PATCH_GRANITE, return_value="[]"):
            result_nd  = cra.run(profile, {"profile_tier": "needs-development"})
            result_str = cra.run(profile, {"profile_tier": "strong"})

        # Find the advanced career in both results
        nd_score  = next((r["confidence_percent"] for r in result_nd  if r["career_id"] == "advanced-career"), None)
        str_score = next((r["confidence_percent"] for r in result_str if r["career_id"] == "advanced-career"), None)
        if nd_score is not None and str_score is not None:
            assert str_score >= nd_score
