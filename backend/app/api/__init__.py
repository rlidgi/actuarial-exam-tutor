from flask import Flask


def register_blueprints(app: Flask) -> None:
    from app.api.auth import bp as auth_bp
    from app.api.students import bp as students_bp
    from app.api.chat import bp as chat_bp
    from app.api.exams import bp as exams_bp
    from app.api.billing import bp as billing_bp
    from app.api.courses import bp as courses_bp
    from app.api.formulas import bp as formulas_bp
    from app.api.referrals import bp as referrals_bp
    from app.api.contact import bp as contact_bp
    from app.api.feedback import bp as feedback_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(students_bp, url_prefix="/api/students")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(exams_bp, url_prefix="/api/exams")
    app.register_blueprint(billing_bp, url_prefix="/api/billing")
    app.register_blueprint(courses_bp, url_prefix="/api/courses")
    app.register_blueprint(formulas_bp, url_prefix="/api/formulas")
    app.register_blueprint(referrals_bp, url_prefix="/api/referrals")
    app.register_blueprint(contact_bp, url_prefix="/api/contact")
    app.register_blueprint(feedback_bp, url_prefix="/api/feedback")
