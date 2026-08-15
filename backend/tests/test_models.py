import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Exam, ReferralReward, StudentProfile, Topic, User


def test_student_profile_unique_per_exam(app, db):
    user = User(email="a@example.com", external_auth_id="ext-a")
    exam = Exam(code="P", name="Exam P")
    db.session.add_all([user, exam])
    db.session.commit()

    db.session.add(StudentProfile(user_id=user.id, exam_id=exam.id))
    db.session.commit()

    assert StudentProfile.query.count() == 1


def test_topic_belongs_to_exam(app, db):
    exam = Exam(code="FM", name="Exam FM")
    db.session.add(exam)
    db.session.commit()

    topic = Topic(exam_id=exam.id, name="Annuities")
    db.session.add(topic)
    db.session.commit()

    assert topic.exam.code == "FM"


def test_referral_reward_referred_user_id_is_unique(app, db):
    referrer = User(email="referrer@example.com", external_auth_id=str(uuid.uuid4()))
    referred = User(email="referred@example.com", external_auth_id=str(uuid.uuid4()))
    db.session.add_all([referrer, referred])
    db.session.commit()

    db.session.add(
        ReferralReward(
            user_id=referrer.id,
            referred_user_id=referred.id,
            reward_type="referrer_percent_off",
            status="pending",
        )
    )
    db.session.commit()

    db.session.add(
        ReferralReward(
            user_id=referrer.id,
            referred_user_id=referred.id,
            reward_type="referrer_percent_off",
            status="pending",
        )
    )
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_referral_reward_allows_multiple_null_referred_user_ids(app, db):
    user = User(email="selfreward@example.com", external_auth_id=str(uuid.uuid4()))
    db.session.add(user)
    db.session.commit()

    db.session.add_all(
        [
            ReferralReward(user_id=user.id, reward_type="referred_percent_off", status="pending"),
            ReferralReward(user_id=user.id, reward_type="referred_percent_off", status="applied"),
        ]
    )
    db.session.commit()

    assert ReferralReward.query.filter_by(user_id=user.id).count() == 2
