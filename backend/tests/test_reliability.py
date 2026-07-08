import sys
import os
import types
import json
import logging
from unittest.mock import patch, MagicMock

# mock out SDKs
for _mod in [
    "ibm_watsonx_ai", "ibm_watsonx_ai.foundation_models",
    "ibm_watsonx_ai.metanames", "ibm_cloud_sdk_core",
    "ibm_cloud_sdk_core.authenticators", "ibm_watson",
]:
    sys.modules[_mod] = types.ModuleType(_mod)

sys.modules["ibm_watsonx_ai"].APIClient = type("A", (), {})
sys.modules["ibm_watsonx_ai"].Credentials = type("C", (), {})
sys.modules["ibm_watsonx_ai.foundation_models"].ModelInference = type("M", (), {})
sys.modules["ibm_watsonx_ai.metanames"].GenTextParamsMetaNames = type(
    "G", (), {
        "MAX_NEW_TOKENS": "max_new_tokens",
        "TEMPERATURE": "temperature",
        "REPETITION_PENALTY": "repetition_penalty",
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
from agents import validation_agent, profile_agent, career_recommendation_agent, skill_gap_agent, roadmap_agent
from errors import GraniteCallError

@pytest.fixture
def complete_transcript():
    return (
        "Hi, my name is Balraju. I am studying B.Tech IT in my second year. "
        "My CGPA is 8.58. I know Java, React, Python, SQL, and C++. I enjoy web development. "
        "My career goal is to become a Full Stack Developer."
    )

class TestReliabilityPipeline:
    """Tests the resilience of the entire agent pipeline when Granite is offline."""

    @patch("agents.validation_agent.call_granite_fast")
    @patch("agents.profile_agent.call_granite_fast")
    @patch("agents.career_recommendation_agent.call_granite_strong")
    @patch("agents.skill_gap_agent.call_granite_strong")
    @patch("agents.roadmap_agent.call_granite_strong")
    def test_pipeline_http_429_rate_limit_degradation(
        self, mock_road, mock_gap, mock_career, mock_profile, mock_val,
        complete_transcript, caplog
    ):
        """
        Mock ALL Granite calls to raise HTTP 429 rate limit exceptions,
        and verify that the entire pipeline still completes successfully
        and generates a complete dashboard with appropriate fallback logging.
        """
        err = GraniteCallError("The usage limit for the current plan has been reached (HTTP 429)")
        mock_val.side_effect = err
        mock_profile.side_effect = err
        mock_career.side_effect = err
        mock_gap.side_effect = err
        mock_road.side_effect = err

        with caplog.at_level(logging.WARNING):
            # Step 1: Validation
            val_res = validation_agent.run(complete_transcript)
            assert val_res["status"] == "complete"
            profile = val_res["profile"]
            assert profile["name"] == "Balraju"
            assert profile["cgpa"] == 8.58

            # Step 2: Profile
            prof_res = profile_agent.run(profile)
            assert "summary" in prof_res
            assert len(prof_res["strengths"]) > 0
            assert prof_res["profile_tier"] == "strong"

            # Step 3: Career recommendations
            recommendations = career_recommendation_agent.run(profile, prof_res)
            assert len(recommendations) == 3
            top_rec = recommendations[0]
            assert top_rec["confidence_percent"] > 0
            assert "reasoning" in top_rec

            # Step 4: Skill Gaps
            gaps = skill_gap_agent.run(profile, top_rec)
            assert gaps["target_career"] == top_rec["title"]
            assert "skills_to_learn" in gaps

            # Step 5: Roadmap
            roadmap = roadmap_agent.run(profile, prof_res, gaps, top_rec)
            assert roadmap["target_career"] == top_rec["title"]
            assert "30_day" in roadmap
            assert "60_day" in roadmap
            assert "90_day" in roadmap

        warnings = [record.message for record in caplog.records if record.levelname == "WARNING"]
        assert any("Granite unavailable — using deterministic fallback" in w for w in warnings)

    @patch("agents.validation_agent.call_granite_fast")
    @patch("agents.profile_agent.call_granite_fast")
    @patch("agents.career_recommendation_agent.call_granite_strong")
    @patch("agents.skill_gap_agent.call_granite_strong")
    @patch("agents.roadmap_agent.call_granite_strong")
    def test_pipeline_timeout_and_malformed_json_resilience(
        self, mock_road, mock_gap, mock_career, mock_profile, mock_val,
        complete_transcript, caplog
    ):
        """
        Mock some calls to timeout and others to return malformed garbage JSON,
        verifying that the pipeline still runs completely.
        """
        mock_val.side_effect = GraniteCallError("Request timed out (timeout)")
        mock_profile.return_value = "NOT VALID JSON"
        mock_career.return_value = "[]"
        mock_gap.side_effect = GraniteCallError("IBM watsonx service unavailable")
        mock_road.return_value = '{"30_day": {}, "60_day": {}}'

        with caplog.at_level(logging.WARNING):
            # Step 1: Validation
            val_res = validation_agent.run(complete_transcript)
            assert val_res["status"] == "complete"
            profile = val_res["profile"]

            # Step 2: Profile
            prof_res = profile_agent.run(profile)
            assert "summary" in prof_res

            # Step 3: Career recommendations
            recommendations = career_recommendation_agent.run(profile, prof_res)
            assert len(recommendations) == 3
            top_rec = recommendations[0]

            # Step 4: Skill Gaps
            gaps = skill_gap_agent.run(profile, top_rec)
            assert "skills_to_learn" in gaps

            # Step 5: Roadmap
            roadmap = roadmap_agent.run(profile, prof_res, gaps, top_rec)
            assert "30_day" in roadmap
            assert "90_day" in roadmap

        warnings = [record.message for record in caplog.records if record.levelname == "WARNING"]
        assert any("Granite unavailable — using deterministic fallback" in w for w in warnings)
