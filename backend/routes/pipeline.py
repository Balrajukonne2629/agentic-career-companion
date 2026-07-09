"""
routes/pipeline.py
==================
Stateless Agent pipeline endpoints.

All pipeline routes receive input states in the HTTP POST request body
and return the corresponding agent output as JSON.
"""

import datetime
import json as _json
import traceback
from typing import Any, Dict

from flask import Blueprint, jsonify, request, session

from errors import AppError, SessionError
from logger import get_logger

log = get_logger(__name__)
pipeline_bp = Blueprint("pipeline", __name__)


# ---------------------------------------------------------------------------
# Route Logging Helpers
# ---------------------------------------------------------------------------

def _log_route_start(route_name: str, payload: dict):
    print("==================================================")
    print(f"ROUTE STARTED: {route_name}")
    print(f"Timestamp: {datetime.datetime.utcnow().isoformat()}Z")
    print("-------------------------------------------------")
    print("Request Headers:")
    headers = dict(request.headers)
    for k, v in headers.items():
        print(f"  {k}: {v}")
    print("-------------------------------------------------")
    print("Request JSON:")
    import json as _json
    try:
        print(_json.dumps(payload, indent=2, default=str))
    except Exception:
        print(payload)
    print("-------------------------------------------------")
    print("SESSION CONTENTS:")
    print("  SESSION (all keys):", list(session.keys()) if session else "(empty)")
    print("  student_profile:", session.get("student_profile"))
    print("  career_recommendations:", session.get("career_recommendations"))
    print("  skill_gap:", session.get("skill_gap"))
    print("  roadmap:", session.get("roadmap"))
    print("  SESSION (full dict):", dict(session))
    print("-------------------------------------------------")

def _log_intermediate(variables: dict):
    import json as _json
    print("Intermediate Variables:")
    for k, v in variables.items():
        try:
            if isinstance(v, (dict, list)):
                print(f"  {k}:")
                print(_json.dumps(v, indent=4, default=str))
            else:
                print(f"  {k}: {v}")
        except Exception:
            print(f"  {k}: {v}")
    print("-------------------------------------------------")

def _log_route_end(route_name: str, response_body: Any, status_code: int):
    import json as _json
    print("-------------------------------------------------")
    print(f"ROUTE OUTPUT: {route_name}")
    print(f"Status code: {status_code}")
    print("Final JSON response:")
    try:
        print(_json.dumps(response_body, indent=2, default=str))
    except Exception:
        print(response_body)
    print("-------------------------------------------------")
    print(f"ROUTE END: {route_name}")
    print("==================================================")



def _require_body_field(body: dict, key: str) -> Any:
    """
    Retrieve a required field from the request body or raise SessionError (400).

    Parameters
    ----------
    body : dict
        The request body dictionary.
    key : str
        The field key to retrieve.

    Returns
    -------
    Any
        The field value.

    Raises
    ------
    SessionError
        If the key is absent or None.
    """
    value = body.get(key)
    if value is None:
        raise SessionError(f"Missing required field '{key}' in request body.")
    return value


# ---------------------------------------------------------------------------
# Pipeline routes
# ---------------------------------------------------------------------------

@pipeline_bp.route("/validate", methods=["POST"])
def validate():
    """
    POST /api/validate

    Body: { "transcript": str, "partial_profile": dict (optional) }

    Runs Validation Agent. Returns complete or incomplete profile.
    """
    try:
        body = request.get_json(silent=True) or {}
        _log_route_start("/api/validate", body)
        transcript = body.get("transcript", "").strip()
        partial = body.get("partial_profile")
        _log_intermediate({"transcript": transcript, "partial_profile": partial})

        if not transcript:
            resp = {
                "error": True,
                "message": "Request body must contain a non-empty 'transcript' field.",
            }
            _log_route_end("/api/validate", resp, 400)
            return jsonify(resp), 400

        if len(transcript) < 30:
            resp = {
                "error": True,
                "message": (
                    "Transcript is too short (minimum 30 characters). "
                    "Please provide more detail about yourself."
                ),
            }
            _log_route_end("/api/validate", resp, 400)
            return jsonify(resp), 400

        from agents.validation_agent import run as run_validation
        result = run_validation(transcript, partial)

        if result.get("status") == "complete":
            log.info("/api/validate → complete | name=%s", result["profile"].get("name"))
        else:
            log.info(
                "/api/validate → incomplete | missing=%s",
                result.get("missing_fields", []),
            )

        _log_route_end("/api/validate", result, 200)
        return jsonify(result), 200

    except AppError as exc:
        log.error("/api/validate error: %s", exc.message)
        _log_route_end("/api/validate", exc.to_dict(), exc.status_code)
        return jsonify(exc.to_dict()), exc.status_code


