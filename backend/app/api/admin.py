from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from app.api.helpers import require_admin
from app.services import admin_service

bp = Blueprint("admin", __name__)


@bp.get("/users")
@jwt_required()
def list_users():
    """Registered users plus their most recent login/logout time -- the
    admin dashboard's user table. Admin-only, see require_admin."""
    _admin, error = require_admin()
    if error:
        return error

    return jsonify(users=admin_service.list_users_with_activity())
