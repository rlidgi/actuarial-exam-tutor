from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token

from app.services import supabase_auth_service, user_service

bp = Blueprint("auth", __name__)


@bp.post("/exchange")
def exchange():
    """Trade a verified Supabase Auth access token (Google OAuth or magic
    link -- both handled client-side by supabase-js) for this app's own
    JWT. The only seam between Supabase Auth and the rest of the app.
    """
    data = request.get_json(silent=True) or {}
    supabase_token = data.get("supabase_access_token", "")
    if not supabase_token:
        return jsonify(error="supabase_access_token is required"), 400

    try:
        claims = supabase_auth_service.verify_access_token(supabase_token)
    except supabase_auth_service.InvalidSupabaseToken:
        return jsonify(error="invalid or expired session"), 401

    try:
        user, is_new_user = user_service.find_or_create_by_external_identity(
            claims["sub"], claims["email"]
        )
    except user_service.IdentityConflict as exc:
        return jsonify(error=str(exc)), 409

    token = create_access_token(identity=str(user.id))
    return (
        jsonify(
            access_token=token,
            user={"id": user.id, "email": user.email},
            is_new_user=is_new_user,
        ),
        200,
    )
