from app.extensions import db


class Exam(db.Model):
    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True, nullable=False)  # "P", "FM", "FAM"
    name = db.Column(db.String(255), nullable=False)

    topics = db.relationship("Topic", back_populates="exam", cascade="all, delete-orphan")


class Topic(db.Model):
    __tablename__ = "topics"

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    exam = db.relationship("Exam", back_populates="topics")

    prerequisites = db.relationship(
        "TopicPrerequisite",
        foreign_keys="TopicPrerequisite.topic_id",
        back_populates="topic",
        cascade="all, delete-orphan",
    )

    __table_args__ = (db.UniqueConstraint("exam_id", "name", name="uq_topic_exam_name"),)


class TopicPrerequisite(db.Model):
    __tablename__ = "topic_prerequisites"

    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id"), primary_key=True)
    prerequisite_topic_id = db.Column(db.Integer, db.ForeignKey("topics.id"), primary_key=True)

    topic = db.relationship("Topic", foreign_keys=[topic_id], back_populates="prerequisites")
    prerequisite_topic = db.relationship("Topic", foreign_keys=[prerequisite_topic_id])