@pipeline_bp.route("/profile", methods=["POST"])
def profile():
    """
    POST /api/profile

    Body: { "student_profile": dict }

    Runs Profile Agent on student_profile.
    """
    # ------------------------------------------------------------------
    # STEP 1 - Request received
    # ------------------------------------------------------------------
    print("")
    print("=================================================")
    print("===== PROFILE ROUTE START =====")
    print("=================================================")
    print(f"Timestamp: {datetime.datetime.utcnow().isoformat()}Z")
    print("")
    print("--- Request Headers ---")
    for header_key, header_val in request.headers:
        print(f"  {header_key}: {header_val}")
    print("")
    print("--- Request Body Raw (bytes) ---")
    raw_bytes = request.get_data()
    print(repr(raw_bytes))
    print("")
    print("--- Request JSON (parsed) ---")
    try:
        raw_json = request.get_json(silent=True, force=True)
        print(_json.dumps(raw_json, indent=2, default=str))
    except Exception as _parse_exc:
        print(f"  [Could not parse JSON: {_parse_exc}]")
        raw_json = None
    print("")
    print("--- SESSION CONTENTS ---")
    print("  dict(session):", dict(session))
    print("  student_profile (from session):", session.get("student_profile"))
    print("=================================================")
    print("STEP 1 - Request received")
    print("=================================================")
    print("")

    try:
        body = request.get_json(silent=True) or {}
        _log_route_start("/api/profile", body)

        # --------------------------------------------------------------
        # STEP 2 - Profile extracted
        # --------------------------------------------------------------
        print("=================================================")
        print("STEP 2 - Profile extracted")
        print("=================================================")
        print("  student_profile key present in body:", "student_profile" in body)
        print("  student_profile from request.json:")
        sp_from_body = body.get("student_profile")
        try:
            print(_json.dumps(sp_from_body, indent=4, default=str))
        except Exception:
            print(" ", sp_from_body)
        print("  student_profile from session:", session.get("student_profile"))
        print("")

        student_profile = _require_body_field(body, "student_profile")
        _log_intermediate({"student_profile": student_profile})

        # --------------------------------------------------------------
        # STEP 3 - Processing profile
        # --------------------------------------------------------------
        print("=================================================")
        print("STEP 3 - Processing profile")
        print("=================================================")
        print("  Fields present in student_profile:")
        if isinstance(student_profile, dict):
            for field_key, field_val in student_profile.items():
                print(f"    {field_key}: {field_val!r}")
        else:
            print("  [student_profile is not a dict — type:", type(student_profile).__name__, "]")
        print("")

        # --------------------------------------------------------------
        # STEP 4 - Building profile summary (calling Profile Agent)
        # --------------------------------------------------------------
        print("=================================================")
        print("STEP 4 - Building profile summary")
        print("=================================================")
        print("  Calling agents.profile_agent.run() ...")
        print("")

        from agents.profile_agent import run as run_profile
        result = run_profile(student_profile)

        print("  Profile Agent returned:")
        try:
            print(_json.dumps(result, indent=4, default=str))
        except Exception:
            print(" ", result)
        print("")

        # --------------------------------------------------------------
        # STEP 5 - Returning response
        # --------------------------------------------------------------
        print("=================================================")
        print("STEP 5 - Returning response")
        print("=================================================")
        print(f"  Status: 200")
        print(f"  career_readiness_score: {result.get('career_readiness_score')}")
        print(f"  profile_tier: {result.get('profile_tier')}")
        print(f"  score_band: {result.get('score_band')}")
        print(f"  estimated_time_to_ready_months: {result.get('estimated_time_to_ready_months')}")
        print("")

        log.info(
            "/api/profile → score=%s tier=%s",
            result.get("career_readiness_score"),
            result.get("profile_tier"),
        )
        _log_route_end("/api/profile", result, 200)
        return jsonify(result), 200

    except AppError as exc:
        print("")
        print("=================================================")
        print("[PROFILE ROUTE] AppError caught")
        print("=================================================")
        print("  message:", exc.message)
        print("  status_code:", exc.status_code)
        print("")
        print("FULL TRACEBACK:")
        print(traceback.format_exc())
        print("=================================================")
        log.error("/api/profile error: %s", exc.message)
        _log_route_end("/api/profile", exc.to_dict(), exc.status_code)
        return jsonify(exc.to_dict()), exc.status_code

    except Exception as exc:
        print("")
        print("=================================================")
        print("[PROFILE ROUTE] Unexpected Exception caught")
        print("=================================================")
        print("  type:", type(exc).__name__)
        print("  message:", str(exc))
        print("")
        print("FULL TRACEBACK:")
        print(traceback.format_exc())
        print("=================================================")
        log.error("/api/profile unexpected error: %s", str(exc))
        error_body = {"error": True, "message": f"Internal server error: {str(exc)}"}
        _log_route_end("/api/profile", error_body, 500)
        return jsonify(error_body), 500


