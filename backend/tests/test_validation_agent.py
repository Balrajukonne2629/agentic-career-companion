"""
tests/test_validation_agent.py
==============================
Unit tests for agents/validation_agent.py.
"""

import sys
import os
import types
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# SDK mocking must happen before any backend import
# ---------------------------------------------------------------------------

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
from agents import validation_agent as va

# ---------------------------------------------------------------------------
# Helper: build a valid Granite profile dict
# ---------------------------------------------------------------------------

def _granite_response(
    name="Balraju",
    branch="B.Tech Information Technology",
    year="second",
    cgpa="8.58",
    skills=None,
    interests=None,
    career_goal="Full Stack Developer",
    learning_style=None,
    availability=None,
):
    """Return a dict as _regex_extract would return it."""
    return {
        "name": name,
        "branch": branch,
        "year": year,
        "cgpa": cgpa,
        "skills": skills if skills is not None else ["Java", "C++", "React"],
        "interests": interests if interests is not None else ["web development"],
        "career_goal": career_goal,
        "preferred_learning_style": learning_style,
        "availability_per_week": availability,
    }


# Minimal complete response
_COMPLETE_RESPONSE = _granite_response()

# Partial response — missing cgpa and career_goal
_PARTIAL_RESPONSE = {
    "name": "Priya",
    "branch": "B.E. Computer Science",
    "year": "final",
    "cgpa": None,
    "skills": ["Python", "SQL"],
    "interests": ["data science"],
    "career_goal": None,
    "preferred_learning_style": None,
    "availability_per_week": None,
}


# Patch target: _regex_extract in validation_agent's namespace
PATCH_TARGET = "agents.validation_agent._regex_extract"


# ===========================================================================
# TestCompleteTranscript
# ===========================================================================

class TestCompleteTranscript:
    """
    Validation Agent returns all required fields → status == "complete".
    """

    def test_status_is_complete(self):
        with patch(PATCH_TARGET, return_value=_COMPLETE_RESPONSE):
            result = va.run(
                "Hi I am Balraju second year IT student my CGPA is 8.58 "
                "I know Java C++ React and want to be a Full Stack Developer"
            )
        assert result["status"] == "complete"

    def test_profile_present(self):
        with patch(PATCH_TARGET, return_value=_COMPLETE_RESPONSE):
            result = va.run("Hi I am Balraju second year IT CGPA 8.58 "
                            "skills Java React career Full Stack Developer")
        assert "profile" in result

    def test_name_normalised(self):
        with patch(PATCH_TARGET, return_value=_COMPLETE_RESPONSE):
            result = va.run("Hi I am Balraju second year IT CGPA 8.58 "
                            "skills Java React career Full Stack Developer")
        assert result["profile"]["name"] == "Balraju"

    def test_year_is_integer(self):
        with patch(PATCH_TARGET, return_value=_COMPLETE_RESPONSE):
            result = va.run("I am Balraju second year IT CGPA 8.58 "
                            "skills Java React want to be Full Stack Developer")
        assert result["profile"]["year"] == 2

    def test_cgpa_is_float(self):
        with patch(PATCH_TARGET, return_value=_COMPLETE_RESPONSE):
            result = va.run("I am Balraju second year IT CGPA 8.58 "
                            "skills Java React want to be Full Stack Developer")
        assert isinstance(result["profile"]["cgpa"], float)
        assert result["profile"]["cgpa"] == 8.58

    def test_skills_is_list(self):
        with patch(PATCH_TARGET, return_value=_COMPLETE_RESPONSE):
            result = va.run("I am Balraju second year IT CGPA 8.58 "
                            "skills Java React want to be Full Stack Developer")
        assert isinstance(result["profile"]["skills"], list)
        assert len(result["profile"]["skills"]) > 0

    def test_interests_is_list(self):
        with patch(PATCH_TARGET, return_value=_COMPLETE_RESPONSE):
            result = va.run("I am Balraju second year IT CGPA 8.58 "
                            "skills Java React want to be Full Stack Developer "
                            "I enjoy building websites")
        assert isinstance(result["profile"]["interests"], list)
        assert len(result["profile"]["interests"]) > 0

    def test_learning_style_default_when_not_mentioned(self):
        with patch(PATCH_TARGET, return_value=_COMPLETE_RESPONSE):
            result = va.run("I am Balraju second year IT CGPA 8.58 "
                            "skills Java React career Full Stack Developer")
        assert result["profile"]["preferred_learning_style"] == "mixed"

    def test_availability_default_when_not_mentioned(self):
        with patch(PATCH_TARGET, return_value=_COMPLETE_RESPONSE):
            result = va.run("I am Balraju second year IT CGPA 8.58 "
                            "skills Java React career Full Stack Developer")
        assert result["profile"]["availability_per_week"] == 10

    def test_nine_fields_present(self):
        expected_keys = {
            "name", "branch", "year", "cgpa", "skills", "interests",
            "career_goal", "preferred_learning_style", "availability_per_week",
        }
        with patch(PATCH_TARGET, return_value=_COMPLETE_RESPONSE):
            result = va.run("I am Balraju second year IT CGPA 8.58 "
                            "skills Java React career Full Stack Developer")
        assert set(result["profile"].keys()) == expected_keys

    def test_no_missing_fields_key_on_complete(self):
        with patch(PATCH_TARGET, return_value=_COMPLETE_RESPONSE):
            result = va.run("I am Balraju second year IT CGPA 8.58 "
                            "skills Java React career Full Stack Developer")
        assert "missing_fields" not in result

    def test_granite_called_exactly_once_on_success(self):
        with patch(PATCH_TARGET, return_value=_COMPLETE_RESPONSE) as mock_g:
            va.run("I am Balraju second year IT CGPA 8.58 "
                   "skills Java React career Full Stack Developer")
        assert mock_g.call_count == 1


