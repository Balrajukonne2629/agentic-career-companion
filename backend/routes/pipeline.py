"""
routes/pipeline.py
==================
Agent pipeline endpoints.

All five pipeline routes follow the same pattern:
    1. Read required session data from Flask session.
    2. Call the corresponding agent's run() function.
    3. Store agent output in Flask session.
    4. Return agent output as JSON.

The full pipeline must be called in sequence:
    POST /api/validate     → session["student_profile"]
    POST /api/profile      → session["profile_analysis"]
    POST /api/recommend    → session["recommendations"]
    POST /api/skillgap     → session["skill_gap"]
    POST /api/roadmap      → session["roadmap"]

A convenience endpoint runs all 5 agents in a single request:
    POST /api/pipeline     → all session keys + merged JSON response

Session cleared via:
    DELETE /api/session
"""

from typing import Any, Dict

from flask import Blueprint, jsonify, request, session

from errors import AppError, SessionError
from logger import get_logger

log = get_logger(__name__)
pipeline_bp = Blueprint("pipeline", __name__)


# ---------------------------------------------------------------------------
# Session key constants — single source of truth
# ---------------------------------------------------------------------------
SESSION_STUDENT_PROFILE = "student_profile"
SESSION_PROFILE_ANALYSIS = "profile_analysis"
SESSION_RECOMMENDATIONS = "recommendations"
SESSION_SKILL_GAP = "skill_gap"
SESSION_ROADMAP = "roadmap"


def _require_session_key(key: str) -> Any:
    """
    Retrieve a value from Flask session or raise SessionError.

    Parameters
    ----------
    key : str
        Session key to retrieve.

    Returns
    -------
    Any
        The session value.

    Raises
    ------
    SessionError
        If the key is absent, indicating the pipeline was called out of order.
    """
    value = session.get(key)
    if value is None:
        raise SessionError(
            f"Session key '{key}' is missing. "
            "The pipeline agents must be called in order: "
            "validate → profile → recommend → skillgap → roadmap."
        )
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
            session[SESSION_STUDENT_PROFILE] = result["profile"]
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

    Reads session["student_profile"]. Runs Profile Agent.
    """
    try:
        student_profile = _require_session_key(SESSION_STUDENT_PROFILE)

        from agents.profile_agent import run as run_profile
        result = run_profile(student_profile)

        session[SESSION_PROFILE_ANALYSIS] = result
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

    Reads session["student_profile"] and session["profile_analysis"].
    Runs Career Recommendation Agent.
    """
    try:
        student_profile  = _require_session_key(SESSION_STUDENT_PROFILE)
        profile_analysis = _require_session_key(SESSION_PROFILE_ANALYSIS)

        from agents.career_recommendation_agent import run as run_recommend
        result = run_recommend(student_profile, profile_analysis)

        session[SESSION_RECOMMENDATIONS] = result
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

    Reads session["student_profile"] and session["recommendations"].
    Runs Skill Gap Agent using the top recommendation as the target career.
    """
    try:
        student_profile   = _require_session_key(SESSION_STUDENT_PROFILE)
        recommendations   = _require_session_key(SESSION_RECOMMENDATIONS)
        top_recommendation = recommendations[0] if recommendations else None

        if not top_recommendation:
            return jsonify({
                "error": True,
                "message": "No career recommendations available. Call /api/recommend first.",
            }), 400

        from agents.skill_gap_agent import run as run_skillgap
        result = run_skillgap(student_profile, top_recommendation)

        session[SESSION_SKILL_GAP] = result
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

    Reads session["student_profile"], session["profile_analysis"],
    session["skill_gap"], session["recommendations"].
    Runs Roadmap Agent.
    """
    try:
        student_profile  = _require_session_key(SESSION_STUDENT_PROFILE)
        profile_analysis = _require_session_key(SESSION_PROFILE_ANALYSIS)
        skill_gap        = _require_session_key(SESSION_SKILL_GAP)
        recommendations  = _require_session_key(SESSION_RECOMMENDATIONS)
        top_recommendation = recommendations[0] if recommendations else None

        if not top_recommendation:
            return jsonify({
                "error": True,
                "message": "No career recommendations in session. Call /api/recommend first.",
            }), 400

        from agents.roadmap_agent import run as run_roadmap
        result = run_roadmap(
            student_profile,
            profile_analysis,
            skill_gap,
            top_recommendation,
        )

        session[SESSION_ROADMAP] = result

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

    Useful for the frontend to trigger the full pipeline in one call
    and display a progress indicator while waiting.
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
        session[SESSION_STUDENT_PROFILE] = student_profile

        # Step 2 — Profile
        from agents.profile_agent import run as run_profile
        profile_analysis = run_profile(student_profile)
        session[SESSION_PROFILE_ANALYSIS] = profile_analysis

        # Step 3 — Career Recommendations
        from agents.career_recommendation_agent import run as run_recommend
        recommendations = run_recommend(student_profile, profile_analysis)
        session[SESSION_RECOMMENDATIONS] = recommendations

        # Step 4 — Skill Gap
        from agents.skill_gap_agent import run as run_skillgap
        skill_gap = run_skillgap(student_profile, recommendations[0])
        session[SESSION_SKILL_GAP] = skill_gap

        # Step 5 — Roadmap
        from agents.roadmap_agent import run as run_roadmap
        roadmap_result = run_roadmap(
            student_profile, profile_analysis, skill_gap, recommendations[0]
        )
        session[SESSION_ROADMAP] = roadmap_result

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

    Clears all pipeline data from the Flask session.
    Used by the "Start Over" button on the Career Dashboard.
    """
    session.clear()
    log.info("/api/session cleared")
    return jsonify({"message": "Session cleared. Ready for a new profile."}), 200
