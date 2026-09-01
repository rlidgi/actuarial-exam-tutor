from unittest.mock import MagicMock, patch

from app.models import Exam, ReferralReward, StudentProfile, Subscription, User
from app.services import referral_service


def _register_with_profile(client, db, register_user, email):
    resp_json = register_user(email)
    headers = {"Authorization": f"Bearer {resp_json['access_token']}"}

    exam = Exam.query.filter_by(code="P").first()
    if exam is None:
        exam = Exam(code="P", name="Exam P")
        db.session.add(exam)
        db.session.commit()

    client.post("/api/students/profiles", json={"exam_code": "P"}, headers=headers)
    return headers


def test_checkout_requires_auth(client):
    resp = client.post("/api/billing/checkout", json={"exam_code": "P"})
    assert resp.status_code == 401


def test_checkout_without_configured_price_returns_400(client, db, app, register_user):
    headers = _register_with_profile(client, db, register_user, "checkoutnoprice@example.com")
    app.config["STRIPE_PRICE_IDS"]["P"] = ""

    resp = client.post("/api/billing/checkout", json={"exam_code": "P"}, headers=headers)

    assert resp.status_code == 400


def test_checkout_returns_stripe_url(client, db, app, register_user):
    headers = _register_with_profile(client, db, register_user, "checkoutok@example.com")
    app.config["STRIPE_PRICE_IDS"]["P"] = "price_test123"

    with patch("app.services.billing_service.stripe") as mock_stripe:
        mock_stripe.checkout.Session.create.return_value = MagicMock(
            url="https://checkout.stripe.com/test-session"
        )
        resp = client.post("/api/billing/checkout", json={"exam_code": "P"}, headers=headers)

    assert resp.status_code == 200
    assert resp.get_json()["url"] == "https://checkout.stripe.com/test-session"
    create_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
    assert create_kwargs["line_items"] == [{"price": "price_test123", "quantity": 1}]
    assert create_kwargs["mode"] == "subscription"
    assert "discounts" not in create_kwargs


def test_checkout_includes_referral_discount_for_referred_user(client, db, app, register_user):
    _register_with_profile(client, db, register_user, "checkoutreferrer@example.com")
    referrer = User.query.filter_by(email="checkoutreferrer@example.com").first()
    code = referral_service.get_or_create_referral_code(referrer)

    resp_json = register_user("checkoutreferred@example.com", referral_code=code)
    headers = {"Authorization": f"Bearer {resp_json['access_token']}"}
    client.post("/api/students/profiles", json={"exam_code": "P"}, headers=headers)

    app.config["STRIPE_PRICE_IDS"]["P"] = "price_test123"
    app.config["STRIPE_COUPON_REFERRED_25_OFF"] = "coupon_referred25"

    with patch("app.services.billing_service.stripe") as mock_stripe:
        mock_stripe.checkout.Session.create.return_value = MagicMock(
            url="https://checkout.stripe.com/test-session"
        )
        resp = client.post("/api/billing/checkout", json={"exam_code": "P"}, headers=headers)

    assert resp.status_code == 200
    create_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
    assert create_kwargs["discounts"] == [{"coupon": "coupon_referred25"}]


def test_checkout_grants_free_trial_for_an_eligible_email(client, db, app, register_user):
    headers = _register_with_profile(client, db, register_user, "president@university.edu")
    app.config["STRIPE_PRICE_IDS"]["P"] = "price_test123"
    app.config["TRIAL_ELIGIBLE_EMAILS"] = {"president@university.edu"}
    app.config["TRIAL_PERIOD_DAYS"] = 14

    with patch("app.services.billing_service.stripe") as mock_stripe:
        mock_stripe.checkout.Session.create.return_value = MagicMock(
            url="https://checkout.stripe.com/test-session"
        )
        resp = client.post("/api/billing/checkout", json={"exam_code": "P"}, headers=headers)

    assert resp.status_code == 200
    create_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
    assert create_kwargs["subscription_data"]["trial_period_days"] == 14
    assert create_kwargs["payment_method_collection"] == "if_required"


