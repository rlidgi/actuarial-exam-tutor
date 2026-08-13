import time
import uuid

from cryptography.hazmat.primitives.asymmetric import ec

from app.models.user import User


def test_exchange_creates_new_user(client, db, supabase_tokens):
    sub = str(uuid.uuid4())
    token = supabase_tokens(sub=sub, email="student@example.com")

    resp = client.post("/api/auth/exchange", json={"supabase_access_token": token})

    assert resp.status_code == 200
    assert resp.json["access_token"]
    assert resp.json["user"]["email"] == "student@example.com"
    assert resp.json["is_new_user"] is True
    user = db.session.query(User).filter_by(external_auth_id=sub).one()
    assert user.email == "student@example.com"


def test_exchange_reuses_existing_user(client, db, supabase_tokens):
    sub = str(uuid.uuid4())
    first = client.post(
        "/api/auth/exchange",
        json={"supabase_access_token": supabase_tokens(sub=sub, email="student@example.com")},
    )
    second = client.post(
        "/api/auth/exchange",
        json={"supabase_access_token": supabase_tokens(sub=sub, email="student@example.com")},
    )

    assert first.json["user"]["id"] == second.json["user"]["id"]
    assert first.json["is_new_user"] is True
    assert second.json["is_new_user"] is False
    assert db.session.query(User).filter_by(external_auth_id=sub).count() == 1


def test_exchange_syncs_email_change(client, db, supabase_tokens):
    sub = str(uuid.uuid4())
    client.post(
        "/api/auth/exchange",
        json={"supabase_access_token": supabase_tokens(sub=sub, email="old@example.com")},
    )
    resp = client.post(
        "/api/auth/exchange",
        json={"supabase_access_token": supabase_tokens(sub=sub, email="new@example.com")},
    )

    assert resp.status_code == 200
    assert resp.json["user"]["email"] == "new@example.com"
    user = db.session.query(User).filter_by(external_auth_id=sub).one()
    assert user.email == "new@example.com"


def test_exchange_rejects_expired_token(client, supabase_tokens):
    now = int(time.time())
    token = supabase_tokens(iat=now - 7200, exp=now - 3600)

    resp = client.post("/api/auth/exchange", json={"supabase_access_token": token})

    assert resp.status_code == 401


def test_exchange_rejects_wrong_issuer(client, supabase_tokens):
    token = supabase_tokens(iss="https://not-our-project.supabase.co/auth/v1")

    resp = client.post("/api/auth/exchange", json={"supabase_access_token": token})

    assert resp.status_code == 401


def test_exchange_rejects_wrong_audience(client, supabase_tokens):
    token = supabase_tokens(aud="some-other-app")

    resp = client.post("/api/auth/exchange", json={"supabase_access_token": token})

    assert resp.status_code == 401


def test_exchange_rejects_bad_signature(client, supabase_tokens):
    # Signed with a different private key than the one served in the JWKS
    # (but claiming the same kid) -- signature verification must fail.
    forged_key = ec.generate_private_key(ec.SECP256R1())
    token = supabase_tokens(key=forged_key)

    resp = client.post("/api/auth/exchange", json={"supabase_access_token": token})

    assert resp.status_code == 401


def test_exchange_conflicting_email_returns_409(client, supabase_tokens):
    client.post(
        "/api/auth/exchange",
        json={"supabase_access_token": supabase_tokens(email="shared@example.com")},
    )
    resp = client.post(
        "/api/auth/exchange",
        json={"supabase_access_token": supabase_tokens(email="shared@example.com")},
    )

    assert resp.status_code == 409


def test_exchange_requires_token(client):
    resp = client.post("/api/auth/exchange", json={})
    assert resp.status_code == 400
