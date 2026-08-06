from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models.user import User

bp = Blueprint("auth", __name__)


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify(error="email and password are required"), 400

    if User.query.filter_by(email=email).first() is not None:
        return jsonify(error="an account with this email already exists"), 409

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify(access_token=token, user={"id": user.id, "email": user.email}), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        return jsonify(error="invalid email or password"), 401

    token = create_access_token(identity=str(user.id))
    return jsonify(access_token=token, user={"id": user.id, "email": user.email}), 200
