"""
tests/test_profile_agent.py
============================
Unit tests for agents/profile_agent.py.

All Granite calls are replaced with unittest.mock.patch so these tests run
without an IBM Cloud account, without the ibm-watsonx-ai SDK, and without
any network connection.

Test scope:
  - Tier computation: strong / moderate / needs-development edge cases
  - Score computation: formula correctness at boundary values
  - Score band mapping: all four bands
  - Time-to-ready: slow / normal / fast pace, minimum 1
  - Fallback narrative: generated without Granite
  - Granite success path: narrative fields parsed correctly
  - Granite failure (GraniteCallError): fallback triggered, run() still succeeds
  - Granite malformed JSON (GraniteParseError): fallback triggered
  - Granite returns non-dict: fallback triggered
  - run() output contract: all 8 required keys present
  - learning_style passthrough: taken from profile, defaults to "mixed"

Run with:
    python -m pytest tests/test_profile_agent.py -v
    (from the backend/ directory)
"""

import sys
import os
import types
import json
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# SDK mocking — must happen before any backend import
# ---------------------------------------------------------------------------

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
    "G", (), {
        "MAX_NEW_TOKENS":      "max_new_tokens",
        "TEMPERATURE":         "temperature",
        "REPETITION_PENALTY":  "repetition_penalty",
    }
)
sys.modules["ibm_cloud_sdk_core.authenticators"].IAMAuthenticator = type("I", (), {})
sys.modules["ibm_watson"].SpeechToTextV1 = type("S", (), {})

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("IBM_API_KEY",      "test_key")
os.environ.setdefault("IBM_PROJECT_ID",   "test_project")
os.environ.setdefault("IBM_WATSONX_URL",  "https://us-south.ml.cloud.ibm.com")
os.environ.setdefault("FLASK_SECRET_KEY", "test_secret_abc")

import pytest
from agents import profile_agent as pa
from errors import GraniteCallError, GraniteParseError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_profile(
    name="Balraju",
    branch="Information Technology",
    year=2,
    cgpa=8.58,
    skills=None,
    interests=None,
    career_goal="Full Stack Developer",
    preferred_learning_style="mixed",
    availability_per_week=10,
):
    return {
        "name":                   name,
        "branch":                 branch,
        "year":                   year,
        "cgpa":                   cgpa,
        "skills":                 skills if skills is not None else ["Java", "C++", "React"],
        "interests":              interests if interests is not None else ["Web Development", "Full Stack Development"],
        "career_goal":            career_goal,
        "preferred_learning_style": preferred_learning_style,
        "availability_per_week":  availability_per_week,
    }


def _good_granite_response():
    return json.dumps({
        "summary": "Balraju is a talented IT student with strong Java skills.",
        "strengths": ["Strong Java background", "Proficient in React"],
        "development_areas": ["Needs Node.js experience", "Limited database knowledge"],
    })


PATCH_TARGET = "agents.profile_agent.call_granite_fast"


# ---------------------------------------------------------------------------
# Tier computation tests
# ---------------------------------------------------------------------------

class TestComputeTier:
    def test_strong_tier_high_cgpa_many_skills(self):
        assert pa._compute_tier(8.5, 6) == "strong"

    def test_strong_tier_exact_boundary(self):
        # cgpa == 8.0 and skill_count == 5 → strong
        assert pa._compute_tier(8.0, 5) == "strong"

    def test_moderate_tier_good_cgpa_some_skills(self):
        assert pa._compute_tier(7.0, 4) == "moderate"

    def test_moderate_tier_lower_bound_cgpa_and_skills(self):
        # cgpa 6.5 + 3 skills → moderate
        assert pa._compute_tier(6.5, 3) == "moderate"

    def test_moderate_tier_high_cgpa_low_skills(self):
        # cgpa >= 8.0 but < 5 skills → moderate (special case)
        assert pa._compute_tier(8.2, 2) == "moderate"

    def test_needs_development_low_everything(self):
        assert pa._compute_tier(5.0, 1) == "needs-development"

    def test_needs_development_cgpa_below_6_5(self):
        assert pa._compute_tier(6.0, 3) == "needs-development"

    def test_needs_development_zero_skills(self):
        assert pa._compute_tier(7.0, 0) == "needs-development"


# ---------------------------------------------------------------------------
# Score computation tests
# ---------------------------------------------------------------------------

