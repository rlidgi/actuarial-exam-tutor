from flask import Flask


def register_blueprints(app: Flask) -> None:
    from app.api.auth import bp as auth_bp
    from app.api.students import bp as students_bp
    from app.api.chat import bp as chat_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(students_bp, url_prefix="/api/students")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
