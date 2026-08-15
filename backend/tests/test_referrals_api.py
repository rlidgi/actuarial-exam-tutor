from app.models import ReferralReward, User


def test_summary_requires_auth(client):
    resp = client.get("/api/referrals")
    assert resp.status_code == 401


def test_summary_returns_a_fresh_code_and_empty_history(client, register_user):
    resp_json = register_user("freshreferrer@example.com")
    headers = {"Authorization": f"Bearer {resp_json['access_token']}"}

    resp = client.get("/api/referrals", headers=headers)

    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body["referral_code"]) == 8
    assert body["referral_code"] in body["referral_url"]
    assert body["completed_referral_count"] == 0
    assert body["rewards"] == []


def test_summary_code_is_stable_across_calls(client, register_user):
    resp_json = register_user("stablereferrer@example.com")
    headers = {"Authorization": f"Bearer {resp_json['access_token']}"}

    first = client.get("/api/referrals", headers=headers).get_json()
    second = client.get("/api/referrals", headers=headers).get_json()

    assert first["referral_code"] == second["referral_code"]


def test_summary_includes_reward_history(client, db, register_user):
    resp_json = register_user("historyreferrer@example.com")
    headers = {"Authorization": f"Bearer {resp_json['access_token']}"}
    user = User.query.filter_by(email="historyreferrer@example.com").first()

    db.session.add(
        ReferralReward(
            user_id=user.id, reward_type="referrer_credit", status="applied",
            stripe_coupon_id="coupon_10off",
        )
    )
    db.session.commit()

    resp = client.get("/api/referrals", headers=headers)

    body = resp.get_json()
    assert len(body["rewards"]) == 1
    assert body["rewards"][0]["reward_type"] == "referrer_credit"
    assert body["rewards"][0]["status"] == "applied"
