"""Verification of Supabase-issued access tokens.

This is the ONLY place in the backend that knows anything about Supabase
Auth's token format. It never calls the Supabase Auth API (no OAuth/OTP
calls happen here -- the frontend talks to Supabase directly for that) and
never holds a privileged Supabase credential; it only fetches the public
JWKS document and verifies a token's signature/claims against it.
"""
from flask import current_app
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError
import jwt

_jwks_clients: dict[str, PyJWKClient] = {}


class InvalidSupabaseToken(Exception):
    """Raised for any token that fails signature or claim verification."""


def _jwks_client() -> PyJWKClient:
    supabase_url = current_app.config["SUPABASE_URL"]
    # Cached per Supabase URL (there's only ever one per app, but per-URL
    # keeps this correct if tests swap config between apps). PyJWKClient
    # itself caches the fetched keys and matches by `kid`, so this avoids
    # refetching the JWKS document on every request.
    client = _jwks_clients.get(supabase_url)
    if client is None:
        jwks_uri = f"{supabase_url}/auth/v1/.well-known/jwks.json"
        client = _jwks_clients[supabase_url] = PyJWKClient(jwks_uri)
    return client


def verify_access_token(token: str) -> dict:
    """Verify a Supabase access token and return its claims.

    Raises InvalidSupabaseToken on any failure -- expired, wrong issuer/
    audience, bad signature, or an unreachable JWKS endpoint.
    """
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience=current_app.config["SUPABASE_JWT_AUD"],
            issuer=current_app.config["SUPABASE_JWT_ISSUER"],
        )
    except PyJWTError as exc:
        raise InvalidSupabaseToken(str(exc)) from exc
