import uuid
from unittest.mock import patch

import pytest

from app.models import Exam, ReferralReward, StudentProfile, Subscription, User
from app.services import referral_service


def _make_user(db, email, *, referred_by_id=None, has_ever_subscribed=False):
    user = User(
        external_auth_id=str(uuid.uuid4()),
        email=email,
        referred_by_id=referred_by_id,
        has_ever_subscribed=has_ever_subscribed,
    )
    db.session.add(user)
    db.session.commit()
    return user


def _make_active_subscription(db, user, *, stripe_subscription_id):
    exam = Exam.query.filter_by(code="P").first()
    if exam is None:
        exam = Exam(code="P", name="Exam P")
        db.session.add(exam)
        db.session.commit()
    profile = StudentProfile(user_id=user.id, exam_id=exam.id)
    db.session.add(profile)
    db.session.commit()
    db.session.add(
        Subscription(
            student_profile_id=profile.id,
            status="active",
            stripe_subscription_id=stripe_subscription_id,
        )
    )
    db.session.commit()
    return profile


def test_get_or_create_referral_code_is_idempotent(db):
    user = _make_user(db, "coder@example.com")

    first = referral_service.get_or_create_referral_code(user)
    second = referral_service.get_or_create_referral_code(user)

    assert first == second
    assert len(first) == 8


def test_attach_referrer_sets_referred_by_id_for_a_valid_code(db):
    referrer = _make_user(db, "referrer@example.com")
    code = referral_service.get_or_create_referral_code(referrer)
    new_user = _make_user(db, "newuser@example.com")

    referral_service.attach_referrer(new_user, code)

    assert new_user.referred_by_id == referrer.id


def test_attach_referrer_noops_on_unknown_or_empty_code(db):
    new_user = _make_user(db, "newuser2@example.com")

    referral_service.attach_referrer(new_user, "NOTAREALCODE")
    referral_service.attach_referrer(new_user, None)

    assert new_user.referred_by_id is None


def test_attach_referrer_blocks_self_referral(db):
    user = _make_user(db, "selfref@example.com")
    code = referral_service.get_or_create_referral_code(user)

    referral_service.attach_referrer(user, code)

    assert user.referred_by_id is None


def test_completed_referral_count_only_counts_converted_referrals(db):
    referrer = _make_user(db, "counter@example.com")
    _make_user(db, "converted1@example.com", referred_by_id=referrer.id, has_ever_subscribed=True)
    _make_user(db, "converted2@example.com", referred_by_id=referrer.id, has_ever_subscribed=True)
    _make_user(db, "notconverted@example.com", referred_by_id=referrer.id, has_ever_subscribed=False)

    assert referral_service.completed_referral_count(referrer.id) == 2


@pytest.mark.parametrize(
    "position,expected",
    [
        (1, "referrer_percent_off"),
        (2, "referrer_percent_off"),
        (3, "referrer_free_month"),
        (4, "referrer_percent_off"),
        (5, "referrer_percent_off"),
        (6, "referrer_free_month"),
        (7, "referrer_percent_off"),
        (8, "referrer_percent_off"),
        (9, "referrer_free_month"),
    ],
)
def test_reward_type_for_position(position, expected):
    assert referral_service._reward_type_for_position(position, interval=3) == expected


def test_grant_referrer_reward_applies_immediately_with_an_active_subscription(app, db):
    referrer = _make_user(db, "activereferrer@example.com")
    _make_active_subscription(db, referrer, stripe_subscription_id="sub_ref123")
    referred_user = _make_user(
        db, "referred1@example.com", referred_by_id=referrer.id, has_ever_subscribed=True
    )
    app.config["STRIPE_COUPON_REFERRER_25_OFF"] = "coupon_25off"

    with patch("app.services.referral_service.stripe") as mock_stripe:
        referral_service.grant_referrer_reward(referrer, referred_user)

    reward = ReferralReward.query.filter_by(referred_user_id=referred_user.id).first()
    assert reward is not None
    assert reward.status == "applied"
    assert reward.reward_type == "referrer_percent_off"
    assert reward.applied_at is not None
    mock_stripe.Subscription.modify.assert_called_once_with(
        "sub_ref123", discounts=[{"coupon": "coupon_25off"}]
    )


def test_grant_referrer_reward_hits_the_free_month_milestone(app, db):
    referrer = _make_user(db, "milestonereferrer@example.com")
    _make_active_subscription(db, referrer, stripe_subscription_id="sub_ref456")
    # Two already-converted referrals -- the third makes this the milestone.
    _make_user(db, "already1@example.com", referred_by_id=referrer.id, has_ever_subscribed=True)
    _make_user(db, "already2@example.com", referred_by_id=referrer.id, has_ever_subscribed=True)
    referred_user = _make_user(
        db, "referred3rd@example.com", referred_by_id=referrer.id, has_ever_subscribed=True
    )
    app.config["STRIPE_COUPON_REFERRER_FREE_MONTH"] = "coupon_freemonth"

    with patch("app.services.referral_service.stripe"):
        referral_service.grant_referrer_reward(referrer, referred_user)

    reward = ReferralReward.query.filter_by(referred_user_id=referred_user.id).first()
    assert reward.reward_type == "referrer_free_month"
    assert reward.stripe_coupon_id == "coupon_freemonth"