class TestComputeScore:
    def test_perfect_score(self):
        # cgpa=10, skills=8, interests=3, goal=True → 35+40+15+10 = 100
        score = pa._compute_score(10.0, 8, 3, True)
        assert score == 100

    def test_zero_score(self):
        score = pa._compute_score(0.0, 0, 0, False)
        assert score == 0

    def test_no_goal_deducts_10(self):
        s_with    = pa._compute_score(8.0, 4, 2, True)
        s_without = pa._compute_score(8.0, 4, 2, False)
        assert s_with - s_without == 10

    def test_skill_component_caps_at_40(self):
        s_exact = pa._compute_score(0.0, 8, 0, False)
        s_over  = pa._compute_score(0.0, 20, 0, False)
        assert s_exact == s_over == 40

    def test_interest_component_caps_at_15(self):
        s_three = pa._compute_score(0.0, 0, 3, False)
        s_ten   = pa._compute_score(0.0, 0, 10, False)
        assert s_three == s_ten == 15

    def test_cgpa_component_caps_at_35(self):
        s_ten    = pa._compute_score(10.0, 0, 0, False)
        s_twelve = pa._compute_score(12.0, 0, 0, False)
        assert s_ten == s_twelve == 35

    def test_typical_profile(self):
        # cgpa=8.58 → 35*0.858=30, skills=3/8=0.375 → 15, interests=2/3=0.666 → 10, goal=10
        score = pa._compute_score(8.58, 3, 2, True)
        assert 0 < score < 100

    def test_returns_int(self):
        score = pa._compute_score(7.5, 4, 2, True)
        assert isinstance(score, int)


# ---------------------------------------------------------------------------
# Score band tests
# ---------------------------------------------------------------------------

class TestScoreBand:
    def test_career_ready_at_80(self):
        assert pa._score_band(80)  == "Career Ready"
    def test_career_ready_at_100(self):
        assert pa._score_band(100) == "Career Ready"
    def test_on_track_at_60(self):
        assert pa._score_band(60)  == "On Track"
    def test_on_track_at_79(self):
        assert pa._score_band(79)  == "On Track"
    def test_developing_at_40(self):
        assert pa._score_band(40)  == "Developing"
    def test_developing_at_59(self):
        assert pa._score_band(59)  == "Developing"
    def test_foundational_at_39(self):
        assert pa._score_band(39)  == "Foundational"
    def test_foundational_at_0(self):
        assert pa._score_band(0)   == "Foundational"


# ---------------------------------------------------------------------------
# Time-to-ready tests
# ---------------------------------------------------------------------------

class TestTimeToReady:
    def test_already_ready_returns_1(self):
        # score=100 → gap=0 → base=0 → result=max(1, ...)=1
        assert pa._estimate_time_to_ready(100, 10) == 1

    def test_slow_pace_multiplier(self):
        # 5 hours < 8 → factor=1.5
        t_slow   = pa._estimate_time_to_ready(50, 5)
        t_normal = pa._estimate_time_to_ready(50, 10)
        assert t_slow > t_normal

    def test_fast_pace_multiplier(self):
        # 20 hours ≥ 15 → factor=0.7
        t_fast   = pa._estimate_time_to_ready(50, 20)
        t_normal = pa._estimate_time_to_ready(50, 10)
        assert t_fast < t_normal

    def test_minimum_one_month(self):
        assert pa._estimate_time_to_ready(99, 20) >= 1

    def test_returns_int(self):
        assert isinstance(pa._estimate_time_to_ready(60, 10), int)


# ---------------------------------------------------------------------------
# Fallback narrative tests
# ---------------------------------------------------------------------------

class TestFallbackNarrative:
    def test_all_three_keys_present(self):
        result = pa._build_fallback_narrative(_make_profile())
        assert "summary" in result
        assert "strengths" in result
        assert "development_areas" in result

    def test_summary_mentions_name(self):
        result = pa._build_fallback_narrative(_make_profile(name="TestStudent"))
        assert "TestStudent" in result["summary"]

    def test_summary_mentions_year_and_branch(self):
        result = pa._build_fallback_narrative(_make_profile(year=3, branch="Computer Science"))
        assert "Year 3" in result["summary"]
        assert "Computer Science" in result["summary"]

    def test_strengths_non_empty(self):
        result = pa._build_fallback_narrative(_make_profile())
        assert len(result["strengths"]) >= 1

    def test_dev_areas_non_empty(self):
        result = pa._build_fallback_narrative(_make_profile())
        assert len(result["development_areas"]) >= 1

    def test_high_cgpa_in_strengths(self):
        result = pa._build_fallback_narrative(_make_profile(cgpa=9.0))
        assert any("Strong academic" in s or "Solid academic" in s for s in result["strengths"])

    def test_empty_skills_does_not_crash(self):
        result = pa._build_fallback_narrative(_make_profile(skills=[]))
        assert isinstance(result["summary"], str)


# ---------------------------------------------------------------------------
# run() — Granite success path
# ---------------------------------------------------------------------------

