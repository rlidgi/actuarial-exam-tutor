from flask import Blueprint, jsonify

bp = Blueprint("chat", __name__)


@bp.post("/message")
def send_message():
    # The tutor orchestrator (LLM tool-calling loop) is Phase 2 work.
    # This stub exists so the frontend has a stable endpoint to build against.
    return jsonify(error="tutor orchestration not yet implemented"), 501
