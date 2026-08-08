import time
import uuid

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from jwt import PyJWKClient
from jwt.algorithms import ECAlgorithm

from app import create_app
from app.config import TestingConfig
from app.extensions import db as _db

SUPABASE_TEST_ISSUER = "https://test.supabase.co/auth/v1"
SUPABASE_TEST_AUDIENCE = "authenticated"
SUPABASE_TEST_KID = "test-key-1"


@pytest.fixture()
def app():
    application = create_app(TestingConfig)
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def supabase_tokens(monkeypatch):
    """Generates a real EC keypair, serves it as a JWKS document in place
    of a network call, and hands back a helper that mints tokens signed
    with the matching private key -- so /api/auth/exchange's actual
    verification code (signature, issuer, audience, expiry) runs for
    real against every test that uses it, nothing about verification
    is mocked.
    """
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_jwk = ECAlgorithm.to_jwk(private_key.public_key(), as_dict=True)
    public_jwk.update(kid=SUPABASE_TEST_KID, use="sig", alg="ES256")
    jwks = {"keys": [public_jwk]}
    monkeypatch.setattr(PyJWKClient, "fetch_data", lambda self: jwks)

    def make_token(*, key=private_key, kid=SUPABASE_TEST_KID, **claim_overrides):
        now = int(time.time())
        claims = {
            "sub": str(uuid.uuid4()),
            "email": "student@example.com",
            "aud": SUPABASE_TEST_AUDIENCE,
            "iss": SUPABASE_TEST_ISSUER,
            "iat": now,
            "exp": now + 3600,
            **claim_overrides,
        }
        return jwt.encode(claims, key, algorithm="ES256", headers={"kid": kid})

    return make_token


@pytest.fixture()
def register_user(client, supabase_tokens):
    """Signs a user in through the real /api/auth/exchange endpoint --
    the test-suite's stand-in for "a user is signed in", replacing the
    old direct /api/auth/register calls from the password-auth flow.
    Returns the exchange endpoint's JSON response.
    """
    def _register(email, external_id=None):
        token = supabase_tokens(sub=external_id or str(uuid.uuid4()), email=email)
        resp = client.post("/api/auth/exchange", json={"supabase_access_token": token})
        return resp.get_json()

    return _register
