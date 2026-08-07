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
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    # Tracing (see app/services/tutor_service.py). Optional -- if either key
    # is unset, tracing is constructed disabled and every call is a no-op,
    # so the app runs fine without a Langfuse account.
    LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY", "")
    LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