def test_checkout_ignores_trial_eligibility_for_a_different_email(client, db, app, register_user):
    headers = _register_with_profile(client, db, register_user, "notpresident@example.com")
    app.config["STRIPE_PRICE_IDS"]["P"] = "price_test123"
    app.config["TRIAL_ELIGIBLE_EMAILS"] = {"president@university.edu"}

    with patch("app.services.billing_service.stripe") as mock_stripe:
        mock_stripe.checkout.Session.create.return_value = MagicMock(
            url="https://checkout.stripe.com/test-session"
        )
        resp = client.post("/api/billing/checkout", json={"exam_code": "P"}, headers=headers)

    assert resp.status_code == 200
    create_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
    assert "trial_period_days" not in create_kwargs["subscription_data"]
    assert "payment_method_collection" not in create_kwargs


def test_checkout_does_not_grant_a_second_trial_after_has_ever_subscribed(
    client, db, app, register_user
):
    headers = _register_with_profile(client, db, register_user, "president2@university.edu")
    user = User.query.filter_by(email="president2@university.edu").first()
    user.has_ever_subscribed = True
    db.session.commit()

    app.config["STRIPE_PRICE_IDS"]["P"] = "price_test123"
    app.config["TRIAL_ELIGIBLE_EMAILS"] = {"president2@university.edu"}

    with patch("app.services.billing_service.stripe") as mock_stripe:
        mock_stripe.checkout.Session.create.return_value = MagicMock(
            url="https://checkout.stripe.com/test-session"
        )
        resp = client.post("/api/billing/checkout", json={"exam_code": "P"}, headers=headers)

    assert resp.status_code == 200
    create_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
    assert "trial_period_days" not in create_kwargs["subscription_data"]
    assert "payment_method_collection" not in create_kwargs


def test_portal_without_existing_customer_returns_400(client, db, register_user):
    headers = _register_with_profile(client, db, register_user, "portalnocustomer@example.com")

    resp = client.post("/api/billing/portal", json={"exam_code": "P"}, headers=headers)

    assert resp.status_code == 400


def test_portal_returns_stripe_url(client, db, register_user):
    headers = _register_with_profile(client, db, register_user, "portalok@example.com")
    user = User.query.filter_by(email="portalok@example.com").first()
    profile = StudentProfile.query.filter_by(user_id=user.id).first()
    db.session.add(
        Subscription(
            student_profile_id=profile.id, status="active", stripe_customer_id="cus_test123"
        )
    )
    db.session.commit()

    with patch("app.services.billing_service.stripe") as mock_stripe:
        mock_stripe.billing_portal.Session.create.return_value = MagicMock(
            url="https://billing.stripe.com/test-portal"
        )
        resp = client.post("/api/billing/portal", json={"exam_code": "P"}, headers=headers)

    assert resp.status_code == 200
    assert resp.get_json()["url"] == "https://billing.stripe.com/test-portal"
    mock_stripe.billing_portal.Session.create.assert_called_once_with(
        customer="cus_test123", return_url="http://localhost:3000/chat"
    )


def test_status_reflects_free_trial_by_default(client, db, register_user):
    headers = _register_with_profile(client, db, register_user, "statusdefault@example.com")

    resp = client.get("/api/billing/status?exam=P", headers=headers)

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["subscribed"] is False
    assert body["free_turns_remaining"] == 6
    assert body["free_trial_total"] == 6


def test_sync_upserts_subscription_from_checkout_session(client, db, register_user):
    headers = _register_with_profile(client, db, register_user, "syncme@example.com")
    user = User.query.filter_by(email="syncme@example.com").first()
    profile = StudentProfile.query.filter_by(user_id=user.id).first()

    fake_checkout_session = MagicMock(
        metadata=MagicMock(student_profile_id=str(profile.id)),
        subscription="sub_test123",
        customer="cus_test123",
    )
    fake_subscription = MagicMock()
    fake_subscription.__getitem__.side_effect = lambda k: {"status": "active"}[k]
    fake_subscription.items.data = []

    with patch("app.services.billing_service.stripe") as mock_stripe:
        mock_stripe.checkout.Session.retrieve.return_value = fake_checkout_session
        mock_stripe.Subscription.retrieve.return_value = fake_subscription

        resp = client.post(
            "/api/billing/sync", json={"session_id": "cs_test123"}, headers=headers
        )

    assert resp.status_code == 200
    sub = Subscription.query.filter_by(student_profile_id=profile.id).first()
    assert sub is not None
    assert sub.status == "active"
    assert sub.stripe_customer_id == "cus_test123"
    assert sub.stripe_subscription_id == "sub_test123"


