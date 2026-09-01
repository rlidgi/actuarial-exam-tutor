import uuid
from unittest.mock import patch

from app.models import ReferralReward, User
from app.services import referral_service


def _make_user(db, email, *, referred_by_id=None, has_ever_subscribed=False, stripe_customer_id=None):
    user = User(
        external_auth_id=str(uuid.uuid4()),
        email=email,
        referred_by_id=referred_by_id,
        has_ever_subscribed=has_ever_subscribed,
    )
    db.session.add(user)
    db.session.commit()
    if stripe_customer_id:
        _give_stripe_customer(db, user, stripe_customer_id)
    return user


def _give_stripe_customer(db, user, stripe_customer_id):
    """any_stripe_customer_id looks for any Subscription row of this user's
    that recorded a Stripe customer id -- status doesn't matter, only that
    the id was captured at some point (see stripe_utils.any_stripe_customer_id)."""
    from app.models import Exam, StudentProfile, Subscription

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
            student_profile_id=profile.id, status="active", stripe_customer_id=stripe_customer_id
        )
    )
    db.session.commit()


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


def test_grant_referrer_reward_always_stays_pending(app, db):
    """Never applied immediately, even when the referrer already has a
    Stripe customer -- see apply_pending_rewards_for_customer, which is the
    only thing that ever actually calls Stripe for this reward type now."""
    referrer = _make_user(db, "activereferrer@example.com", stripe_customer_id="cus_ref123")
    referred_user = _make_user(
        db, "referred1@example.com", referred_by_id=referrer.id, has_ever_subscribed=True
    )
    app.config["REFERRAL_CREDIT_CENTS"] = 1000

    with patch("app.services.referral_service.stripe") as mock_stripe:
        referral_service.grant_referrer_reward(referrer, referred_user)

    reward = ReferralReward.query.filter_by(referred_user_id=referred_user.id).first()
    assert reward is not None
    assert reward.status == "pending"
    assert reward.reward_type == "referrer_credit"
    assert reward.applied_at is None
    mock_stripe.Customer.create_balance_transaction.assert_not_called()


def test_grant_referrer_reward_creates_one_pending_row_per_referral(db):
    referrer = _make_user(db, "repeatreferrer@example.com", stripe_customer_id="cus_ref999")

    with patch("app.services.referral_service.stripe") as mock_stripe:
        for i in range(3):
            referred = _make_user(
                db, f"repeat{i}@example.com", referred_by_id=referrer.id, has_ever_subscribed=True
            )
            referral_service.grant_referrer_reward(referrer, referred)

    mock_stripe.Customer.create_balance_transaction.assert_not_called()
    rewards = ReferralReward.query.filter_by(
        user_id=referrer.id, reward_type="referrer_credit"
    ).all()
    assert len(rewards) == 3
    assert all(r.status == "pending" for r in rewards)


def test_grant_referrer_reward_stays_pending_without_a_stripe_customer(db):
    referrer = _make_user(db, "noactivesub@example.com")
    referred_user = _make_user(
        db, "referred2@example.com", referred_by_id=referrer.id, has_ever_subscribed=True
    )

    with patch("app.services.referral_service.stripe") as mock_stripe:
        referral_service.grant_referrer_reward(referrer, referred_user)

    reward = ReferralReward.query.filter_by(referred_user_id=referred_user.id).first()
    assert reward is not None
    assert reward.status == "pending"
    mock_stripe.Customer.create_balance_transaction.assert_not_called()


def test_apply_pending_rewards_applies_every_pending_reward_for_the_customer(app, db):
    referrer = _make_user(db, "upcominginvoice@example.com", stripe_customer_id="cus_upcoming1")
    app.config["REFERRAL_CREDIT_CENTS"] = 1000
    for i in range(2):
        referred = _make_user(
            db, f"upcoming{i}@example.com", referred_by_id=referrer.id, has_ever_subscribed=True
        )
        with patch("app.services.referral_service.stripe"):
            referral_service.grant_referrer_reward(referrer, referred)

    with patch("app.services.referral_service.stripe") as mock_stripe:
        referral_service.apply_pending_rewards_for_customer("cus_upcoming1")

    assert mock_stripe.Customer.create_balance_transaction.call_count == 2
    for call in mock_stripe.Customer.create_balance_transaction.call_args_list:
        assert call.args[0] == "cus_upcoming1"
        assert call.kwargs["amount"] == -1000
    rewards = ReferralReward.query.filter_by(
        user_id=referrer.id, reward_type="referrer_credit"
    ).all()
    assert all(r.status == "applied" and r.applied_at is not None for r in rewards)


def test_apply_pending_rewards_skips_rewards_not_still_pending(app, db):
    """Covers the manual Visa/PayPal payout path -- support marks a reward
    something other than "pending" (e.g. "paid_out") to keep this from
    double-paying it once the next invoice.upcoming fires."""
    referrer = _make_user(db, "paidoutreferrer@example.com", stripe_customer_id="cus_paidout1")
    referred = _make_user(
        db, "paidoutreferred@example.com", referred_by_id=referrer.id, has_ever_subscribed=True
    )
    with patch("app.services.referral_service.stripe"):
        referral_service.grant_referrer_reward(referrer, referred)
    reward = ReferralReward.query.filter_by(referred_user_id=referred.id).first()
    reward.status = "paid_out"
    db.session.commit()

    with patch("app.services.referral_service.stripe") as mock_stripe:
        referral_service.apply_pending_rewards_for_customer("cus_paidout1")

    mock_stripe.Customer.create_balance_transaction.assert_not_called()
    db.session.refresh(reward)
    assert reward.status == "paid_out"


def test_apply_pending_rewards_noops_for_an_unknown_customer(db):
    with patch("app.services.referral_service.stripe") as mock_stripe:
        referral_service.apply_pending_rewards_for_customer("cus_doesnotexist")

    mock_stripe.Customer.create_balance_transaction.assert_not_called()


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
            user_id=user.id, reward_type="referrer_credit", status="pending", stripe_coupon_id="c1"
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
    app.config["STRIPE_COUPON_REFERRER_10_OFF"] = "coupon_x"

    with patch("app.services.referral_service.stripe"):
        referral_service.handle_first_ever_activation(referred_user.id)

    db.session.refresh(referred_user)
    assert referred_user.has_ever_subscribed is True
    assert ReferralReward.query.filter_by(referred_user_id=referred_user.id).count() == 1

    # Simulate the webhook+/sync race: calling it again must be a no-op.
    with patch("app.services.referral_service.stripe") as mock_stripe_second:
        referral_service.handle_first_ever_activation(referred_user.id)

    assert ReferralReward.query.filter_by(referred_user_id=referred_user.id).count() == 1
    mock_stripe_second.Customer.create_balance_transaction.assert_not_called()


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
