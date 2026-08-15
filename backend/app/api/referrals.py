from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models.user import User
from app.services import referral_service

bp = Blueprint("referrals", __name__)


@bp.get("")
@jwt_required()
def summary():
    """Everything the account/referrals page needs: this user's own
    referral link, how many completed referrals they have, and a history of
    every reward they've earned (either side -- referrer or referred)."""
    user = db.session.get(User, int(get_jwt_identity()))
    code = referral_service.get_or_create_referral_code(user)
    rewards = referral_service.reward_history(user)

    return jsonify(
        referral_code=code,
        referral_url=f"{current_app.config['FRONTEND_URL']}/?ref={code}",
        completed_referral_count=referral_service.completed_referral_count(user.id),
        rewards=[
            {
                "reward_type": r.reward_type,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "applied_at": r.applied_at.isoformat() if r.applied_at else None,
            }
            for r in rewards
        ],
    )