def _register_referred_pair(client, db, app, register_user, *, referrer_email, referred_email):
    """Registers a referrer who already has a Stripe customer id, plus a
    referred user with a profile, ready for a checkout sync/webhook to
    activate. The referrer's existing customer id doesn't change when their
    reward gets applied any more (see apply_pending_rewards_for_customer) --
    it's kept here mainly so tests can distinguish "referrer with a
    subscription" from "referrer who's never subscribed"."""
    _register_with_profile(client, db, register_user, referrer_email)
    referrer = User.query.filter_by(email=referrer_email).first()
    referrer_profile = StudentProfile.query.filter_by(user_id=referrer.id).first()
    db.session.add(
        Subscription(
            student_profile_id=referrer_profile.id,
            status="active",
            stripe_customer_id="cus_referrer_active",
        )
    )
    db.session.commit()
    code = referral_service.get_or_create_referral_code(referrer)

    resp_json = register_user(referred_email, referral_code=code)
    headers = {"Authorization": f"Bearer {resp_json['access_token']}"}
    client.post("/api/students/profiles", json={"exam_code": "P"}, headers=headers)
    referred_user = User.query.filter_by(email=referred_email).first()
    referred_profile = StudentProfile.query.filter_by(user_id=referred_user.id).first()
    return headers, referred_user, referred_profile


def test_sync_activation_grants_a_pending_referrer_reward(client, db, app, register_user):
    headers, referred_user, referred_profile = _register_referred_pair(
        client, db, app, register_user,
        referrer_email="syncreferrer@example.com", referred_email="syncreferred@example.com",
    )
    app.config["REFERRAL_CREDIT_CENTS"] = 1000

    fake_checkout_session = MagicMock(
        metadata=MagicMock(student_profile_id=str(referred_profile.id)),
        subscription="sub_referred1",
        customer="cus_referred1",
    )
    fake_subscription = MagicMock()
    fake_subscription.__getitem__.side_effect = lambda k: {"status": "active"}[k]
    fake_subscription.items.data = []

    with patch("app.services.billing_service.stripe") as mock_stripe, \
         patch("app.services.referral_service.stripe") as mock_referral_stripe:
        mock_stripe.checkout.Session.retrieve.return_value = fake_checkout_session
        mock_stripe.Subscription.retrieve.return_value = fake_subscription
        resp = client.post(
            "/api/billing/sync", json={"session_id": "cs_referred1"}, headers=headers
        )

    assert resp.status_code == 200
    db.session.refresh(referred_user)
    assert referred_user.has_ever_subscribed is True
    reward = ReferralReward.query.filter_by(referred_user_id=referred_user.id).first()
    assert reward is not None
    assert reward.status == "pending"
    # Not applied at activation time any more -- see
    # apply_pending_rewards_for_customer, fired later from invoice.upcoming.
    mock_referral_stripe.Customer.create_balance_transaction.assert_not_called()


