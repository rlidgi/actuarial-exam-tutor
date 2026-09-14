import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev")
    # Flask-JWT-Extended's default is 15 minutes, too short for a study
    # session. No refresh-token flow yet, so this is the session lifetime.
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/actuarial_tutor"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Identity verification only (see app/services/supabase_auth_service.py)
    # -- the backend fetches Supabase's public JWKS to verify tokens minted
    # by the frontend's supabase-js client. No Supabase API key is held
    # here; this is the only Supabase Auth config the backend needs.
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_JWT_AUD = os.environ.get("SUPABASE_JWT_AUD", "authenticated")
    SUPABASE_JWT_ISSUER = os.environ.get("SUPABASE_JWT_ISSUER", f"{SUPABASE_URL}/auth/v1")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    # Tracing (see app/services/tutor_service.py). Optional -- if either key
    # is unset, tracing is constructed disabled and every call is a no-op,
    # so the app runs fine without a Langfuse account.
    LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY", "")
    LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")
    # Live transcription of a student's uploaded problem screenshot (see
    # app/services/vision_service.py). Defaults to the same cheap tier
    # already used for auto-summarize -- transcription doesn't need sol's
    # heavier reasoning, just accurate reading of the image.
    VISION_MODEL = os.environ.get("VISION_MODEL", "gpt-5.6-luna")
    # Billing (see app/services/billing_service.py, app/services/
    # entitlement_service.py). Access is sold per exam, so each exam has
    # its own Stripe price id; FM/FAM are unused until those exams exist,
    # but wired up now since there's no reason to defer it.
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PRICE_IDS = {
        "P": os.environ.get("STRIPE_PRICE_ID_P", ""),
        "FM": os.environ.get("STRIPE_PRICE_ID_FM", ""),
        "FAM": os.environ.get("STRIPE_PRICE_ID_FAM", ""),
    }
    FREE_TRIAL_TURNS = int(os.environ.get("FREE_TRIAL_TURNS", "6"))
    # Referral program (see app/services/referral_service.py). A referred
    # user's own first-month discount must be created in the Stripe
    # dashboard with duration=once. Referrer rewards are a flat account
    # credit (REFERRAL_CREDIT_CENTS) applied via a Stripe customer balance
    # transaction once the referrer has a Stripe customer id -- credits are
    # additive, so multiple simultaneous rewards can't clobber each other the
    # way stacking discounts on one subscription would. STRIPE_COUPON_
    # REFERRER_10_OFF (also duration=once, same fixed amount) only covers the
    # one-time case where the referrer earns a reward before ever
    # subscribing themselves -- see grant_referrer_reward.
    STRIPE_COUPON_REFERRED_25_OFF = os.environ.get("STRIPE_COUPON_REFERRED_25_OFF", "")
    STRIPE_COUPON_REFERRER_10_OFF = os.environ.get("STRIPE_COUPON_REFERRER_10_OFF", "")
    REFERRAL_CREDIT_CENTS = int(os.environ.get("REFERRAL_CREDIT_CENTS", "1000"))
    # Partner vanity referral codes (see referral_service.py's partner_terms_for
    # helper) -- a specific institution's own referral_code gets its own
    # discount/credit terms instead of the standard 25%/$10 above, everything
    # else about the referral pipeline (attach_referrer, ReferralReward rows,
    # the /account "Total earned" stat, payout-by-request) stays identical.
    # Keyed by the partner's User.referral_code (set directly in the DB once
    # their real account exists -- see referral_service.py's module docstring
    # for why it can't be pre-created).
    PARTNER_REFERRAL_CODES = {
        "PENNSTATE": {
            "referred_discount_coupon": os.environ.get(
                "STRIPE_COUPON_PENNSTATE_REFERRED_15_OFF", ""
            ),
            "referrer_credit_coupon": os.environ.get(
                "STRIPE_COUPON_PENNSTATE_REFERRER_5_OFF", ""
            ),
            "referrer_credit_cents": 500,
        },
    }
    # Promotional free trial for a short, hand-picked outreach list (e.g.
    # university actuarial club presidents) -- see
    # billing_service.create_checkout_session. Tied to the signed-in user's
    # own verified account email (never client-supplied), not a shareable
    # link or code, so forwarding the offer to someone else doesn't extend
    # it to them.
    TRIAL_ELIGIBLE_EMAILS = {
        e.strip().lower()
        for e in os.environ.get("TRIAL_ELIGIBLE_EMAILS", "").split(",")
        if e.strip()
    }
    TRIAL_PERIOD_DAYS = int(os.environ.get("TRIAL_PERIOD_DAYS", "14"))
    # Gates the /admin dashboard (see api/admin.py, api/helpers.py's
    # require_admin) -- same env-var-driven set pattern as
    # TRIAL_ELIGIBLE_EMAILS above, checked against the signed-in user's own
    # verified account email.
    ADMIN_EMAILS = {
        e.strip().lower()
        for e in os.environ.get("ADMIN_EMAILS", "").split(",")
        if e.strip()
    }
    # Where Stripe Checkout/portal redirect back to -- the Next.js app, not
    # this API.
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
    # Transactional email (see app/services/email_service.py) via Namecheap
    # Private Email's SMTP relay. SMTP_PASSWORD unset means email sending is
    # silently disabled (logged, not raised) -- same "optional, no-ops when
    # unconfigured" pattern as LANGFUSE_* above, so the app runs fine without
    # mailbox credentials in dev.
    SMTP_HOST = os.environ.get("SMTP_HOST", "mail.privateemail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "admin@actuarialexamstutor.com")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    # Comma-separated list of origins allowed to call this API cross-origin.
    # Defaults to just the frontend's own URL -- set explicitly (e.g. to add
    # a temporary staging hostname during a rollout) via the env var.
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.environ.get("CORS_ORIGINS", "").split(",")
        if origin.strip()
    ] or [FRONTEND_URL]


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
    SUPABASE_URL = "https://test.supabase.co"
    SUPABASE_JWT_ISSUER = "https://test.supabase.co/auth/v1"
