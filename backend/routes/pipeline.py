"""
routes/pipeline.py
==================
Stateless Agent pipeline endpoints.

All pipeline routes receive input states in the HTTP POST request body
and return the corresponding agent output as JSON.
"""

from typing import Any, Dict

from flask import Blueprint, jsonify, request

from errors import AppError, SessionError
from logger import get_logger

log = get_logger(__name__)
pipeline_bp = Blueprint("pipeline", __name__)


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
        transcript = body.get("transcript", "").strip()

        if not transcript:
            return jsonify({
                "error": True,
                "message": "Request body must contain a non-empty 'transcript' field.",
            }), 400

        if len(transcript) < 30:
            return jsonify({
                "error": True,
                "message": (
                    "Transcript is too short (minimum 30 characters). "
                    "Please provide more detail about yourself."
                ),
            }), 400

        from agents.validation_agent import run as run_validation
        partial = body.get("partial_profile")
        result = run_validation(transcript, partial)

        if result.get("status") == "complete":
            log.info("/api/validate → complete | name=%s", result["profile"].get("name"))
        else:
            log.info(
                "/api/validate → incomplete | missing=%s",
                result.get("missing_fields", []),
            )

        return jsonify(result), 200

    except AppError as exc:
        log.error("/api/validate error: %s", exc.message)
        return jsonify(exc.to_dict()), exc.status_code


@pipeline_bp.route("/profile", methods=["POST"])
def profile():
    """
    POST /api/profile

    Body: { "student_profile": dict }

    Runs Profile Agent on student_profile.
    """
    try:
        body = request.get_json(silent=True) or {}
        student_profile = _require_body_field(body, "student_profile")

        from agents.profile_agent import run as run_profile
        result = run_profile(student_profile)

        log.info(
            "/api/profile → score=%s tier=%s",
            result.get("career_readiness_score"),
            result.get("profile_tier"),
        )
        return jsonify(result), 200

    except AppError as exc:
        log.error("/api/profile error: %s", exc.message)
        return jsonify(exc.to_dict()), exc.status_code


@pipeline_bp.route("/recommend", methods=["POST"])
def recommend():
    """
    POST /api/recommend

    Body: { "student_profile": dict, "profile_analysis": dict }

    Runs Career Recommendation Agent.
    """
    try:
        body = request.get_json(silent=True) or {}
        student_profile = _require_body_field(body, "student_profile")
        profile_analysis = _require_body_field(body, "profile_analysis")

        from agents.career_recommendation_agent import run as run_recommend
        result = run_recommend(student_profile, profile_analysis)

        top_career = result[0]["title"] if result else "none"
        log.info("/api/recommend → top_career=%s", top_career)
        return jsonify(result), 200

    except AppError as exc:
        log.error("/api/recommend error: %s", exc.message)
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
        student_profile = _require_body_field(body, "student_profile")
        recommendations = _require_body_field(body, "recommendations")
        top_recommendation = recommendations[0] if recommendations else None

        if not top_recommendation:
            return jsonify({
                "error": True,
                "message": "No career recommendations available. Pass recommendations array.",
            }), 400

        from agents.skill_gap_agent import run as run_skillgap
        result = run_skillgap(student_profile, top_recommendation)

        log.info(
            "/api/skillgap → target=%s total_gaps=%s",
            result.get("target_career"),
            result.get("gap_summary", {}).get("total_gap_items"),
        )
        return jsonify(result), 200

    except AppError as exc:
        log.error("/api/skillgap error: %s", exc.message)
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
        student_profile = _require_body_field(body, "student_profile")
        profile_analysis = _require_body_field(body, "profile_analysis")
        skill_gap = _require_body_field(body, "skill_gap")
        recommendations = _require_body_field(body, "recommendations")
        top_recommendation = recommendations[0] if recommendations else None

        if not top_recommendation:
            return jsonify({
                "error": True,
                "message": "No career recommendations in session. Pass recommendations array.",
            }), 400

        from agents.roadmap_agent import run as run_roadmap
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
        return jsonify(result), 200

    except AppError as exc:
        log.error("/api/roadmap error: %s", exc.message)
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
        transcript = body.get("transcript", "").strip()

        if not transcript or len(transcript) < 30:
            return jsonify({
                "error": True,
                "message": "Provide a 'transcript' of at least 30 characters.",
            }), 400

        # Step 1 — Validation
        from agents.validation_agent import run as run_validation
        val_result = run_validation(transcript)

        if val_result.get("status") != "complete":
            return jsonify(val_result), 200  # Incomplete — frontend asks follow-ups

        student_profile = val_result["profile"]

        # Step 2 — Profile
        from agents.profile_agent import run as run_profile
        profile_analysis = run_profile(student_profile)

        # Step 3 — Career Recommendations
        from agents.career_recommendation_agent import run as run_recommend
        recommendations = run_recommend(student_profile, profile_analysis)

        # Step 4 — Skill Gap
        from agents.skill_gap_agent import run as run_skillgap
        skill_gap = run_skillgap(student_profile, recommendations[0])

        # Step 5 — Roadmap
        from agents.roadmap_agent import run as run_roadmap
        roadmap_result = run_roadmap(
            student_profile, profile_analysis, skill_gap, recommendations[0]
        )

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
        return jsonify(response_body), 200

    except AppError as exc:
        log.error("/api/pipeline error: %s", exc.message)
        return jsonify(exc.to_dict()), exc.status_code


@pipeline_bp.route("/session", methods=["DELETE"])
def clear_session():
    """
    DELETE /api/session

    No-op route for frontend compatibility.
    """
    log.info("/api/session cleared (stateless: no-op)")
    return jsonify({"message": "No server-side session to clear."}), 200
