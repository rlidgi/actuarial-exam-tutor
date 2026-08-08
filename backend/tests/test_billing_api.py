from unittest.mock import MagicMock, patch

from app.models import Exam, StudentProfile, Subscription, User


def _register_with_profile(client, db, email):
    resp = client.post("/api/auth/register", json={"email": email, "password": "secret123"})
    token = resp.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

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


def test_checkout_without_configured_price_returns_400(client, db, app):
    headers = _register_with_profile(client, db, "checkoutnoprice@example.com")
    app.config["STRIPE_PRICE_IDS"]["P"] = ""

    resp = client.post("/api/billing/checkout", json={"exam_code": "P"}, headers=headers)

    assert resp.status_code == 400


def test_checkout_returns_stripe_url(client, db, app):
    headers = _register_with_profile(client, db, "checkoutok@example.com")
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


def test_portal_without_existing_customer_returns_400(client, db):
    headers = _register_with_profile(client, db, "portalnocustomer@example.com")

    resp = client.post("/api/billing/portal", json={"exam_code": "P"}, headers=headers)

    assert resp.status_code == 400


def test_portal_returns_stripe_url(client, db):
    headers = _register_with_profile(client, db, "portalok@example.com")
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


def test_status_reflects_free_trial_by_default(client, db):
    headers = _register_with_profile(client, db, "statusdefault@example.com")

    resp = client.get("/api/billing/status?exam=P", headers=headers)

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["subscribed"] is False
    assert body["free_turns_remaining"] == 6


def test_sync_upserts_subscription_from_checkout_session(client, db):
    headers = _register_with_profile(client, db, "syncme@example.com")
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


def test_webhook_invalid_signature_returns_400(client):
    resp = client.post(
        "/api/billing/webhook",
        data=b"{}",
        headers={"Stripe-Signature": "bad-sig", "Content-Type": "application/json"},
    )
    assert resp.status_code == 400


def test_webhook_subscription_deleted_marks_canceled(client, db):
    _register_with_profile(client, db, "webhookuser@example.com")
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
