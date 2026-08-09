from flask import Flask

from app.config import Config
from app.extensions import db, migrate, jwt, cors
from app.logging_config import configure_logging


def create_app(config_object: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    configure_logging(app)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config["CORS_ORIGINS"])

    from app import models  # noqa: F401  (ensures models are registered with SQLAlchemy)

    from app.api import register_blueprints

    register_blueprints(app)

    return app
