from datetime import datetime, timezone

from app.extensions import db


class Mastery(db.Model):
    __tablename__ = "mastery"

    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(
        db.Integer, db.ForeignKey("student_profiles.id"), nullable=False
    )
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id"), nullable=False)
    mastery_score = db.Column(db.Integer, nullable=False, default=0)  # 0-100
    confidence = db.Column(db.Float, nullable=True)  # 0-1, from the LLM's last assessment
    last_reviewed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    student_profile = db.relationship("StudentProfile", back_populates="mastery_records")
    topic = db.relationship("Topic")

    __table_args__ = (
        db.UniqueConstraint(
            "student_profile_id", "topic_id", name="uq_mastery_student_topic"
        ),
        db.CheckConstraint("mastery_score >= 0 AND mastery_score <= 100", name="ck_mastery_range"),
    )