# ===========================================================================
# TestPartialTranscript
# ===========================================================================

class TestPartialTranscript:
    """
    Extraction returns some null fields → status == "incomplete".
    """

    def test_status_is_incomplete(self):
        with patch(PATCH_TARGET, return_value=_PARTIAL_RESPONSE):
            result = va.run("I am Priya final year CS student I know Python and SQL")
        assert result["status"] == "incomplete"

    def test_missing_fields_key_present(self):
        with patch(PATCH_TARGET, return_value=_PARTIAL_RESPONSE):
            result = va.run("I am Priya final year CS student I know Python and SQL")
        assert "missing_fields" in result

    def test_cgpa_in_missing_fields(self):
        with patch(PATCH_TARGET, return_value=_PARTIAL_RESPONSE):
            result = va.run("I am Priya final year CS student I know Python and SQL")
        assert "cgpa" in result["missing_fields"]

    def test_career_goal_in_missing_fields(self):
        with patch(PATCH_TARGET, return_value=_PARTIAL_RESPONSE):
            result = va.run("I am Priya final year CS I know Python and SQL")
        assert "career_goal" in result["missing_fields"]

    def test_missing_labels_present(self):
        with patch(PATCH_TARGET, return_value=_PARTIAL_RESPONSE):
            result = va.run("I am Priya final year CS I know Python and SQL")
        assert "missing_labels" in result

    def test_missing_labels_are_strings(self):
        with patch(PATCH_TARGET, return_value=_PARTIAL_RESPONSE):
            result = va.run("I am Priya final year CS I know Python and SQL")
        for key, label in result["missing_labels"].items():
            assert isinstance(label, str)
            assert len(label) > 5

    def test_partial_profile_present(self):
        with patch(PATCH_TARGET, return_value=_PARTIAL_RESPONSE):
            result = va.run("I am Priya final year CS I know Python and SQL")
        assert "partial_profile" in result

    def test_partial_profile_has_name(self):
        with patch(PATCH_TARGET, return_value=_PARTIAL_RESPONSE):
            result = va.run("I am Priya final year CS I know Python and SQL")
        assert result["partial_profile"]["name"] == "Priya"

    def test_partial_profile_has_skills(self):
        with patch(PATCH_TARGET, return_value=_PARTIAL_RESPONSE):
            result = va.run("I am Priya final year CS I know Python and SQL")
        assert len(result["partial_profile"]["skills"]) > 0

    def test_defaulted_fields_still_present_in_partial(self):
        """Even on incomplete, defaulted fields should be in partial_profile."""
        with patch(PATCH_TARGET, return_value=_PARTIAL_RESPONSE):
            result = va.run("I am Priya final year CS I know Python and SQL")
        pp = result["partial_profile"]
        assert pp["preferred_learning_style"] == "mixed"
        assert pp["availability_per_week"] == 10

    def test_defaulted_fields_not_in_missing_list(self):
        with patch(PATCH_TARGET, return_value=_PARTIAL_RESPONSE):
            result = va.run("I am Priya final year CS I know Python and SQL")
        assert "preferred_learning_style" not in result["missing_fields"]
        assert "availability_per_week" not in result["missing_fields"]