class TestRunGraniteSuccess:
    def test_output_has_all_keys(self):
        with patch(PATCH_TARGET, return_value=_good_granite_response()):
            result = pa.run(_make_profile())
        for key in ("summary", "strengths", "development_areas",
                    "profile_tier", "career_readiness_score",
                    "score_band", "estimated_time_to_ready_months", "learning_style"):
            assert key in result, f"Missing key: {key}"

    def test_granite_summary_used(self):
        with patch(PATCH_TARGET, return_value=_good_granite_response()):
            result = pa.run(_make_profile())
        assert "Balraju is a talented" in result["summary"]

    def test_profile_tier_is_string(self):
        with patch(PATCH_TARGET, return_value=_good_granite_response()):
            result = pa.run(_make_profile())
        assert result["profile_tier"] in ("strong", "moderate", "needs-development")

    def test_score_is_int_in_range(self):
        with patch(PATCH_TARGET, return_value=_good_granite_response()):
            result = pa.run(_make_profile())
        assert isinstance(result["career_readiness_score"], int)
        assert 0 <= result["career_readiness_score"] <= 100

    def test_time_to_ready_positive(self):
        with patch(PATCH_TARGET, return_value=_good_granite_response()):
            result = pa.run(_make_profile())
        assert result["estimated_time_to_ready_months"] >= 1

    def test_learning_style_passthrough(self):
        with patch(PATCH_TARGET, return_value=_good_granite_response()):
            result = pa.run(_make_profile(preferred_learning_style="visual"))
        assert result["learning_style"] == "visual"

    def test_learning_style_defaults_to_mixed(self):
        profile = _make_profile()
        profile.pop("preferred_learning_style", None)
        with patch(PATCH_TARGET, return_value=_good_granite_response()):
            result = pa.run(profile)
        assert result["learning_style"] == "mixed"


# ---------------------------------------------------------------------------
# run() — Granite failure paths
# ---------------------------------------------------------------------------

class TestRunGraniteFallback:
    def test_granite_call_error_falls_back(self):
        with patch(PATCH_TARGET, side_effect=GraniteCallError("API failed")):
            result = pa.run(_make_profile())
        assert "summary" in result
        assert result["summary"]  # non-empty

    def test_granite_parse_error_falls_back(self):
        with patch(PATCH_TARGET, side_effect=GraniteParseError("bad JSON")):
            result = pa.run(_make_profile())
        assert "summary" in result

    def test_granite_returns_non_dict_falls_back(self):
        with patch(PATCH_TARGET, return_value='["list", "not", "dict"]'):
            result = pa.run(_make_profile())
        assert "summary" in result

    def test_granite_returns_empty_summary_falls_back(self):
        bad_response = json.dumps({
            "summary": "",
            "strengths": ["something"],
            "development_areas": ["something"],
        })
        with patch(PATCH_TARGET, return_value=bad_response):
            result = pa.run(_make_profile())
        assert result["summary"]  # fallback summary is non-empty

    def test_granite_returns_empty_strengths_falls_back(self):
        bad_response = json.dumps({
            "summary": "A good summary.",
            "strengths": [],
            "development_areas": ["something"],
        })
        with patch(PATCH_TARGET, return_value=bad_response):
            result = pa.run(_make_profile())
        # Fallback narrative should still produce strengths
        assert len(result["strengths"]) >= 1


# ---------------------------------------------------------------------------
# run() — Deterministic correctness tests
# ---------------------------------------------------------------------------

class TestRunDeterministic:
    def test_strong_tier_student(self):
        profile = _make_profile(
            cgpa=9.0,
            skills=["Java", "Python", "React", "Node.js", "SQL", "Docker"]
        )
        with patch(PATCH_TARGET, return_value=_good_granite_response()):
            result = pa.run(profile)
        assert result["profile_tier"] == "strong"

    def test_needs_development_student(self):
        profile = _make_profile(cgpa=5.0, skills=["HTML"], interests=[], career_goal="")
        with patch(PATCH_TARGET, return_value=_good_granite_response()):
            result = pa.run(profile)
        assert result["profile_tier"] == "needs-development"

    def test_slow_availability_gives_longer_timeline(self):
        profile_slow   = _make_profile(availability_per_week=5)
        profile_normal = _make_profile(availability_per_week=10)
        with patch(PATCH_TARGET, return_value=_good_granite_response()):
            result_slow   = pa.run(profile_slow)
            result_normal = pa.run(profile_normal)
        assert result_slow["estimated_time_to_ready_months"] >= result_normal["estimated_time_to_ready_months"]

    def test_fast_availability_gives_shorter_timeline(self):
        profile_fast   = _make_profile(availability_per_week=20)
        profile_normal = _make_profile(availability_per_week=10)
        with patch(PATCH_TARGET, return_value=_good_granite_response()):
            result_fast   = pa.run(profile_fast)
            result_normal = pa.run(profile_normal)
        assert result_fast["estimated_time_to_ready_months"] <= result_normal["estimated_time_to_ready_months"]