def test_webhook_and_sync_race_produces_one_referrer_reward(client, db, app, register_user):
    headers, referred_user, referred_profile = _register_referred_pair(
        client, db, app, register_user,
        referrer_email="racereferrer@example.com", referred_email="racereferred@example.com",
    )
    app.config["REFERRAL_CREDIT_CENTS"] = 1000

    fake_checkout_session = MagicMock(
        metadata=MagicMock(student_profile_id=str(referred_profile.id)),
        subscription="sub_referred_race",
        customer="cus_referred_race",
    )
    fake_subscription = MagicMock()
    fake_subscription.__getitem__.side_effect = lambda k: {"status": "active"}[k]
    fake_subscription.items.data = []

    with patch("app.services.billing_service.stripe") as mock_stripe, \
         patch("app.services.referral_service.stripe") as mock_referral_stripe:
        mock_stripe.checkout.Session.retrieve.return_value = fake_checkout_session
        mock_stripe.Subscription.retrieve.return_value = fake_subscription

        # The success-page sync lands first...
        sync_resp = client.post(
            "/api/billing/sync", json={"session_id": "cs_referred_race"}, headers=headers
        )

        # ...and the webhook for the same checkout arrives shortly after.
        mock_stripe.Webhook.construct_event.return_value = {
            "type": "checkout.session.completed",
            "data": {"object": fake_checkout_session},
        }
        webhook_resp = client.post(
            "/api/billing/webhook",
            data=b"{}",
            headers={"Stripe-Signature": "sig", "Content-Type": "application/json"},
        )

    assert sync_resp.status_code == 200
    assert webhook_resp.status_code == 200
    assert ReferralReward.query.filter_by(referred_user_id=referred_user.id).count() == 1
    mock_referral_stripe.Customer.create_balance_transaction.assert_not_called()


def test_webhook_invalid_signature_returns_400(client):
    resp = client.post(
        "/api/billing/webhook",
        data=b"{}",
        headers={"Stripe-Signature": "bad-sig", "Content-Type": "application/json"},
    )
    assert resp.status_code == 400


def test_webhook_subscription_deleted_marks_canceled(client, db, register_user):
    _register_with_profile(client, db, register_user, "webhookuser@example.com")
    user = User.query.filter_by(email="webhookuser@example.com").first()
    profile = StudentProfile.query.filter_by(user_id=user.id).first()
    db.session.add(
        Subscription(
            student_profile_id=profile.id, status="active", stripe_subscription_id="sub_test456"
        )
    )
    db.session.commit()

    with patch("app.services.billing_service.stripe") as mock_stripe:
        mock_stripe.Webhook.construct_event.return_value = {
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_test456"}},
        }
        resp = client.post(
            "/api/billing/webhook",
            data=b"{}",
            headers={"Stripe-Signature": "sig", "Content-Type": "application/json"},
        )

    assert resp.status_code == 200
    sub = Subscription.query.filter_by(stripe_subscription_id="sub_test456").first()
    assert sub.status == "canceled"


def test_webhook_invoice_upcoming_applies_pending_referrer_reward(client, db, app, register_user):
    _register_with_profile(client, db, register_user, "upcomingwebhookuser@example.com")
    referrer = User.query.filter_by(email="upcomingwebhookuser@example.com").first()
    profile = StudentProfile.query.filter_by(user_id=referrer.id).first()
    db.session.add(
        Subscription(
            student_profile_id=profile.id, status="active", stripe_customer_id="cus_webhook_up1"
        )
    )
    db.session.add(
        ReferralReward(
            user_id=referrer.id, reward_type="referrer_credit", status="pending",
            stripe_coupon_id="coupon_x",
        )
    )
    db.session.commit()
    app.config["REFERRAL_CREDIT_CENTS"] = 1000

    with patch("app.services.billing_service.stripe") as mock_stripe, \
         patch("app.services.referral_service.stripe") as mock_referral_stripe:
        mock_stripe.Webhook.construct_event.return_value = {
            "type": "invoice.upcoming",
            "data": {"object": {"customer": "cus_webhook_up1"}},
        }
        resp = client.post(
            "/api/billing/webhook",
            data=b"{}",
            headers={"Stripe-Signature": "sig", "Content-Type": "application/json"},
        )

    assert resp.status_code == 200
    mock_referral_stripe.Customer.create_balance_transaction.assert_called_once_with(
        "cus_webhook_up1", amount=-1000, currency="usd", description="Referral reward"
    )
    reward = ReferralReward.query.filter_by(user_id=referrer.id).first()
    assert reward.status == "applied"
    assert reward.applied_at is not None