# ===========================================================================
# TestMergeWithPartialProfile
# ===========================================================================

class TestMergeWithPartialProfile:
    """
    Verify multi-call merge behaviour when partial_profile is provided.
    """

    def test_scalar_field_overridden_by_new_extraction(self):
        """New CGPA from follow-up overrides old null CGPA."""
        prior = {
            "name": "Priya", "branch": "B.E. CS", "year": 4,
            "cgpa": None, "skills": ["Python"],
            "interests": ["Data Science"], "career_goal": None,
            "preferred_learning_style": "mixed", "availability_per_week": 10,
        }
        followup_response = {
            "name": None, "branch": None, "year": None,
            "cgpa": "7.8", "skills": [],
            "interests": [], "career_goal": "Data Analyst",
            "preferred_learning_style": None, "availability_per_week": None,
        }
        with patch(PATCH_TARGET, return_value=followup_response):
            result = va.run("My CGPA is 7.8 and I want to be a Data Analyst",
                            partial_profile=prior)
        assert result["status"] == "complete"
        assert result["profile"]["cgpa"] == 7.8
        assert result["profile"]["career_goal"] == "Data Analyst"

    def test_skills_unioned_not_replaced(self):
        """Existing skills + new skills = union, not replacement."""
        prior = {
            "name": "Priya", "branch": "B.E. CS", "year": 4,
            "cgpa": 7.8, "skills": ["Python", "SQL"],
            "interests": ["Data Science"], "career_goal": "Data Analyst",
            "preferred_learning_style": "mixed", "availability_per_week": 10,
        }
        followup_response = {
            "name": None, "branch": None, "year": None,
            "cgpa": None, "skills": ["Pandas", "NumPy"],
            "interests": [], "career_goal": None,
            "preferred_learning_style": None, "availability_per_week": None,
        }
        with patch(PATCH_TARGET, return_value=followup_response):
            result = va.run("I also know Pandas and NumPy", partial_profile=prior)
        skills = result["profile"]["skills"]
        assert "Python" in skills
        assert "SQL" in skills
        assert "Pandas" in skills
        assert "NumPy" in skills

    def test_interests_unioned(self):
        prior = {
            "name": "Ravi", "branch": "B.Tech IT", "year": 3,
            "cgpa": 8.0, "skills": ["Java"],
            "interests": ["Web Development"], "career_goal": "Backend Developer",
            "preferred_learning_style": "mixed", "availability_per_week": 10,
        }
        followup_response = {
            "name": None, "branch": None, "year": None, "cgpa": None,
            "skills": [], "interests": ["cloud computing"],
            "career_goal": None, "preferred_learning_style": None,
            "availability_per_week": None,
        }
        with patch(PATCH_TARGET, return_value=followup_response):
            result = va.run("I am also interested in cloud computing",
                            partial_profile=prior)
        interests = result["profile"]["interests"]
        assert "Web Development" in interests
        assert "Cloud Computing" in interests

    def test_existing_scalar_preserved_when_new_is_null(self):
        """If extraction returns null for a field that exists in partial_profile, keep prior value."""
        prior = {
            "name": "Ravi", "branch": "B.Tech IT", "year": 3,
            "cgpa": None, "skills": ["Java"],
            "interests": ["Web Development"], "career_goal": "Backend Developer",
            "preferred_learning_style": "mixed", "availability_per_week": 10,
        }
        followup_response = {
            "name": None, "branch": None, "year": None,
            "cgpa": "8.0", "skills": [],
            "interests": [], "career_goal": None,
            "preferred_learning_style": None, "availability_per_week": None,
        }
        with patch(PATCH_TARGET, return_value=followup_response):
            result = va.run("My CGPA is 8.0", partial_profile=prior)
        # "Ravi" kept from prior
        assert result["profile"]["name"] == "Ravi"


