import sys
import os
import types
import json
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
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_clear_session_route(client):
    """DELETE /api/session should return success."""
    res = client.delete("/api/session")
    assert res.status_code == 200
    data = res.get_json()
    assert "No server-side session to clear." in data["message"]

def test_validate_route_missing_transcript(client):
    """POST /api/validate with empty transcript should return 400."""
    res = client.post("/api/validate", json={})
    assert res.status_code == 400
    assert "transcript" in res.get_json()["message"]

def test_validate_route_too_short(client):
    """POST /api/validate with short transcript should return 400."""
    res = client.post("/api/validate", json={"transcript": "hello"})
    assert res.status_code == 400
    assert "too short" in res.get_json()["message"]

def test_profile_route_missing_payload(client):
    """POST /api/profile with missing student_profile should return 400."""
    res = client.post("/api/profile", json={})
    assert res.status_code == 400
    assert "student_profile" in res.get_json()["message"]

def test_recommend_route_missing_payload(client):
    """POST /api/recommend with missing arguments should return 400."""
    res = client.post("/api/recommend", json={"student_profile": {}})
    assert res.status_code == 400
    assert "profile_analysis" in res.get_json()["message"]

def test_skillgap_route_missing_payload(client):
    """POST /api/skillgap with missing arguments should return 400."""
    res = client.post("/api/skillgap", json={"student_profile": {}})
    assert res.status_code == 400
    assert "recommendations" in res.get_json()["message"]

def test_roadmap_route_missing_payload(client):
    """POST /api/roadmap with missing arguments should return 400."""
    res = client.post("/api/roadmap", json={"student_profile": {}})
    assert res.status_code == 400
    assert "profile_analysis" in res.get_json()["message"]

@patch("agents.career_recommendation_agent.call_granite_strong")
@patch("agents.roadmap_agent.call_granite_strong")
def test_full_stateless_flow(mock_road, mock_career, client):
    """Verify that a full stateless chain executes successfully by passing bodies explicitly."""
    # Mock career recommendations response
    mock_career.return_value = json.dumps([
        {"title": "Full Stack Developer", "confidence_percent": 90, "reasoning": "Fits React/SQL skills"},
        {"title": "Software Engineer", "confidence_percent": 80, "reasoning": "Fits Java/Python skills"},
        {"title": "Backend Developer", "confidence_percent": 70, "reasoning": "Fits Python/SQL skills"}
    ])

    # Mock roadmap response
    mock_road.return_value = json.dumps({
        "30_day": {"focus": "HTML/CSS", "weekly_goals": [["Learn HTML", "Build page"], [], [], []], "resources": ["W3Schools"]},
        "60_day": {"focus": "React", "weekly_goals": [["React Hooks"], [], [], []], "resources": ["React Docs"]},
        "90_day": {"focus": "Node.js", "weekly_goals": [["Express"], [], [], []], "resources": ["Node Docs"]}
    })

    # Step 1: Validate transcript
    transcript = (
        "Hi, my name is Balraju. I am studying B.Tech IT in my second year. "
        "My CGPA is 8.58. I know Java, React, Python, SQL, and C++. I enjoy web development. "
        "My career goal is to become a Full Stack Developer."
    )
    res_val = client.post("/api/validate", json={"transcript": transcript})
    assert res_val.status_code == 200
    val_data = res_val.get_json()
    assert val_data["status"] == "complete"
    student_profile = val_data["profile"]

    # Step 2: Profile analysis
    res_prof = client.post("/api/profile", json={"student_profile": student_profile})
    assert res_prof.status_code == 200
    prof_analysis = res_prof.get_json()
    assert "profile_tier" in prof_analysis

    # Step 3: Recommend careers
    res_rec = client.post("/api/recommend", json={
        "student_profile": student_profile,
        "profile_analysis": prof_analysis
    })
    assert res_rec.status_code == 200
    recommendations = res_rec.get_json()
    assert len(recommendations) == 3

    # Step 4: Skill gap analysis
    res_gap = client.post("/api/skillgap", json={
        "student_profile": student_profile,
        "recommendations": recommendations
    })
    assert res_gap.status_code == 200
    skill_gap = res_gap.get_json()
    assert "skills_to_learn" in skill_gap

    # Step 5: Roadmap generation
    res_road = client.post("/api/roadmap", json={
        "student_profile": student_profile,
        "profile_analysis": prof_analysis,
        "skill_gap": skill_gap,
        "recommendations": recommendations
    })
    assert res_road.status_code == 200
    roadmap = res_road.get_json()
    assert "30_day" in roadmap