@pipeline_bp.route("/recommend", methods=["POST"])
def recommend():
    """
    POST /api/recommend

    Body: { "student_profile": dict, "profile_analysis": dict }

    Runs Career Recommendation Agent.
    """
    try:
        body = request.get_json(silent=True) or {}
        _log_route_start("/api/recommend", body)
        student_profile = _require_body_field(body, "student_profile")
        profile_analysis = _require_body_field(body, "profile_analysis")
        _log_intermediate({
            "student_profile": student_profile,
            "profile_analysis": profile_analysis
        })

        from agents.career_recommendation_agent import run as run_recommend
        result = run_recommend(student_profile, profile_analysis)

        top_career = result[0]["title"] if result else "none"
        log.info("/api/recommend → top_career=%s", top_career)
        _log_route_end("/api/recommend", result, 200)
        return jsonify(result), 200

    except AppError as exc:
        log.error("/api/recommend error: %s", exc.message)
        _log_route_end("/api/recommend", exc.to_dict(), exc.status_code)
        return jsonify(exc.to_dict()), exc.status_code


@pipeline_bp.route("/skillgap", methods=["POST"])
def skillgap():
    """
    POST /api/skillgap

    Body: { "student_profile": dict, "recommendations": list }

    Runs Skill Gap Agent using the top recommendation as the target career.
    """
    try:
        body = request.get_json(silent=True) or {}
        _log_route_start("/api/skillgap", body)
        student_profile = _require_body_field(body, "student_profile")
        recommendations = _require_body_field(body, "recommendations")
        top_recommendation = recommendations[0] if recommendations else None
        _log_intermediate({
            "student_profile": student_profile,
            "recommendations": recommendations,
            "top_recommendation": top_recommendation
        })

        if not top_recommendation:
            resp = {
                "error": True,
                "message": "No career recommendations available. Pass recommendations array.",
            }
            _log_route_end("/api/skillgap", resp, 400)
            return jsonify(resp), 400

        from agents.skill_gap_agent import run as run_skillgap
        result = run_skillgap(student_profile, top_recommendation)

        log.info(
            "/api/skillgap → target=%s total_gaps=%s",
            result.get("target_career"),
            result.get("gap_summary", {}).get("total_gap_items"),
        )
        _log_route_end("/api/skillgap", result, 200)
        return jsonify(result), 200

    except AppError as exc:
        log.error("/api/skillgap error: %s", exc.message)
        _log_route_end("/api/skillgap", exc.to_dict(), exc.status_code)
        return jsonify(exc.to_dict()), exc.status_code


@pipeline_bp.route("/roadmap", methods=["POST"])
def roadmap():
    """
    POST /api/roadmap

    Body: { "student_profile": dict, "profile_analysis": dict, "skill_gap": dict, "recommendations": list }

    Runs Roadmap Agent.
    """
    try:
        body = request.get_json(silent=True) or {}
        _log_route_start("/api/roadmap", body)
        student_profile = _require_body_field(body, "student_profile")
        profile_analysis = _require_body_field(body, "profile_analysis")
        skill_gap = _require_body_field(body, "skill_gap")
        recommendations = _require_body_field(body, "recommendations")
        top_recommendation = recommendations[0] if recommendations else None
        _log_intermediate({
            "student_profile": student_profile,
            "profile_analysis": profile_analysis,
            "skill_gap": skill_gap,
            "recommendations": recommendations,
            "top_recommendation": top_recommendation
        })

        if not top_recommendation:
            resp = {
                "error": True,
                "message": "No career recommendations in session. Pass recommendations array.",
            }
            _log_route_end("/api/roadmap", resp, 400)
            return jsonify(resp), 400

        from agents.roadmap_agent import run as run_roadmap

        # Log roadmap_context (the key variables driving the Granite prompt)
        print("==================================================")
        print("ROADMAP CONTEXT (inputs to roadmap_agent.run)")
        print("==================================================")
        print(f"  target_career: {top_recommendation.get('title') if top_recommendation else 'N/A'}")
        print(f"  target_career_id: {top_recommendation.get('career_id') if top_recommendation else 'N/A'}")
        print(f"  profile_tier: {profile_analysis.get('profile_tier') if profile_analysis else 'N/A'}")
        print(f"  availability_per_week: {student_profile.get('availability_per_week') if student_profile else 'N/A'}")
        print(f"  preferred_learning_style: {student_profile.get('preferred_learning_style') if student_profile else 'N/A'}")
        print(f"  skill_gap keys: {list(skill_gap.keys()) if skill_gap else 'N/A'}")
        print(f"  skills_to_learn count: {len(skill_gap.get('skills_to_learn', [])) if skill_gap else 'N/A'}")
        print(f"  skills_already_have count: {len(skill_gap.get('skills_already_have', [])) if skill_gap else 'N/A'}")
        print("==================================================")

        result = run_roadmap(
            student_profile,
            profile_analysis,
            skill_gap,
            top_recommendation,
        )

        # Print FINAL RESPONSE stage log
        print("==================================================")
        print("FINAL RESPONSE")
        print("==================================================")
        print("Dashboard Data:")
        print(f"  Target Career: {result.get('target_career')}")
        print(f"  Total Milestones: 3 phases (30, 60, 90 day)")
        print(f"  Certifications Picked: {[c.get('name') for c in result.get('certifications', [])]}")
        print(f"  Projects Picked: {[p.get('title') for p in result.get('projects', [])]}")
        print()

        log.info("/api/roadmap → target=%s", result.get("target_career"))
        _log_route_end("/api/roadmap", result, 200)
        return jsonify(result), 200

    except AppError as exc:
        log.error("/api/roadmap error: %s", exc.message)
        _log_route_end("/api/roadmap", exc.to_dict(), exc.status_code)
        return jsonify(exc.to_dict()), exc.status_code