# ===========================================================================
# TestSessionSafety
# ===========================================================================

class TestSessionSafety:
    """
    The run() function never writes to Flask session directly.
    Session writes are the route's responsibility.
    """

    def test_run_does_not_import_flask_session(self):
        """validation_agent module must not import flask.session at module level."""
        import agents.validation_agent as mod
        src = open(mod.__file__).read()
        assert "from flask import" not in src, \
            "validation_agent.py must not import from flask"

    def test_run_returns_dict_not_none(self):
        with patch(PATCH_TARGET, return_value=_COMPLETE_RESPONSE):
            result = va.run("I am Balraju second year IT CGPA 8.58 "
                            "skills Java React career Full Stack Developer")
        assert isinstance(result, dict)

    def test_incomplete_result_has_no_profile_key(self):
        """Incomplete response must not have a 'profile' key (only partial_profile)."""
        with patch(PATCH_TARGET, return_value=_PARTIAL_RESPONSE):
            result = va.run("I am Priya final year CS I know Python and SQL")
        assert "profile" not in result


# ===========================================================================
# TestInterestInference
# ===========================================================================

class TestInterestInference:
    """
    Python keyword inference runs regardless of extraction interest output.
    Hallucinated interests from extraction are discarded.
    """

    def test_python_inference_adds_interests(self):
        """Transcript contains "building websites" → Web Development inferred."""
        no_interest_response = {
            "name": "Ravi", "branch": "B.Tech IT", "year": "third",
            "cgpa": "8.0", "skills": ["HTML", "CSS"],
            "interests": [],   # Extraction found nothing
            "career_goal": "Frontend Developer",
            "preferred_learning_style": None, "availability_per_week": None,
        }
        with patch(PATCH_TARGET, return_value=no_interest_response):
            result = va.run(
                "I am Ravi third year IT CGPA 8.0 I know HTML CSS "
                "I enjoy building websites and want to be a Frontend Developer"
            )
        interests = result["profile"]["interests"]
        assert "Web Development" in interests

    def test_hallucinated_granite_interest_discarded(self):
        """Extraction returns a non-canonical interest string → dropped."""
        hallucinated = {
            "name": "Ravi", "branch": "B.Tech IT", "year": "third",
            "cgpa": "8.0", "skills": ["HTML"],
            "interests": ["coding for fun", "awesome stuff"],  # not canonical
            "career_goal": "Frontend Developer",
            "preferred_learning_style": None, "availability_per_week": None,
        }
        with patch(PATCH_TARGET, return_value=hallucinated):
            result = va.run(
                "I am Ravi third year IT CGPA 8.0 skills HTML "
                "I enjoy building websites career Frontend Developer"
            )
        interests = result["profile"]["interests"]
        assert "coding for fun" not in interests
        assert "awesome stuff" not in interests

    def test_canonical_granite_interest_kept(self):
        """Extraction returns a correctly-cased canonical interest → kept."""
        canonical_response = {
            "name": "Ravi", "branch": "B.Tech IT", "year": "third",
            "cgpa": "8.0", "skills": ["Python"],
            "interests": ["data science"],   # lowercase — should canonicalize
            "career_goal": "Data Analyst",
            "preferred_learning_style": None, "availability_per_week": None,
        }
        with patch(PATCH_TARGET, return_value=canonical_response):
            result = va.run(
                "I am Ravi third year IT CGPA 8.0 skills Python "
                "career Data Analyst"
            )
        interests = result["profile"]["interests"]
        assert "Data Science" in interests

    def test_no_duplicate_interests(self):
        """Extraction and Python both infer the same interest → appears once."""
        response = {
            "name": "Ravi", "branch": "B.Tech IT", "year": "third",
            "cgpa": "8.0", "skills": ["HTML", "CSS"],
            "interests": ["web development"],  # Extraction also found this
            "career_goal": "Frontend Developer",
            "preferred_learning_style": None, "availability_per_week": None,
        }
        with patch(PATCH_TARGET, return_value=response):
            result = va.run(
                "I am Ravi third year IT CGPA 8.0 skills HTML CSS "
                "I enjoy web development career Frontend Developer "
                "I like building websites"  # also triggers Web Development via Python
            )
        interests = result["profile"]["interests"]
        assert interests.count("Web Development") == 1