def test_grant_referrer_reward_stays_pending_without_an_active_subscription(db):
    referrer = _make_user(db, "noactivesub@example.com")
    referred_user = _make_user(
        db, "referred2@example.com", referred_by_id=referrer.id, has_ever_subscribed=True
    )

    with patch("app.services.referral_service.stripe") as mock_stripe:
        referral_service.grant_referrer_reward(referrer, referred_user)

    reward = ReferralReward.query.filter_by(referred_user_id=referred_user.id).first()
    assert reward is not None
    assert reward.status == "pending"
    mock_stripe.Subscription.modify.assert_not_called()


def test_grant_referrer_reward_is_idempotent_for_the_same_referred_user(db):
    referrer = _make_user(db, "idempotentreferrer@example.com")
    referred_user = _make_user(
        db, "referred3@example.com", referred_by_id=referrer.id, has_ever_subscribed=True
    )

    with patch("app.services.referral_service.stripe"):
        referral_service.grant_referrer_reward(referrer, referred_user)
        referral_service.grant_referrer_reward(referrer, referred_user)

    assert ReferralReward.query.filter_by(referred_user_id=referred_user.id).count() == 1


def test_record_referred_user_pending_reward_creates_a_pending_row(app, db):
    referrer = _make_user(db, "recordreferrer@example.com")
    user = _make_user(db, "recorduser@example.com", referred_by_id=referrer.id)
    app.config["STRIPE_COUPON_REFERRED_25_OFF"] = "coupon_referred"

    referral_service.record_referred_user_pending_reward(user)

    reward = ReferralReward.query.filter_by(
        user_id=user.id, reward_type="referred_percent_off"
    ).first()
    assert reward is not None
    assert reward.status == "pending"
    assert reward.stripe_coupon_id == "coupon_referred"


def test_record_referred_user_pending_reward_is_idempotent_on_retry(db):
    referrer = _make_user(db, "retryreferrer@example.com")
    user = _make_user(db, "retryuser@example.com", referred_by_id=referrer.id)

    referral_service.record_referred_user_pending_reward(user)
    referral_service.record_referred_user_pending_reward(user)

    assert (
        ReferralReward.query.filter_by(user_id=user.id, reward_type="referred_percent_off").count()
        == 1
    )


def test_record_referred_user_pending_reward_noops_without_a_referrer(db):
    user = _make_user(db, "noreferreruser@example.com")

    referral_service.record_referred_user_pending_reward(user)

    assert ReferralReward.query.filter_by(user_id=user.id).count() == 0


def test_pending_reward_for_checkout_prioritizes_referred_discount(db):
    user = _make_user(db, "prioritizeuser@example.com")
    db.session.add(
        ReferralReward(
            user_id=user.id, reward_type="referrer_percent_off", status="pending", stripe_coupon_id="c1"
        )
    )
    db.session.commit()
    db.session.add(
        ReferralReward(
            user_id=user.id, reward_type="referred_percent_off", status="pending", stripe_coupon_id="c2"
        )
    )
    db.session.commit()

    reward = referral_service.pending_reward_for_checkout(user)

    assert reward.reward_type == "referred_percent_off"


def test_handle_first_ever_activation_flips_flag_and_grants_reward_once(app, db):
    referrer = _make_user(db, "firstactivationreferrer@example.com")
    referred_user = _make_user(
        db, "firstactivationreferred@example.com", referred_by_id=referrer.id
    )
    app.config["STRIPE_COUPON_REFERRER_25_OFF"] = "coupon_x"

    with patch("app.services.referral_service.stripe"):
        referral_service.handle_first_ever_activation(referred_user.id)

    db.session.refresh(referred_user)
    assert referred_user.has_ever_subscribed is True
    assert ReferralReward.query.filter_by(referred_user_id=referred_user.id).count() == 1

    # Simulate the webhook+/sync race: calling it again must be a no-op.
    with patch("app.services.referral_service.stripe") as mock_stripe_second:
        referral_service.handle_first_ever_activation(referred_user.id)

    assert ReferralReward.query.filter_by(referred_user_id=referred_user.id).count() == 1
    mock_stripe_second.Subscription.modify.assert_not_called()


def test_handle_first_ever_activation_marks_referred_user_reward_applied(db):
    referrer = _make_user(db, "referredrewardreferrer@example.com")
    referred_user = _make_user(db, "referredrewarduser@example.com", referred_by_id=referrer.id)
    db.session.add(
        ReferralReward(
            user_id=referred_user.id,
            reward_type="referred_percent_off",
            status="pending",
            stripe_coupon_id="coupon_referred25",
        )
    )
    db.session.commit()

    with patch("app.services.referral_service.stripe"):
        referral_service.handle_first_ever_activation(referred_user.id)

    reward = ReferralReward.query.filter_by(
        user_id=referred_user.id, reward_type="referred_percent_off"
    ).first()
    assert reward.status == "applied"
    assert reward.applied_at is not None