@pipeline_bp.route("/pipeline", methods=["POST"])
def full_pipeline():
    """
    POST /api/pipeline

    Convenience endpoint: runs all 5 agents in sequence and returns
    a single merged JSON response containing all pipeline outputs.

    Body: { "transcript": str }
    """
    try:
        body = request.get_json(silent=True) or {}
        _log_route_start("/api/pipeline", body)
        transcript = body.get("transcript", "").strip()
        _log_intermediate({"transcript": transcript})

        if not transcript or len(transcript) < 30:
            resp = {
                "error": True,
                "message": "Provide a 'transcript' of at least 30 characters.",
            }
            _log_route_end("/api/pipeline", resp, 400)
            return jsonify(resp), 400

        # Step 1 — Validation
        from agents.validation_agent import run as run_validation
        val_result = run_validation(transcript)
        _log_intermediate({"validation_result": val_result})

        if val_result.get("status") != "complete":
            _log_route_end("/api/pipeline", val_result, 200)
            return jsonify(val_result), 200  # Incomplete — frontend asks follow-ups

        student_profile = val_result["profile"]
        _log_intermediate({"student_profile": student_profile})

        # Step 2 — Profile
        from agents.profile_agent import run as run_profile
        profile_analysis = run_profile(student_profile)
        _log_intermediate({"profile_analysis": profile_analysis})

        # Step 3 — Career Recommendations
        from agents.career_recommendation_agent import run as run_recommend
        recommendations = run_recommend(student_profile, profile_analysis)
        _log_intermediate({"recommendations": recommendations})

        # Step 4 — Skill Gap
        from agents.skill_gap_agent import run as run_skillgap
        skill_gap = run_skillgap(student_profile, recommendations[0])
        _log_intermediate({"skill_gap": skill_gap})

        # Step 5 — Roadmap
        from agents.roadmap_agent import run as run_roadmap
        roadmap_result = run_roadmap(
            student_profile, profile_analysis, skill_gap, recommendations[0]
        )
        _log_intermediate({"roadmap_result": roadmap_result})

        response_body = {
            "status": "complete",
            "profile": student_profile,
            "profile_analysis": profile_analysis,
            "recommendations": recommendations,
            "skill_gap": skill_gap,
            "roadmap": roadmap_result,
        }

        # Print FINAL RESPONSE stage log
        print("==================================================")
        print("FINAL RESPONSE")
        print("==================================================")
        print("Dashboard Data:")
        print(f"  Target Career: {roadmap_result.get('target_career')}")
        print(f"  Total Milestones: 3 phases (30, 60, 90 day)")
        print(f"  Certifications Picked: {[c.get('name') for c in roadmap_result.get('certifications', [])]}")
        print(f"  Projects Picked: {[p.get('title') for p in roadmap_result.get('projects', [])]}")
        print()

        log.info("/api/pipeline → complete for '%s'", student_profile.get("name"))
        _log_route_end("/api/pipeline", response_body, 200)
        return jsonify(response_body), 200

    except AppError as exc:
        log.error("/api/pipeline error: %s", exc.message)
        _log_route_end("/api/pipeline", exc.to_dict(), exc.status_code)
        return jsonify(exc.to_dict()), exc.status_code


@pipeline_bp.route("/session", methods=["DELETE"])
def clear_session():
    """
    DELETE /api/session

    No-op route for frontend compatibility.
    """
    log.info("/api/session cleared (stateless: no-op)")
    return jsonify({"message": "No server-side session to clear."}), 200
