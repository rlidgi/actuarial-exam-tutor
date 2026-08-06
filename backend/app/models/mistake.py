from app.extensions import db


class Mistake(db.Model):
    __tablename__ = "mistakes"

    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(
        db.Integer, db.ForeignKey("student_profiles.id"), nullable=False
    )
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id"), nullable=False)
    misconception = db.Column(db.Text, nullable=False)
    frequency = db.Column(db.Integer, nullable=False, default=1)
    severity = db.Column(db.String(32), nullable=True)  # e.g. "low" | "medium" | "high"
    resolution_status = db.Column(db.String(32), nullable=False, default="open")

    student_profile = db.relationship("StudentProfile", back_populates="mistakes")
    topic = db.relationship("Topic")