# ===========================================================================
# TestLearningStyleAndAvailability
# ===========================================================================

class TestLearningStyleAndAvailability:

    def test_learning_style_from_transcript(self):
        """Transcript says "I prefer learning by doing" → project-based."""
        response = {
            "name": "Ravi", "branch": "B.Tech IT", "year": "third",
            "cgpa": "8.0", "skills": ["Java"],
            "interests": ["web development"], "career_goal": "Backend Developer",
            "preferred_learning_style": None, "availability_per_week": None,
        }
        with patch(PATCH_TARGET, return_value=response):
            result = va.run(
                "I am Ravi third year IT CGPA 8.0 skills Java "
                "I prefer learning by doing career Backend Developer "
                "I enjoy building websites"
            )
        assert result["profile"]["preferred_learning_style"] == "project-based"

    def test_learning_style_default_mixed(self):
        """No learning style mentioned → default "mixed"."""
        with patch(PATCH_TARGET, return_value=_COMPLETE_RESPONSE):
            result = va.run("I am Balraju second year IT CGPA 8.58 "
                            "skills Java React career Full Stack Developer")
        assert result["profile"]["preferred_learning_style"] == "mixed"

    def test_availability_from_transcript(self):
        """Transcript explicitly says hours → captured."""
        response = {
            "name": "Ravi", "branch": "B.Tech IT", "year": "third",
            "cgpa": "8.0", "skills": ["Java"],
            "interests": ["web development"], "career_goal": "Backend Developer",
            "preferred_learning_style": None, "availability_per_week": None,
        }
        with patch(PATCH_TARGET, return_value=response):
            result = va.run(
                "I am Ravi third year IT CGPA 8.0 skills Java "
                "I enjoy building websites career Backend Developer "
                "I can study 15 hours a week"
            )
        assert result["profile"]["availability_per_week"] == 15

    def test_availability_from_granite_field(self):
        """Extraction correctly extracts availability → used."""
        response = {
            "name": "Ravi", "branch": "B.Tech IT", "year": "third",
            "cgpa": "8.0", "skills": ["Java"],
            "interests": ["web development"], "career_goal": "Backend Developer",
            "preferred_learning_style": None, "availability_per_week": "12",
        }
        with patch(PATCH_TARGET, return_value=response):
            result = va.run(
                "I am Ravi third year IT CGPA 8.0 skills Java "
                "I enjoy building websites career Backend Developer"
            )
        assert result["profile"]["availability_per_week"] == 12

    def test_availability_default_when_not_stated(self):
        with patch(PATCH_TARGET, return_value=_COMPLETE_RESPONSE):
            result = va.run("I am Balraju second year IT CGPA 8.58 "
                            "skills Java React career Full Stack Developer")
        assert result["profile"]["availability_per_week"] == 10

    def test_availability_out_of_bounds_uses_default(self):
        """Extraction returns "200" for availability → out of bounds → default 10."""
        response = {
            "name": "Ravi", "branch": "B.Tech IT", "year": "third",
            "cgpa": "8.0", "skills": ["Java"],
            "interests": ["web development"], "career_goal": "Backend Developer",
            "preferred_learning_style": None, "availability_per_week": "200",
        }
        with patch(PATCH_TARGET, return_value=response):
            result = va.run(
                "I am Ravi third year IT CGPA 8.0 skills Java "
                "I enjoy web development career Backend Developer"
            )
        assert result["profile"]["availability_per_week"] == 10


