"""
tests/test_profile_agent.py
============================
Unit tests for agents/profile_agent.py.
"""

import sys
import os
import types
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


# ===========================================================================
# Tier computation tests
# ===========================================================================

class TestComputeTier:
    def test_strong_tier_high_cgpa_many_skills(self):
        assert pa._compute_tier(8.5, 6) == "strong"

    def test_strong_tier_exact_boundary(self):
        assert pa._compute_tier(8.0, 5) == "strong"

    def test_moderate_tier_good_cgpa_some_skills(self):
        assert pa._compute_tier(7.0, 4) == "moderate"

    def test_moderate_tier_lower_bound_cgpa_and_skills(self):
        assert pa._compute_tier(6.5, 3) == "moderate"

    def test_moderate_tier_high_cgpa_low_skills(self):
        assert pa._compute_tier(8.2, 2) == "moderate"

    def test_needs_development_low_everything(self):
        assert pa._compute_tier(5.0, 1) == "needs-development"

    def test_needs_development_cgpa_below_6_5(self):
        assert pa._compute_tier(6.0, 3) == "needs-development"

    def test_needs_development_zero_skills(self):
        assert pa._compute_tier(7.0, 0) == "needs-development"


# ===========================================================================
# Score computation tests
# ===========================================================================

class TestComputeScore:
    def test_perfect_score(self):
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
        score = pa._compute_score(8.58, 3, 2, True)
        assert 0 < score < 100

    def test_returns_int(self):
        score = pa._compute_score(7.5, 4, 2, True)
        assert isinstance(score, int)


# ===========================================================================
# Score band tests
# ===========================================================================

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


# ===========================================================================
# Time-to-ready tests
# ===========================================================================

class TestTimeToReady:
    def test_already_ready_returns_1(self):
        assert pa._estimate_time_to_ready(100, 10) == 1

    def test_slow_pace_multiplier(self):
        t_slow   = pa._estimate_time_to_ready(50, 5)
        t_normal = pa._estimate_time_to_ready(50, 10)
        assert t_slow > t_normal

    def test_fast_pace_multiplier(self):
        t_fast   = pa._estimate_time_to_ready(50, 20)
        t_normal = pa._estimate_time_to_ready(50, 10)
        assert t_fast < t_normal

    def test_minimum_one_month(self):
        assert pa._estimate_time_to_ready(99, 20) >= 1

    def test_returns_int(self):
        assert isinstance(pa._estimate_time_to_ready(60, 10), int)


# ===========================================================================
# Fallback narrative tests
# ===========================================================================

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


# ===========================================================================
# run() — deterministic narrative path
# ===========================================================================

class TestRunDeterministic:
    def test_output_has_all_keys(self):
        result = pa.run(_make_profile())
        for key in ("summary", "strengths", "development_areas",
                    "profile_tier", "career_readiness_score",
                    "score_band", "estimated_time_to_ready_months", "learning_style"):
            assert key in result, f"Missing key: {key}"

    def test_profile_tier_is_string(self):
        result = pa.run(_make_profile())
        assert result["profile_tier"] in ("strong", "moderate", "needs-development")

    def test_score_is_int_in_range(self):
        result = pa.run(_make_profile())
        assert isinstance(result["career_readiness_score"], int)
        assert 0 <= result["career_readiness_score"] <= 100

    def test_time_to_ready_positive(self):
        result = pa.run(_make_profile())
        assert result["estimated_time_to_ready_months"] >= 1

    def test_learning_style_passthrough(self):
        result = pa.run(_make_profile(preferred_learning_style="hands-on"))
        assert result["learning_style"] == "hands-on"

    def test_learning_style_defaults_to_mixed(self):
        result = pa.run(_make_profile(preferred_learning_style=None))
        assert result["learning_style"] == "mixed"
