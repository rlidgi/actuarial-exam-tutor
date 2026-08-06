from datetime import datetime, timezone

from app.extensions import db


class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    goals = db.Column(db.Text, nullable=True)
    experience_level = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="student_profiles")
    exam = db.relationship("Exam")
    mastery_records = db.relationship(
        "Mastery", back_populates="student_profile", cascade="all, delete-orphan"
    )
    mistakes = db.relationship(
        "Mistake", back_populates="student_profile", cascade="all, delete-orphan"
    )
    sessions = db.relationship(
        "Session", back_populates="student_profile", cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "exam_id", name="uq_student_profile_user_exam"),
    )