# ===========================================================================
# TestCGPANormalisationInAgent
# ===========================================================================

class TestCGPANormalisationInAgent:
    """
    End-to-end CGPA normalisation through the agent (not just the utility).
    """

    def test_written_cgpa_normalised(self):
        response = {
            "name": "Balraju", "branch": "B.Tech IT", "year": "second",
            "cgpa": "eight point five eight",
            "skills": ["Java", "React"],
            "interests": ["web development"], "career_goal": "Full Stack Developer",
            "preferred_learning_style": None, "availability_per_week": None,
        }
        with patch(PATCH_TARGET, return_value=response):
            result = va.run(
                "I am Balraju second year IT my CGPA is eight point five eight "
                "I know Java and React I enjoy building websites "
                "I want to be a Full Stack Developer"
            )
        assert result["profile"]["cgpa"] == 8.58

    def test_percentage_cgpa_normalised(self):
        response = {
            "name": "Ananya", "branch": "B.E. CS", "year": "third",
            "cgpa": "85%",
            "skills": ["Python", "SQL"],
            "interests": ["data science"], "career_goal": "Data Analyst",
            "preferred_learning_style": None, "availability_per_week": None,
        }
        with patch(PATCH_TARGET, return_value=response):
            result = va.run(
                "I am Ananya third year CS my score is 85% "
                "I know Python SQL I am interested in data science "
                "I want to become a Data Analyst"
            )
        assert result["profile"]["cgpa"] == 8.5

    def test_invalid_cgpa_triggers_missing(self):
        """Extraction returns a nonsense CGPA → normalises to None → cgpa in missing_fields."""
        response = {
            "name": "Ananya", "branch": "B.E. CS", "year": "third",
            "cgpa": "not a number at all",
            "skills": ["Python"],
            "interests": ["data science"], "career_goal": "Data Analyst",
            "preferred_learning_style": None, "availability_per_week": None,
        }
        with patch(PATCH_TARGET, return_value=response):
            result = va.run(
                "I am Ananya third year CS I know Python "
                "I like data science I want to be a Data Analyst"
            )
        assert "cgpa" in result.get("missing_fields", [])


# ===========================================================================
# TestSkillsCanonicalization
# ===========================================================================

class TestSkillsCanonicalization:

    def test_lowercase_skills_canonicalized(self):
        response = {
            "name": "Kiran", "branch": "B.Tech IT", "year": "second",
            "cgpa": "8.0", "skills": ["javascript", "react", "node"],
            "interests": ["web development"], "career_goal": "Full Stack Developer",
            "preferred_learning_style": None, "availability_per_week": None,
        }
        with patch(PATCH_TARGET, return_value=response):
            result = va.run(
                "I am Kiran second year IT CGPA 8.0 "
                "I know javascript react and node "
                "I enjoy building websites want to be Full Stack Developer"
            )
        skills = result["profile"]["skills"]
        assert "JavaScript" in skills
        assert "React" in skills

    def test_duplicate_skills_deduplicated(self):
        response = {
            "name": "Kiran", "branch": "B.Tech IT", "year": "second",
            "cgpa": "8.0",
            "skills": ["Python", "python", "PYTHON"],
            "interests": ["data science"], "career_goal": "Data Analyst",
            "preferred_learning_style": None, "availability_per_week": None,
        }
        with patch(PATCH_TARGET, return_value=response):
            result = va.run(
                "I am Kiran second year IT CGPA 8.0 I know Python "
                "I like data science I want to be a Data Analyst"
            )
        skills = result["profile"]["skills"]
        assert skills.count("Python") == 1
